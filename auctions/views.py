from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.db.models import Count, Q
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import Auction, Category, Item, AuctionImage, Watchlist
from .forms import ItemForm, AuctionForm, AuctionSearchForm
from bidding.models import BidLog
from notifications.models import Notification


def home(request):
    now = timezone.now()
    featured = Auction.objects.filter(
        status='active', start_time__lte=now, end_time__gt=now
    ).select_related('item', 'item__category', 'seller').prefetch_related('images')[:6]

    ending_soon = Auction.objects.filter(
        status='active', start_time__lte=now, end_time__gt=now
    ).order_by('end_time').select_related('item', 'seller').prefetch_related('images')[:6]

    recently_ended = Auction.objects.filter(
        status='ended'
    ).order_by('-end_time').select_related('item', 'seller').prefetch_related('images')[:4]

    categories = Category.objects.annotate(
        active_count=Count('items__auctions', filter=Q(items__auctions__status='active'))
    )

    stats = {
        'total_active': Auction.objects.filter(status='active').count(),
        'total_ended': Auction.objects.filter(status='ended').count(),
        'total_categories': Category.objects.count(),
    }

    context = {
        'featured': featured,
        'ending_soon': ending_soon,
        'recently_ended': recently_ended,
        'categories': categories,
        'stats': stats,
    }
    return render(request, 'auctions/home.html', context)


def auction_list(request):
    now = timezone.now()
    form = AuctionSearchForm(request.GET or None)
    auctions = Auction.objects.filter(
        status='active', start_time__lte=now, end_time__gt=now
    ).select_related('item', 'item__category', 'seller').prefetch_related('images')

    if form.is_valid():
        q = form.cleaned_data.get('q')
        category = form.cleaned_data.get('category')
        condition = form.cleaned_data.get('condition')
        min_price = form.cleaned_data.get('min_price')
        max_price = form.cleaned_data.get('max_price')
        sort = form.cleaned_data.get('sort', 'ending_soon')

        if q:
            auctions = auctions.filter(
                Q(item__title__icontains=q) | Q(item__description__icontains=q)
            )
        if category:
            auctions = auctions.filter(item__category=category)
        if condition:
            auctions = auctions.filter(item__condition=condition)
        if min_price:
            auctions = auctions.filter(current_price__gte=min_price)
        if max_price:
            auctions = auctions.filter(current_price__lte=max_price)

        if sort == 'ending_soon':
            auctions = auctions.order_by('end_time')
        elif sort == 'newly_listed':
            auctions = auctions.order_by('-start_time')
        elif sort == 'price_low':
            auctions = auctions.order_by('current_price')
        elif sort == 'price_high':
            auctions = auctions.order_by('-current_price')
        elif sort == 'most_bids':
            auctions = auctions.annotate(bid_count=Count('bids')).order_by('-bid_count')
    else:
        auctions = auctions.order_by('end_time')

    paginator = Paginator(auctions, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'auctions/list.html', {
        'page_obj': page_obj,
        'form': form,
        'categories': Category.objects.all(),
    })


def auction_detail(request, pk):
    auction = get_object_or_404(
        Auction.objects.select_related('item', 'item__category', 'seller', 'current_winner')
        .prefetch_related('images', 'bids__bidder'),
        pk=pk
    )

    # Increment view count
    Auction.objects.filter(pk=pk).update(view_count=auction.view_count + 1)

    bids = auction.bids.select_related('bidder').order_by('-bid_time')[:20]
    bid_logs = auction.bid_logs.order_by('-timestamp')[:20]

    is_watching = False
    user_has_proxy = None
    can_bid, bid_reason = False, ""
    if request.user.is_authenticated:
        is_watching = Watchlist.objects.filter(user=request.user, auction=auction).exists()
        can_bid, bid_reason = auction.can_user_bid(request.user)
        try:
            from bidding.models import ProxyBid
            user_has_proxy = ProxyBid.objects.get(user=request.user, auction=auction, is_active=True)
        except Exception:
            pass

    related = Auction.objects.filter(
        status='active',
        item__category=auction.item.category,
        start_time__lte=timezone.now(),
        end_time__gt=timezone.now(),
    ).exclude(pk=pk).select_related('item', 'seller').prefetch_related('images')[:4]

    context = {
        'auction': auction,
        'bids': bids,
        'bid_logs': bid_logs,
        'is_watching': is_watching,
        'can_bid': can_bid,
        'bid_reason': bid_reason,
        'user_has_proxy': user_has_proxy,
        'related': related,
    }
    return render(request, 'auctions/detail.html', context)


@login_required
def create_auction(request):
    if request.method == 'POST':
        item_form = ItemForm(request.POST)
        auction_form = AuctionForm(request.POST)
        images = request.FILES.getlist('images')

        if item_form.is_valid() and auction_form.is_valid():
            with transaction.atomic():
                item = item_form.save()
                auction = auction_form.save(commit=False)
                auction.item = item
                auction.seller = request.user
                auction.current_price = auction.start_price
                auction.status = 'active'
                auction.save()

                for i, img_file in enumerate(images):
                    AuctionImage.objects.create(
                        auction=auction,
                        image=img_file,
                        is_primary=(i == 0),
                        order=i,
                    )

                from bidding.models import BidLog
                BidLog.objects.create(
                    auction=auction,
                    event_type='auction_started',
                    description=f"Auction started by {request.user.username} at ${auction.start_price}"
                )

            messages.success(request, "Auction created successfully!")
            return redirect('auctions:detail', pk=auction.pk)
    else:
        item_form = ItemForm()
        auction_form = AuctionForm()

    return render(request, 'auctions/create.html', {
        'item_form': item_form,
        'auction_form': auction_form,
    })


@login_required
def my_auctions(request):
    selling = Auction.objects.filter(
        seller=request.user
    ).select_related('item').prefetch_related('images').order_by('-created_at')

    context = {'selling': selling}
    return render(request, 'auctions/my_auctions.html', context)


@login_required
def watchlist(request):
    watched = Watchlist.objects.filter(
        user=request.user
    ).select_related('auction', 'auction__item', 'auction__seller').prefetch_related(
        'auction__images'
    ).order_by('-added_at')

    return render(request, 'auctions/watchlist.html', {'watched': watched})


@login_required
def add_to_watchlist(request, pk):
    auction = get_object_or_404(Auction, pk=pk)
    wl, created = Watchlist.objects.get_or_create(user=request.user, auction=auction)
    if created:
        Auction.objects.filter(pk=pk).update(watchlist_count=auction.watchlist_count + 1)
        msg = "Added to watchlist."
    else:
        msg = "Already in watchlist."

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok', 'message': msg})
    messages.success(request, msg)
    return redirect('auctions:detail', pk=pk)


@login_required
def remove_from_watchlist(request, pk):
    auction = get_object_or_404(Auction, pk=pk)
    deleted, _ = Watchlist.objects.filter(user=request.user, auction=auction).delete()
    if deleted:
        count = max(0, auction.watchlist_count - 1)
        Auction.objects.filter(pk=pk).update(watchlist_count=count)
        msg = "Removed from watchlist."
    else:
        msg = "Not in watchlist."

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok', 'message': msg})
    messages.info(request, msg)
    return redirect('auctions:detail', pk=pk)


@login_required
def end_auction(request, pk):
    auction = get_object_or_404(Auction, pk=pk, seller=request.user)
    if auction.status != 'active':
        messages.error(request, "This auction is not active.")
        return redirect('auctions:detail', pk=pk)

    if request.method == 'POST':
        bid_count = auction.get_bid_count()
        reserve_met = auction.reserve_met()

        if bid_count > 0 and reserve_met:
            messages.error(
                request,
                "Cannot end auction early: bids have been placed and reserve price is met."
            )
            return redirect('auctions:detail', pk=pk)

        with transaction.atomic():
            auction.status = 'ended'
            auction.end_time = timezone.now()
            auction.save()

            BidLog.objects.create(
                auction=auction,
                event_type='auction_ended',
                description=f"Auction ended early by seller {request.user.username}."
            )

            if auction.current_winner:
                Notification.objects.create(
                    user=auction.current_winner,
                    notification_type='won',
                    message=f"You won the auction for '{auction.item.title}'!",
                    auction=auction,
                )
                from accounts.models import UserProfile
                UserProfile.objects.filter(user=request.user).update(
                    total_sales=auction.seller.profile.total_sales + 1
                )
                UserProfile.objects.filter(user=auction.current_winner).update(
                    total_purchases=auction.current_winner.profile.total_purchases + 1
                )

        messages.success(request, "Auction ended.")
        return redirect('auctions:my_auctions')

    return render(request, 'auctions/confirm_end.html', {'auction': auction})


@login_required
def buy_now(request, pk):
    auction = get_object_or_404(Auction, pk=pk)
    if not auction.buy_now_price:
        messages.error(request, "This auction does not have a Buy Now option.")
        return redirect('auctions:detail', pk=pk)

    if auction.seller == request.user:
        messages.error(request, "You cannot buy your own auction.")
        return redirect('auctions:detail', pk=pk)

    if not auction.is_active():
        messages.error(request, "This auction is not active.")
        return redirect('auctions:detail', pk=pk)

    if request.method == 'POST':
        with transaction.atomic():
            from bidding.models import Bid, BidLog as BLog

            prev_winner = auction.current_winner
            Bid.objects.filter(auction=auction, is_winning=True).update(
                is_winning=False, status='outbid'
            )

            bid = Bid.objects.create(
                auction=auction,
                bidder=request.user,
                amount=auction.buy_now_price,
                is_winning=True,
                status='won',
                ip_address=get_client_ip(request),
            )

            auction.current_price = auction.buy_now_price
            auction.current_winner = request.user
            auction.status = 'ended'
            auction.end_time = timezone.now()
            auction.save()

            BLog.objects.create(
                auction=auction,
                event_type='buy_now',
                description=f"{request.user.username} purchased via Buy Now at ${auction.buy_now_price}"
            )

            Notification.objects.create(
                user=request.user,
                notification_type='won',
                message=f"You purchased '{auction.item.title}' via Buy Now for ${auction.buy_now_price}!",
                auction=auction,
            )
            Notification.objects.create(
                user=auction.seller,
                notification_type='buy_now',
                message=f"'{auction.item.title}' was purchased via Buy Now by {request.user.username}.",
                auction=auction,
            )

            if prev_winner and prev_winner != request.user:
                Notification.objects.create(
                    user=prev_winner,
                    notification_type='auction_ended',
                    message=f"Auction for '{auction.item.title}' ended via Buy Now.",
                    auction=auction,
                )

        messages.success(
            request,
            f"Congratulations! You purchased '{auction.item.title}' for ${auction.buy_now_price}!"
        )
        return redirect('auctions:detail', pk=pk)

    return render(request, 'auctions/buy_now_confirm.html', {'auction': auction})


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def handler404(request, exception):
    return render(request, '404.html', status=404)


def handler500(request):
    return render(request, '500.html', status=500)

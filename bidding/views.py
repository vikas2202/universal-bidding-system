from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.cache import cache
from decimal import Decimal, InvalidOperation
from auctions.models import Auction
from .models import Bid, BidLog, ProxyBid


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def check_rate_limit(ip_address):
    """Return True if rate limit exceeded (too many bids from this IP)."""
    cache_key = f"bid_rate_{ip_address}"
    count = cache.get(cache_key, 0)
    if count >= 10:
        return True
    cache.set(cache_key, count + 1, timeout=60)
    return False


@login_required
@require_POST
def place_bid(request, pk):
    auction = get_object_or_404(Auction, pk=pk)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    ip = get_client_ip(request)

    # Rate limiting
    if check_rate_limit(ip):
        msg = "Too many bids. Please wait before bidding again."
        if is_ajax:
            return JsonResponse({'success': False, 'error': msg}, status=429)
        messages.error(request, msg)
        return redirect('auctions:detail', pk=pk)

    # Shill bidding prevention
    if auction.seller == request.user:
        msg = "You cannot bid on your own auction."
        if is_ajax:
            return JsonResponse({'success': False, 'error': msg}, status=403)
        messages.error(request, msg)
        return redirect('auctions:detail', pk=pk)

    if not auction.is_active():
        msg = "This auction is not active."
        if is_ajax:
            return JsonResponse({'success': False, 'error': msg}, status=400)
        messages.error(request, msg)
        return redirect('auctions:detail', pk=pk)

    try:
        amount = Decimal(request.POST.get('amount', '0'))
    except (InvalidOperation, ValueError):
        msg = "Invalid bid amount."
        if is_ajax:
            return JsonResponse({'success': False, 'error': msg}, status=400)
        messages.error(request, msg)
        return redirect('auctions:detail', pk=pk)

    max_amount_raw = request.POST.get('max_amount', '').strip()
    max_amount = None
    if max_amount_raw:
        try:
            max_amount = Decimal(max_amount_raw)
            if max_amount < amount:
                max_amount = amount
        except (InvalidOperation, ValueError):
            max_amount = None

    success, result = auction.place_bid(
        user=request.user,
        amount=amount,
        max_amount=max_amount,
        ip_address=ip,
    )

    if success:
        bid = result
        msg = f"Bid of ${bid.amount:.2f} placed successfully!"
        if is_ajax:
            return JsonResponse({
                'success': True,
                'message': msg,
                'new_price': str(auction.current_price),
                'bid_count': auction.get_bid_count(),
                'end_time': auction.end_time.isoformat(),
            })
        messages.success(request, msg)
    else:
        error = result
        if is_ajax:
            return JsonResponse({'success': False, 'error': error}, status=400)
        messages.error(request, error)

    return redirect('auctions:detail', pk=pk)


def bid_history(request, pk):
    auction = get_object_or_404(
        Auction.objects.select_related('item', 'seller'),
        pk=pk
    )
    bids = Bid.objects.filter(auction=auction).select_related('bidder').order_by('-bid_time')
    logs = BidLog.objects.filter(auction=auction).order_by('-timestamp')

    return render(request, 'bidding/bid_history.html', {
        'auction': auction,
        'bids': bids,
        'logs': logs,
    })


@login_required
def auction_status_api(request, pk):
    """AJAX endpoint to get current auction status."""
    auction = get_object_or_404(Auction, pk=pk)
    return JsonResponse({
        'current_price': str(auction.current_price),
        'bid_count': auction.get_bid_count(),
        'time_remaining': auction.time_remaining_seconds(),
        'is_active': auction.is_active(),
        'current_winner': auction.current_winner.username if auction.current_winner else None,
        'status': auction.status,
        'end_time': auction.end_time.isoformat(),
        'min_next_bid': str(auction.min_next_bid),
    })

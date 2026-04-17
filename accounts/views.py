from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import transaction
from .forms import RegistrationForm, LoginForm, UserProfileForm
from .models import UserProfile, UserRating
from auctions.models import Auction
from bidding.models import Bid


def register(request):
    if request.user.is_authenticated:
        return redirect('auctions:home')
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = form.save()
                UserProfile.objects.get_or_create(user=user)
            login(request, user)
            messages.success(request, f"Welcome, {user.username}! Your account has been created.")
            return redirect('auctions:home')
    else:
        form = RegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('auctions:home')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.GET.get('next', '')
            messages.success(request, f"Welcome back, {user.username}!")
            # Only redirect to safe relative URLs to prevent open redirect attacks
            if next_url and next_url.startswith('/') and not next_url.startswith('//'):
                return redirect(next_url)
            return redirect('auctions:home')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('auctions:home')


@login_required
def dashboard(request):
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)

    active_bids = Bid.objects.filter(
        bidder=user, status='active'
    ).select_related('auction').order_by('-bid_time')

    winning_bids = Bid.objects.filter(
        bidder=user, is_winning=True, auction__status='active'
    ).select_related('auction')

    won_auctions = Auction.objects.filter(
        current_winner=user, status='ended'
    ).order_by('-end_time')

    selling_auctions = Auction.objects.filter(
        seller=user
    ).exclude(status='cancelled').order_by('-created_at')

    watched = user.watchlist_set.select_related('auction').order_by('-added_at') if hasattr(user, 'watchlist_set') else []

    context = {
        'profile': profile,
        'active_bids': active_bids,
        'winning_bids': winning_bids,
        'won_auctions': won_auctions,
        'selling_auctions': selling_auctions,
        'watched': watched,
    }
    return render(request, 'accounts/dashboard.html', context)


def profile(request, username):
    user = get_object_or_404(User, username=username)
    profile, _ = UserProfile.objects.get_or_create(user=user)

    selling_history = Auction.objects.filter(
        seller=user, status='ended'
    ).order_by('-end_time')[:10]

    active_selling = Auction.objects.filter(
        seller=user, status='active'
    ).order_by('-start_time')[:5]

    existing_rating = None
    if request.user.is_authenticated and request.user != user:
        existing_rating = UserRating.objects.filter(
            rater=request.user, rated_user=user
        ).first()

    ratings = UserRating.objects.filter(rated_user=user).select_related('rater').order_by('-created_at')

    context = {
        'profile_user': user,
        'profile': profile,
        'selling_history': selling_history,
        'active_selling': active_selling,
        'existing_rating': existing_rating,
        'ratings': ratings,
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def edit_profile(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('accounts:profile', username=request.user.username)
    else:
        form = UserProfileForm(instance=profile)
    return render(request, 'accounts/edit_profile.html', {'form': form})


@login_required
def rate_user(request, username):
    rated_user = get_object_or_404(User, username=username)
    if rated_user == request.user:
        messages.error(request, "You cannot rate yourself.")
        return redirect('accounts:profile', username=username)

    if request.method == 'POST':
        score = request.POST.get('score')
        comment = request.POST.get('comment', '')
        try:
            score = int(score)
            if 1 <= score <= 5:
                UserRating.objects.update_or_create(
                    rater=request.user,
                    rated_user=rated_user,
                    defaults={'score': score, 'comment': comment}
                )
                messages.success(request, f"Rating submitted for {rated_user.username}.")
            else:
                messages.error(request, "Score must be between 1 and 5.")
        except (ValueError, TypeError):
            messages.error(request, "Invalid score.")
    return redirect('accounts:profile', username=username)

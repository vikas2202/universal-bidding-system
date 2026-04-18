"""
Fraud detection services.

Provides functions to analyse a newly-placed bid and raise FraudFlag
records when suspicious patterns are detected.

Detection algorithms implemented
---------------------------------
1. **Bid Anomaly Detection** – Z-score of bid amounts on the same auction.
   A bid that is more than 3 standard deviations above the mean is flagged.

2. **Rapid-Fire Detection** – More than 5 bids by the same user on the
   same auction within the last 10 minutes triggers a flag.

3. **Collusion Detection** – Two or more accounts bidding from the
   same IP on the same auction.

4. **Shill Bid Pattern** – A bidder who has bid on ≥ 5 of the seller's
   auctions and *never* won any of them (driving price up without winning).

5. **Trust Score Update** – Each new flag reduces the user's
   ``UserProfile.trust_score`` by a severity-weighted amount.
"""

from __future__ import annotations

import math
from typing import Optional

from django.contrib.auth.models import User
from django.utils import timezone


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyse_bid(bid) -> list:
    """
    Run all detectors against *bid* and persist any FraudFlag records.

    Returns a list of created FraudFlag instances (may be empty).
    """
    from bidding.models import Bid

    flags: list = []
    flags += _detect_anomaly(bid)
    flags += _detect_rapid_fire(bid)
    flags += _detect_collusion(bid)
    flags += _detect_shill_pattern(bid)

    # Update risk profile and trust score for each new flag
    for flag in flags:
        _update_risk_profile(flag.user, flag.flag_type)
        _penalise_trust_score(flag.user, flag.severity)

    return flags


# ---------------------------------------------------------------------------
# Individual detectors
# ---------------------------------------------------------------------------

def _detect_anomaly(bid) -> list:
    """Z-score based bid-amount outlier detection."""
    from bidding.models import Bid
    from .models import FraudFlag

    bids = list(
        Bid.objects.filter(auction=bid.auction)
        .exclude(pk=bid.pk)
        .values_list('amount', flat=True)
    )
    if len(bids) < 3:
        return []

    mean = sum(float(a) for a in bids) / len(bids)
    variance = sum((float(a) - mean) ** 2 for a in bids) / len(bids)
    std = math.sqrt(variance) if variance > 0 else 0

    if std == 0:
        return []

    z = (float(bid.amount) - mean) / std
    if abs(z) > 3:
        flag = FraudFlag.objects.create(
            user=bid.bidder,
            auction=bid.auction,
            bid=bid,
            flag_type='anomaly',
            severity='high' if abs(z) > 5 else 'medium',
            description=(
                f"Bid amount ${bid.amount} is a statistical outlier "
                f"(Z-score={z:.2f}, mean=${mean:.2f}, σ=${std:.2f})."
            ),
            ip_address=bid.ip_address,
        )
        return [flag]
    return []


def _detect_rapid_fire(bid) -> list:
    """Flag more than 5 bids by the same bidder in 10 minutes on the same auction."""
    from bidding.models import Bid
    from .models import FraudFlag

    window_start = timezone.now() - timezone.timedelta(minutes=10)
    recent_count = Bid.objects.filter(
        auction=bid.auction,
        bidder=bid.bidder,
        bid_time__gte=window_start,
    ).count()

    if recent_count > 5:
        flag = FraudFlag.objects.create(
            user=bid.bidder,
            auction=bid.auction,
            bid=bid,
            flag_type='rapid_fire',
            severity='medium',
            description=(
                f"{bid.bidder.username} placed {recent_count} bids on this auction "
                f"in the last 10 minutes."
            ),
            ip_address=bid.ip_address,
        )
        return [flag]
    return []


def _detect_collusion(bid) -> list:
    """Flag when two different accounts bid from the same IP on the same auction."""
    from bidding.models import Bid
    from .models import FraudFlag

    if not bid.ip_address:
        return []

    other_bidders = (
        Bid.objects.filter(auction=bid.auction, ip_address=bid.ip_address)
        .exclude(bidder=bid.bidder)
        .values_list('bidder', flat=True)
        .distinct()
    )

    if other_bidders.exists():
        other_ids = list(other_bidders[:5])
        flag = FraudFlag.objects.create(
            user=bid.bidder,
            auction=bid.auction,
            bid=bid,
            flag_type='collusion',
            severity='high',
            description=(
                f"IP {bid.ip_address} used by multiple bidders on the same auction "
                f"(other bidder IDs: {other_ids})."
            ),
            ip_address=bid.ip_address,
        )
        return [flag]
    return []


def _detect_shill_pattern(bid) -> list:
    """
    Flag a bidder who has participated in ≥5 auctions by the same seller
    and has never won any of them.
    """
    from bidding.models import Bid
    from .models import FraudFlag
    from auctions.models import Auction

    seller = bid.auction.seller
    seller_auction_ids = Auction.objects.filter(seller=seller).values_list('id', flat=True)

    participated = (
        Bid.objects.filter(bidder=bid.bidder, auction__in=seller_auction_ids)
        .values_list('auction', flat=True)
        .distinct()
        .count()
    )

    if participated < 5:
        return []

    won = Auction.objects.filter(
        id__in=seller_auction_ids, current_winner=bid.bidder, status='ended'
    ).count()

    if won == 0:
        flag = FraudFlag.objects.create(
            user=bid.bidder,
            auction=bid.auction,
            bid=bid,
            flag_type='shill_bid',
            severity='medium',
            description=(
                f"{bid.bidder.username} has bid on {participated} auctions by "
                f"{seller.username} and won none — possible shill pattern."
            ),
            ip_address=bid.ip_address,
        )
        return [flag]
    return []


# ---------------------------------------------------------------------------
# Risk profile and trust score helpers
# ---------------------------------------------------------------------------

_FLAG_SCORE_WEIGHTS = {
    'shill_bid': ('shill_score', 15.0),
    'collusion': ('collusion_score', 20.0),
    'anomaly': ('anomaly_score', 10.0),
    'rapid_fire': ('anomaly_score', 5.0),
    'rate_limit': ('anomaly_score', 5.0),
    'account_link': ('collusion_score', 15.0),
    'duplicate_bid': ('anomaly_score', 5.0),
    'withdrawal_pattern': ('shill_score', 10.0),
}

_TRUST_PENALTY = {
    'low': 2.0,
    'medium': 5.0,
    'high': 10.0,
    'critical': 20.0,
}


def _update_risk_profile(user: User, flag_type: str) -> None:
    from .models import BidderRiskProfile

    profile, _ = BidderRiskProfile.objects.get_or_create(user=user)
    profile.total_flags += 1
    profile.last_flagged_at = timezone.now()

    field_name, increment = _FLAG_SCORE_WEIGHTS.get(flag_type, ('anomaly_score', 5.0))
    current = getattr(profile, field_name)
    setattr(profile, field_name, min(100.0, current + increment))
    profile.save()


def _penalise_trust_score(user: User, severity: str) -> None:
    """Reduce UserProfile.trust_score by a severity-weighted amount."""
    try:
        from accounts.models import UserProfile
        penalty = _TRUST_PENALTY.get(severity, 5.0)
        # Use a DB query to avoid stale cached profile objects on the user instance
        profile = UserProfile.objects.get(user=user)
        profile.trust_score = max(0.0, profile.trust_score - penalty)
        profile.save(update_fields=['trust_score'])
    except Exception:
        pass

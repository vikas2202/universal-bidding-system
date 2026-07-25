from celery import shared_task
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from auctions.models import Auction
from notifications.models import Notification


@shared_task
def close_expired_auctions():
    """Close active auctions that have reached end time."""
    now = timezone.now()
    expired = Auction.objects.filter(status='active', end_time__lte=now).select_related(
        'item', 'seller', 'current_winner'
    )

    for auction in expired:
        with transaction.atomic():
            auction.status = 'ended'
            auction.save(update_fields=['status', 'updated_at'])

            if auction.auction_type == 'sealed_bid':
                auction.determine_sealed_bid_winner()
                auction.refresh_from_db()
            elif auction.auction_type == 'vickrey':
                auction.determine_vickrey_winner()
                auction.refresh_from_db()

            if auction.current_winner:
                Notification.objects.create(
                    user=auction.current_winner,
                    notification_type='won',
                    message=f"You won the auction for '{auction.item.title}'!",
                    auction=auction,
                )

            Notification.objects.create(
                user=auction.seller,
                notification_type='auction_ended',
                message=f"Your auction '{auction.item.title}' has ended.",
                auction=auction,
            )

        run_fraud_analysis.delay(auction.pk)

    return expired.count()


@shared_task
def send_outbid_notification(user_id, auction_id):
    """Notify previous high bidder when they are outbid."""
    user = User.objects.filter(pk=user_id).first()
    auction = Auction.objects.select_related('item').filter(pk=auction_id).first()
    if not user or not auction:
        return False

    Notification.objects.create(
        user=user,
        notification_type='outbid',
        message=f"You have been outbid on '{auction.item.title}'. Current price: ${auction.current_price:.2f}",
        auction=auction,
    )

    if user.email:
        send_mail(
            subject=f"You've been outbid on {auction.item.title}",
            message=f"Current price is ${auction.current_price:.2f}.",
            from_email=None,
            recipient_list=[user.email],
            fail_silently=True,
        )
    return True


@shared_task
def run_fraud_analysis(auction_id):
    """Re-run fraud checks on all bids for an auction."""
    from bidding.models import Bid
    from fraud_detection.services import analyse_bid

    bids = Bid.objects.filter(auction_id=auction_id).select_related('auction', 'bidder')
    for bid in bids:
        analyse_bid(bid)
    return bids.count()


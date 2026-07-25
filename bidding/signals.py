from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Bid


@receiver(post_save, sender=Bid)
def broadcast_bid_update(sender, instance, created, **kwargs):
    if not created:
        return

    auction = instance.auction
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    payload = {
        "type": "bid_update",
        "current_price": float(auction.current_price),
        "bid_count": auction.get_bid_count(),
        "time_remaining": auction.time_remaining_seconds(),
        "last_bidder": instance.bidder.username,
        "auction_end": auction.end_time.isoformat(),
    }
    try:
        async_to_sync(channel_layer.group_send)(
            f"auction_{auction.pk}",
            {
                "type": "bid_update",
                "payload": payload,
            }
        )
    except Exception:
        pass

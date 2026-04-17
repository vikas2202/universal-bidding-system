from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Bid(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('outbid', 'Outbid'),
        ('won', 'Won'),
        ('cancelled', 'Cancelled'),
    ]

    auction = models.ForeignKey('auctions.Auction', on_delete=models.CASCADE, related_name='bids')
    bidder = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bids')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    max_amount = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text='Maximum proxy bid amount'
    )
    bid_time = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    is_auto_bid = models.BooleanField(default=False)
    is_winning = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    class Meta:
        ordering = ['-bid_time']

    def __str__(self):
        return f"{self.bidder.username} bid ${self.amount} on {self.auction}"


class BidLog(models.Model):
    EVENT_CHOICES = [
        ('bid_placed', 'Bid Placed'),
        ('proxy_bid', 'Proxy Bid'),
        ('outbid', 'Outbid'),
        ('reserve_met', 'Reserve Met'),
        ('auction_started', 'Auction Started'),
        ('auction_ended', 'Auction Ended'),
        ('buy_now', 'Buy Now'),
        ('auto_extend', 'Auto Extended'),
        ('cancelled', 'Cancelled'),
    ]

    auction = models.ForeignKey('auctions.Auction', on_delete=models.CASCADE, related_name='bid_logs')
    event_type = models.CharField(max_length=30, choices=EVENT_CHOICES)
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.event_type}] {self.auction} @ {self.timestamp}"


class ProxyBid(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='proxy_bids')
    auction = models.ForeignKey('auctions.Auction', on_delete=models.CASCADE, related_name='proxy_bids')
    max_amount = models.DecimalField(max_digits=12, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'auction')

    def __str__(self):
        return f"{self.user.username} proxy bid (max ${self.max_amount}) on {self.auction}"

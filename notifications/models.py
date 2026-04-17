from django.db import models
from django.contrib.auth.models import User


class Notification(models.Model):
    TYPE_CHOICES = [
        ('outbid', 'You were outbid'),
        ('won', 'You won an auction'),
        ('auction_ending', 'Auction ending soon'),
        ('new_bid', 'New bid on your auction'),
        ('reserve_met', 'Reserve price met'),
        ('buy_now', 'Item purchased via Buy Now'),
        ('auction_ended', 'Auction ended'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    message = models.TextField()
    auction = models.ForeignKey(
        'auctions.Auction', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='notifications'
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}: {self.notification_type}"

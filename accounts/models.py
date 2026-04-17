from django.db import models
from django.contrib.auth.models import User
from django.db.models import Avg


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    total_sales = models.PositiveIntegerField(default=0)
    total_purchases = models.PositiveIntegerField(default=0)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Profile of {self.user.username}"

    def get_rating(self):
        avg = self.user.ratings_received.aggregate(avg=Avg('score'))['avg']
        return round(avg, 1) if avg else 0.0

    def get_active_bids(self):
        from bidding.models import Bid
        return Bid.objects.filter(bidder=self.user, status='active').select_related('auction')

    def get_won_auctions(self):
        from auctions.models import Auction
        return Auction.objects.filter(current_winner=self.user, status='ended')


class UserRating(models.Model):
    rater = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings_given')
    rated_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='ratings_received'
    )
    score = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('rater', 'rated_user')

    def __str__(self):
        return f"{self.rater.username} rated {self.rated_user.username}: {self.score}"

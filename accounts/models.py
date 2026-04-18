from django.db import models
from django.contrib.auth.models import User
from django.db.models import Avg


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('bidder', 'Bidder'),
        ('auctioneer', 'Auctioneer'),
        ('moderator', 'Moderator'),
        ('admin', 'Admin'),
    ]

    KYC_STATUS_CHOICES = [
        ('none', 'Not Submitted'),
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='bidder')
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    total_sales = models.PositiveIntegerField(default=0)
    total_purchases = models.PositiveIntegerField(default=0)
    is_verified = models.BooleanField(default=False)
    # KYC compliance
    kyc_status = models.CharField(max_length=20, choices=KYC_STATUS_CHOICES, default='none')
    kyc_submitted_at = models.DateTimeField(null=True, blank=True)
    # Bidder trust/reputation
    trust_score = models.FloatField(default=100.0, help_text='0–100; reduced by fraud flags')
    is_blacklisted = models.BooleanField(default=False)
    blacklist_reason = models.TextField(blank=True)
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

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from django.utils.text import slugify
from decimal import Decimal
import datetime


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='bi-tag', help_text='Bootstrap icon class')

    class Meta:
        verbose_name_plural = 'categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('auctions:list') + f'?category={self.slug}'


class Item(models.Model):
    CONDITION_CHOICES = [
        ('new', 'New'),
        ('used', 'Used'),
        ('refurbished', 'Refurbished'),
    ]
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='items')
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='used')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Auction(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('ended', 'Ended'),
        ('cancelled', 'Cancelled'),
    ]

    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='auctions')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='auctions_selling')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    start_price = models.DecimalField(max_digits=12, decimal_places=2)
    reserve_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    buy_now_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    current_price = models.DecimalField(max_digits=12, decimal_places=2)
    current_winner = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='auctions_winning'
    )

    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    auto_extend = models.BooleanField(default=True, help_text='Extend by 5 min if bid placed in last 5 min')

    view_count = models.PositiveIntegerField(default=0)
    watchlist_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.item.title} by {self.seller.username}"

    def save(self, *args, **kwargs):
        if not self.current_price:
            self.current_price = self.start_price
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('auctions:detail', kwargs={'pk': self.pk})

    def is_active(self):
        now = timezone.now()
        return self.status == 'active' and self.start_time <= now <= self.end_time

    def time_remaining(self):
        if not self.is_active():
            return None
        remaining = self.end_time - timezone.now()
        if remaining.total_seconds() <= 0:
            return datetime.timedelta(0)
        return remaining

    def time_remaining_seconds(self):
        remaining = self.time_remaining()
        if remaining is None:
            return 0
        return max(0, int(remaining.total_seconds()))

    def get_bid_count(self):
        return self.bids.count()

    @property
    def min_bid_increment(self):
        return max(Decimal('1.00'), (self.current_price * Decimal('0.05')).quantize(Decimal('0.01')))

    @property
    def min_next_bid(self):
        return self.current_price + self.min_bid_increment

    def reserve_met(self):
        if self.reserve_price is None:
            return True
        return self.current_price >= self.reserve_price

    def can_user_bid(self, user):
        if not user.is_authenticated:
            return False, "You must be logged in to bid."
        if user == self.seller:
            return False, "You cannot bid on your own auction."
        if not self.is_active():
            return False, "This auction is not active."
        return True, ""

    def place_bid(self, user, amount, max_amount=None, ip_address=None):
        from bidding.models import Bid, BidLog, ProxyBid
        from notifications.models import Notification

        can_bid, reason = self.can_user_bid(user)
        if not can_bid:
            return False, reason

        amount = Decimal(str(amount))
        if amount < self.min_next_bid:
            return False, f"Bid must be at least ${self.min_next_bid:.2f}"

        if max_amount is not None:
            max_amount = Decimal(str(max_amount))
            if max_amount < amount:
                max_amount = amount

        previous_winner = self.current_winner
        previous_price = self.current_price

        # Mark previous winning bid as outbid
        if previous_winner:
            Bid.objects.filter(auction=self, is_winning=True).update(
                is_winning=False, status='outbid'
            )

        bid = Bid.objects.create(
            auction=self,
            bidder=user,
            amount=amount,
            max_amount=max_amount,
            ip_address=ip_address,
            is_auto_bid=False,
            is_winning=True,
            status='active',
        )

        if max_amount is not None:
            ProxyBid.objects.update_or_create(
                user=user, auction=self,
                defaults={'max_amount': max_amount, 'is_active': True}
            )

        self.current_price = amount
        self.current_winner = user

        # Auto-extend if bid placed in last 5 minutes
        if self.auto_extend:
            time_left = self.time_remaining()
            if time_left and time_left.total_seconds() < 300:
                self.end_time = timezone.now() + datetime.timedelta(minutes=5)
                BidLog.objects.create(
                    auction=self,
                    event_type='auto_extend',
                    description=f"Auction extended by 5 minutes due to last-minute bid."
                )

        self.save()

        BidLog.objects.create(
            auction=self,
            event_type='bid_placed',
            description=(
                f"{user.username} placed bid of ${amount:.2f}"
                + (f" (proxy max: ${max_amount:.2f})" if max_amount else "")
            )
        )

        if self.reserve_price and amount >= self.reserve_price and previous_price < self.reserve_price:
            BidLog.objects.create(
                auction=self,
                event_type='reserve_met',
                description=f"Reserve price of ${self.reserve_price:.2f} has been met."
            )
            Notification.objects.create(
                user=self.seller,
                notification_type='reserve_met',
                message=f"Reserve price met on your auction: {self.item.title}",
                auction=self,
            )

        # Notify outbid user
        if previous_winner and previous_winner != user:
            Notification.objects.create(
                user=previous_winner,
                notification_type='outbid',
                message=f"You have been outbid on '{self.item.title}'. Current price: ${self.current_price:.2f}",
                auction=self,
            )

            # Check if outbid user has a proxy bid that can respond
            try:
                proxy = ProxyBid.objects.get(user=previous_winner, auction=self, is_active=True)
                proxy_amount = proxy.max_amount
                needed = amount + self.min_bid_increment
                if proxy_amount >= needed:
                    # Auto-bid back
                    self._process_proxy_bid(previous_winner, needed, proxy_amount, ip_address)
            except ProxyBid.DoesNotExist:
                pass

        return True, bid

    def _process_proxy_bid(self, user, amount, max_amount, ip_address=None):
        from bidding.models import Bid, BidLog, ProxyBid
        from notifications.models import Notification

        previous_winner = self.current_winner
        Bid.objects.filter(auction=self, is_winning=True).update(is_winning=False, status='outbid')

        Bid.objects.create(
            auction=self,
            bidder=user,
            amount=amount,
            max_amount=max_amount,
            ip_address=ip_address,
            is_auto_bid=True,
            is_winning=True,
            status='active',
        )

        self.current_price = amount
        self.current_winner = user
        self.save()

        BidLog.objects.create(
            auction=self,
            event_type='proxy_bid',
            description=f"Auto-bid placed for {user.username}: ${amount:.2f} (proxy max: ${max_amount:.2f})"
        )

        if previous_winner and previous_winner != user:
            Notification.objects.create(
                user=previous_winner,
                notification_type='outbid',
                message=f"You have been outbid on '{self.item.title}'. Current price: ${self.current_price:.2f}",
                auction=self,
            )


class AuctionImage(models.Model):
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='auction_images/')
    is_primary = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"Image for {self.auction}"


class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watchlist_set')
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name='watchlisted_by')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'auction')

    def __str__(self):
        return f"{self.user.username} watching {self.auction}"

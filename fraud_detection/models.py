"""
Fraud detection models.

FraudFlag     – individual flag raised against a bid or bidder
BidderRiskProfile – aggregated risk metrics per user
"""
from django.db import models
from django.contrib.auth.models import User


class FraudFlag(models.Model):
    FLAG_TYPES = [
        ('shill_bid', 'Shill Bidding'),
        ('collusion', 'Collusion'),
        ('rate_limit', 'Rate Limit Exceeded'),
        ('anomaly', 'Bid Anomaly'),
        ('account_link', 'Linked Account'),
        ('duplicate_bid', 'Duplicate Bid'),
        ('rapid_fire', 'Rapid-Fire Bidding'),
        ('withdrawal_pattern', 'Bid Withdrawal Pattern'),
    ]
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fraud_flags')
    auction = models.ForeignKey(
        'auctions.Auction', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='fraud_flags'
    )
    bid = models.ForeignKey(
        'bidding.Bid', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='fraud_flags'
    )
    flag_type = models.CharField(max_length=30, choices=FLAG_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='medium')
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    is_reviewed = models.BooleanField(default=False)
    reviewed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reviewed_fraud_flags'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'flag_type']),
            models.Index(fields=['auction']),
            models.Index(fields=['is_reviewed']),
        ]

    def __str__(self):
        return f"[{self.flag_type}] {self.user.username} – {self.severity}"


class BidderRiskProfile(models.Model):
    """Aggregated risk metrics maintained per bidder."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='risk_profile')
    total_flags = models.PositiveIntegerField(default=0)
    collusion_score = models.FloatField(default=0.0, help_text='0–100; higher = more suspicious')
    anomaly_score = models.FloatField(default=0.0, help_text='0–100; higher = more anomalous')
    shill_score = models.FloatField(default=0.0, help_text='0–100; higher = more suspicious')
    last_flagged_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-collusion_score']

    def __str__(self):
        return f"RiskProfile({self.user.username})"

    @property
    def overall_risk(self):
        """Composite risk score 0–100."""
        return round(
            (self.collusion_score * 0.4 + self.anomaly_score * 0.3 + self.shill_score * 0.3),
            2
        )

"""
Tests for the fraud detection services.

Covers:
  - Bid anomaly detection (Z-score)
  - Rapid-fire detection
  - Collusion detection (same IP, different users)
  - Shill bidding pattern detection
  - Risk profile updates
  - Trust score penalisation
"""
from decimal import Decimal
import datetime

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User

from auctions.models import Category, Item, Auction
from bidding.models import Bid
from accounts.models import UserProfile
from fraud_detection.models import FraudFlag, BidderRiskProfile
from fraud_detection import services


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_user(username):
    u = User.objects.create_user(username=username, password='pass1234')
    UserProfile.objects.get_or_create(user=u)
    return u


def make_auction(seller, auction_type='english', start_price=100):
    cat = Category.objects.get_or_create(
        slug='fd-cat', defaults={'name': 'FD Cat', 'icon': 'bi-box'}
    )[0]
    item = Item.objects.create(title='FD Item', description='x', category=cat, condition='used')
    now = timezone.now()
    return Auction.objects.create(
        item=item, seller=seller, status='active',
        auction_type=auction_type,
        start_price=Decimal(str(start_price)),
        current_price=Decimal(str(start_price)),
        start_time=now - datetime.timedelta(hours=1),
        end_time=now + datetime.timedelta(hours=24),
        auto_extend=False,
    )


def make_bid(auction, bidder, amount, ip=None, minutes_ago=0):
    bid = Bid.objects.create(
        auction=auction,
        bidder=bidder,
        amount=Decimal(str(amount)),
        ip_address=ip,
        is_winning=False,
        status='active',
    )
    if minutes_ago:
        bid_time = timezone.now() - datetime.timedelta(minutes=minutes_ago)
        Bid.objects.filter(pk=bid.pk).update(bid_time=bid_time)
        bid.refresh_from_db()
    return bid


# ---------------------------------------------------------------------------
# Anomaly detection
# ---------------------------------------------------------------------------

class BidAnomalyDetectionTest(TestCase):

    def setUp(self):
        self.seller = make_user('fd_seller')
        self.bidder = make_user('fd_bidder')
        self.auction = make_auction(self.seller)

    def _seed_bids(self, amounts):
        for a in amounts:
            make_bid(self.auction, self.bidder, a)

    def test_no_anomaly_on_normal_bids(self):
        self._seed_bids([100, 105, 110, 115, 120])
        bid = make_bid(self.auction, self.bidder, 125)
        flags = services._detect_anomaly(bid)
        self.assertEqual(len(flags), 0)

    def test_anomaly_flagged_for_extreme_bid(self):
        self._seed_bids([100, 105, 110, 115, 120])
        # A bid 10× the standard deviation away
        bid = make_bid(self.auction, self.bidder, 100_000)
        flags = services._detect_anomaly(bid)
        self.assertGreater(len(flags), 0)
        self.assertEqual(flags[0].flag_type, 'anomaly')

    def test_fewer_than_3_bids_skips_analysis(self):
        self._seed_bids([100, 110])
        bid = make_bid(self.auction, self.bidder, 100_000)
        flags = services._detect_anomaly(bid)
        self.assertEqual(len(flags), 0)


# ---------------------------------------------------------------------------
# Rapid-fire detection
# ---------------------------------------------------------------------------

class RapidFireDetectionTest(TestCase):

    def setUp(self):
        self.seller = make_user('rf_seller')
        self.bidder = make_user('rf_bidder')
        self.auction = make_auction(self.seller)

    def test_no_flag_for_normal_frequency(self):
        for _ in range(3):
            make_bid(self.auction, self.bidder, 100)
        bid = make_bid(self.auction, self.bidder, 105)
        flags = services._detect_rapid_fire(bid)
        self.assertEqual(len(flags), 0)

    def test_flag_raised_after_six_bids_in_window(self):
        for _ in range(6):
            make_bid(self.auction, self.bidder, 100, minutes_ago=5)
        bid = make_bid(self.auction, self.bidder, 105, minutes_ago=1)
        flags = services._detect_rapid_fire(bid)
        self.assertGreater(len(flags), 0)
        self.assertEqual(flags[0].flag_type, 'rapid_fire')

    def test_old_bids_outside_window_not_counted(self):
        # Bids placed 15+ minutes ago should not count
        for _ in range(6):
            make_bid(self.auction, self.bidder, 100, minutes_ago=20)
        bid = make_bid(self.auction, self.bidder, 105, minutes_ago=0)
        flags = services._detect_rapid_fire(bid)
        self.assertEqual(len(flags), 0)


# ---------------------------------------------------------------------------
# Collusion detection
# ---------------------------------------------------------------------------

class CollusionDetectionTest(TestCase):

    def setUp(self):
        self.seller = make_user('col_seller')
        self.bidder1 = make_user('col_bidder1')
        self.bidder2 = make_user('col_bidder2')
        self.auction = make_auction(self.seller)

    def test_no_flag_when_single_ip_single_bidder(self):
        make_bid(self.auction, self.bidder1, 110, ip='192.168.1.1')
        bid = make_bid(self.auction, self.bidder1, 120, ip='192.168.1.1')
        flags = services._detect_collusion(bid)
        self.assertEqual(len(flags), 0)

    def test_flag_raised_when_two_bidders_share_ip(self):
        make_bid(self.auction, self.bidder1, 110, ip='10.0.0.1')
        bid = make_bid(self.auction, self.bidder2, 120, ip='10.0.0.1')
        flags = services._detect_collusion(bid)
        self.assertGreater(len(flags), 0)
        self.assertEqual(flags[0].flag_type, 'collusion')

    def test_no_flag_when_ip_is_none(self):
        make_bid(self.auction, self.bidder1, 110, ip=None)
        bid = make_bid(self.auction, self.bidder2, 120, ip=None)
        flags = services._detect_collusion(bid)
        self.assertEqual(len(flags), 0)


# ---------------------------------------------------------------------------
# Shill bid pattern
# ---------------------------------------------------------------------------

class ShillPatternDetectionTest(TestCase):

    def setUp(self):
        self.seller = make_user('shp_seller')
        self.shill = make_user('shp_shill')

    def _make_seller_auction(self):
        return make_auction(self.seller)

    def test_no_flag_with_few_participations(self):
        auction = self._make_seller_auction()
        bid = make_bid(auction, self.shill, 110)
        flags = services._detect_shill_pattern(bid)
        self.assertEqual(len(flags), 0)

    def test_flag_raised_when_never_won_5_plus_auctions(self):
        for _ in range(5):
            a = self._make_seller_auction()
            make_bid(a, self.shill, 110)

        # Current auction
        auction = self._make_seller_auction()
        bid = make_bid(auction, self.shill, 110)
        flags = services._detect_shill_pattern(bid)
        self.assertGreater(len(flags), 0)
        self.assertEqual(flags[0].flag_type, 'shill_bid')

    def test_no_flag_when_bidder_has_won(self):
        for _ in range(5):
            a = self._make_seller_auction()
            make_bid(a, self.shill, 110)

        # Mark one auction as won by shill
        won_auction = self._make_seller_auction()
        won_auction.current_winner = self.shill
        won_auction.status = 'ended'
        won_auction.save()

        auction = self._make_seller_auction()
        bid = make_bid(auction, self.shill, 110)
        flags = services._detect_shill_pattern(bid)
        self.assertEqual(len(flags), 0)


# ---------------------------------------------------------------------------
# Risk profile and trust score
# ---------------------------------------------------------------------------

class RiskProfileTest(TestCase):

    def setUp(self):
        self.user = make_user('rp_user')

    def test_risk_profile_created_on_first_flag(self):
        services._update_risk_profile(self.user, 'collusion')
        profile = BidderRiskProfile.objects.filter(user=self.user).first()
        self.assertIsNotNone(profile)
        self.assertEqual(profile.total_flags, 1)

    def test_collusion_score_increases(self):
        services._update_risk_profile(self.user, 'collusion')
        profile = BidderRiskProfile.objects.get(user=self.user)
        self.assertGreater(profile.collusion_score, 0)

    def test_trust_score_decreases_on_penalty(self):
        profile, _ = UserProfile.objects.get_or_create(user=self.user)
        initial = profile.trust_score
        services._penalise_trust_score(self.user, 'high')
        profile.refresh_from_db()
        self.assertLess(profile.trust_score, initial)

    def test_trust_score_floor_is_zero(self):
        profile, _ = UserProfile.objects.get_or_create(user=self.user)
        profile.trust_score = 0.0
        profile.save()
        services._penalise_trust_score(self.user, 'critical')
        profile.refresh_from_db()
        self.assertEqual(profile.trust_score, 0.0)

    def test_overall_risk_composite(self):
        profile = BidderRiskProfile.objects.create(
            user=self.user,
            collusion_score=40.0,
            anomaly_score=30.0,
            shill_score=20.0,
        )
        expected = round(40 * 0.4 + 30 * 0.3 + 20 * 0.3, 2)
        self.assertEqual(profile.overall_risk, expected)


# ---------------------------------------------------------------------------
# Blacklisted user bidding blocked
# ---------------------------------------------------------------------------

class BlacklistTest(TestCase):

    def setUp(self):
        self.seller = make_user('bl_seller')
        self.bidder = make_user('bl_bidder')
        profile = self.bidder.profile
        profile.is_blacklisted = True
        profile.blacklist_reason = 'Fraud'
        profile.save()
        self.auction = make_auction(self.seller)

    def test_blacklisted_user_cannot_bid(self):
        can_bid, reason = self.auction.can_user_bid(self.bidder)
        self.assertFalse(can_bid)
        self.assertIn('restricted', reason.lower())

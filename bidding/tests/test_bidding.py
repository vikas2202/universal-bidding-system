from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
import datetime
from auctions.models import Category, Item, Auction
from bidding.models import Bid, BidLog, ProxyBid
from accounts.models import UserProfile


def make_user(username, password='pass1234'):
    user = User.objects.create_user(username=username, password=password)
    UserProfile.objects.get_or_create(user=user)
    return user


def make_auction(seller, start_price=100, reserve=None, buy_now=None, hours=24):
    category = Category.objects.get_or_create(
        slug='test-cat', defaults={'name': 'Test Category', 'icon': 'bi-box'}
    )[0]
    item = Item.objects.create(
        title='Test Item', description='A test item',
        category=category, condition='used'
    )
    now = timezone.now()
    auction = Auction.objects.create(
        item=item,
        seller=seller,
        status='active',
        start_price=Decimal(str(start_price)),
        reserve_price=Decimal(str(reserve)) if reserve else None,
        buy_now_price=Decimal(str(buy_now)) if buy_now else None,
        current_price=Decimal(str(start_price)),
        start_time=now - datetime.timedelta(hours=1),
        end_time=now + datetime.timedelta(hours=hours),
        auto_extend=False,
    )
    return auction


class ShillBiddingPreventionTest(TestCase):
    """Users cannot bid on their own auctions."""

    def setUp(self):
        self.seller = make_user('seller')
        self.buyer = make_user('buyer')
        self.auction = make_auction(self.seller)

    def test_seller_cannot_bid_own_auction(self):
        success, result = self.auction.place_bid(self.seller, Decimal('110'))
        self.assertFalse(success)
        self.assertIn('own auction', result.lower())

    def test_buyer_can_bid(self):
        success, result = self.auction.place_bid(self.buyer, Decimal('110'))
        self.assertTrue(success)
        self.assertIsInstance(result, Bid)

    def test_can_user_bid_seller_returns_false(self):
        can_bid, reason = self.auction.can_user_bid(self.seller)
        self.assertFalse(can_bid)

    def test_can_user_bid_buyer_returns_true(self):
        can_bid, reason = self.auction.can_user_bid(self.buyer)
        self.assertTrue(can_bid)


class BidIncrementValidationTest(TestCase):
    """Bids must meet minimum increment (5% of current price or $1 minimum)."""

    def setUp(self):
        self.seller = make_user('seller2')
        self.buyer = make_user('buyer2')
        self.auction = make_auction(self.seller, start_price=100)

    def test_bid_below_minimum_rejected(self):
        # Min increment = max(1.00, 100 * 0.05) = 5.00, so min bid = 105.00
        success, result = self.auction.place_bid(self.buyer, Decimal('100.50'))
        self.assertFalse(success)

    def test_bid_exactly_at_minimum_accepted(self):
        min_bid = self.auction.min_next_bid
        success, result = self.auction.place_bid(self.buyer, min_bid)
        self.assertTrue(success)

    def test_bid_above_minimum_accepted(self):
        success, result = self.auction.place_bid(self.buyer, Decimal('120'))
        self.assertTrue(success)

    def test_min_increment_is_5_percent(self):
        increment = self.auction.min_bid_increment
        self.assertEqual(increment, Decimal('5.00'))  # 5% of 100

    def test_min_increment_is_at_least_one_dollar(self):
        # Set a very low price
        self.auction.current_price = Decimal('10')
        self.auction.save()
        increment = self.auction.min_bid_increment
        self.assertGreaterEqual(increment, Decimal('1.00'))

    def test_min_increment_at_low_price(self):
        self.auction.current_price = Decimal('5')
        self.auction.save()
        # 5% of 5 = 0.25, but minimum is 1.00
        self.assertEqual(self.auction.min_bid_increment, Decimal('1.00'))


class ProxyBiddingTest(TestCase):
    """Proxy/automatic bidding logic."""

    def setUp(self):
        self.seller = make_user('seller3')
        self.buyer1 = make_user('buyer3a')
        self.buyer2 = make_user('buyer3b')
        self.auction = make_auction(self.seller, start_price=100)

    def test_proxy_bid_created(self):
        self.auction.place_bid(self.buyer1, Decimal('110'), max_amount=Decimal('200'))
        proxy = ProxyBid.objects.filter(user=self.buyer1, auction=self.auction).first()
        self.assertIsNotNone(proxy)
        self.assertEqual(proxy.max_amount, Decimal('200'))
        self.assertTrue(proxy.is_active)

    def test_proxy_auto_bids_when_outbid(self):
        # buyer1 sets proxy max of 200
        self.auction.place_bid(self.buyer1, Decimal('110'), max_amount=Decimal('200'))
        self.assertEqual(self.auction.current_winner, self.buyer1)

        # buyer2 bids 130 - proxy should auto-respond
        self.auction.place_bid(self.buyer2, Decimal('130'))
        self.auction.refresh_from_db()
        # buyer1's proxy should have auto-bid
        self.assertEqual(self.auction.current_winner, self.buyer1)

    def test_proxy_does_not_exceed_max(self):
        # buyer1 proxy max = 150
        self.auction.place_bid(self.buyer1, Decimal('110'), max_amount=Decimal('150'))
        # buyer2 bids 160 - exceeds proxy max
        self.auction.place_bid(self.buyer2, Decimal('160'))
        self.auction.refresh_from_db()
        # buyer2 should win since they exceeded the proxy max
        self.assertEqual(self.auction.current_winner, self.buyer2)

    def test_bid_history_shows_auto_bids(self):
        self.auction.place_bid(self.buyer1, Decimal('110'), max_amount=Decimal('200'))
        self.auction.place_bid(self.buyer2, Decimal('130'))
        auto_bids = Bid.objects.filter(auction=self.auction, is_auto_bid=True)
        self.assertGreater(auto_bids.count(), 0)


class AuctionAutoExtensionTest(TestCase):
    """Auctions auto-extend if bid placed in last 5 minutes."""

    def setUp(self):
        self.seller = make_user('seller4')
        self.buyer = make_user('buyer4')
        category = Category.objects.get_or_create(
            slug='test-cat2', defaults={'name': 'Test2', 'icon': 'bi-box'}
        )[0]
        item = Item.objects.create(
            title='Expiring Item', description='test',
            category=category, condition='used'
        )
        now = timezone.now()
        self.auction = Auction.objects.create(
            item=item,
            seller=self.seller,
            status='active',
            start_price=Decimal('100'),
            current_price=Decimal('100'),
            start_time=now - datetime.timedelta(hours=1),
            end_time=now + datetime.timedelta(minutes=3),  # 3 minutes left
            auto_extend=True,
        )

    def test_auto_extend_when_bid_in_last_5_minutes(self):
        original_end = self.auction.end_time
        success, bid = self.auction.place_bid(self.buyer, Decimal('110'))
        self.assertTrue(success)
        self.auction.refresh_from_db()
        # End time should have been extended
        self.assertGreater(self.auction.end_time, original_end)

    def test_auto_extend_log_created(self):
        self.auction.place_bid(self.buyer, Decimal('110'))
        log = BidLog.objects.filter(auction=self.auction, event_type='auto_extend').first()
        self.assertIsNotNone(log)

    def test_no_extend_when_more_than_5_minutes(self):
        # Create auction with 10+ minutes left
        category = Category.objects.get_or_create(
            slug='test-cat3', defaults={'name': 'Test3', 'icon': 'bi-box'}
        )[0]
        item = Item.objects.create(title='Item2', description='x', category=category, condition='used')
        now = timezone.now()
        long_auction = Auction.objects.create(
            item=item,
            seller=self.seller,
            status='active',
            start_price=Decimal('100'),
            current_price=Decimal('100'),
            start_time=now - datetime.timedelta(hours=1),
            end_time=now + datetime.timedelta(hours=2),  # 2 hours left
            auto_extend=True,
        )
        original_end = long_auction.end_time
        long_auction.place_bid(self.buyer, Decimal('110'))
        long_auction.refresh_from_db()
        self.assertEqual(long_auction.end_time, original_end)


class ReservePriceTest(TestCase):
    """Reserve price tracking."""

    def setUp(self):
        self.seller = make_user('seller5')
        self.buyer = make_user('buyer5')
        self.auction = make_auction(self.seller, start_price=100, reserve=200)

    def test_reserve_not_met_initially(self):
        self.assertFalse(self.auction.reserve_met())

    def test_reserve_met_after_sufficient_bid(self):
        self.auction.place_bid(self.buyer, Decimal('210'))
        self.auction.refresh_from_db()
        self.assertTrue(self.auction.reserve_met())

    def test_reserve_met_log_created(self):
        self.auction.place_bid(self.buyer, Decimal('210'))
        log = BidLog.objects.filter(auction=self.auction, event_type='reserve_met').first()
        self.assertIsNotNone(log)

    def test_bid_below_reserve_still_accepted(self):
        success, result = self.auction.place_bid(self.buyer, Decimal('150'))
        self.assertTrue(success)
        self.auction.refresh_from_db()
        self.assertFalse(self.auction.reserve_met())


class BidHistoryImmutabilityTest(TestCase):
    """Bid history is public and immutable."""

    def setUp(self):
        self.seller = make_user('seller6')
        self.buyer = make_user('buyer6')
        self.auction = make_auction(self.seller)

    def test_bid_log_created_for_each_bid(self):
        initial_logs = BidLog.objects.filter(auction=self.auction).count()
        self.auction.place_bid(self.buyer, Decimal('110'))
        final_logs = BidLog.objects.filter(auction=self.auction).count()
        self.assertGreater(final_logs, initial_logs)

    def test_outbid_bids_preserved_in_history(self):
        buyer2 = make_user('buyer6b')
        self.auction.place_bid(self.buyer, Decimal('110'))
        self.auction.place_bid(buyer2, Decimal('120'))
        all_bids = Bid.objects.filter(auction=self.auction)
        self.assertEqual(all_bids.count(), 2)
        outbid = all_bids.filter(status='outbid')
        self.assertEqual(outbid.count(), 1)


class EndedAuctionBiddingTest(TestCase):
    """Cannot bid on ended/inactive auctions."""

    def setUp(self):
        self.seller = make_user('seller7')
        self.buyer = make_user('buyer7')
        self.auction = make_auction(self.seller, hours=-1)  # ended 1 hour ago
        self.auction.status = 'ended'
        self.auction.save()

    def test_cannot_bid_on_ended_auction(self):
        success, result = self.auction.place_bid(self.buyer, Decimal('110'))
        self.assertFalse(success)

    def test_unauthenticated_user_cannot_bid(self):
        from django.contrib.auth.models import AnonymousUser
        anon = AnonymousUser()
        can_bid, reason = self.auction.can_user_bid(anon)
        self.assertFalse(can_bid)

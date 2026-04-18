"""
Tests for multi-strategy auction types:
  - Sealed-Bid auction
  - Dutch auction
  - Vickrey (second-price sealed-bid) auction
"""
from decimal import Decimal
import datetime

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User

from auctions.models import Category, Item, Auction
from bidding.models import Bid, BidLog
from accounts.models import UserProfile


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_user(username, password='pass1234'):
    user = User.objects.create_user(username=username, password=password)
    UserProfile.objects.get_or_create(user=user)
    return user


def make_auction(seller, auction_type='english', start_price=100, hours=24, **kwargs):
    category = Category.objects.get_or_create(
        slug='type-test', defaults={'name': 'Type Test', 'icon': 'bi-box'}
    )[0]
    item = Item.objects.create(
        title='Type Test Item', description='desc',
        category=category, condition='used'
    )
    now = timezone.now()
    return Auction.objects.create(
        item=item,
        seller=seller,
        status='active',
        auction_type=auction_type,
        start_price=Decimal(str(start_price)),
        current_price=Decimal(str(start_price)),
        start_time=now - datetime.timedelta(hours=1),
        end_time=now + datetime.timedelta(hours=hours),
        auto_extend=False,
        **kwargs
    )


# ---------------------------------------------------------------------------
# Sealed-Bid
# ---------------------------------------------------------------------------

class SealedBidAuctionTest(TestCase):

    def setUp(self):
        self.seller = make_user('sb_seller')
        self.buyer1 = make_user('sb_buyer1')
        self.buyer2 = make_user('sb_buyer2')
        self.auction = make_auction(self.seller, auction_type='sealed_bid')

    def test_bidder_can_submit_sealed_bid(self):
        success, result = self.auction.place_bid(self.buyer1, Decimal('150'))
        self.assertTrue(success)
        self.assertIsInstance(result, Bid)

    def test_bidder_cannot_bid_twice(self):
        self.auction.place_bid(self.buyer1, Decimal('150'))
        success, msg = self.auction.place_bid(self.buyer1, Decimal('200'))
        self.assertFalse(success)
        self.assertIn('already placed', msg.lower())

    def test_sealed_bid_not_winning_until_ended(self):
        success, bid = self.auction.place_bid(self.buyer1, Decimal('150'))
        self.assertTrue(success)
        self.assertFalse(bid.is_winning)

    def test_determine_winner_picks_highest_bid(self):
        self.auction.place_bid(self.buyer1, Decimal('150'))
        self.auction.place_bid(self.buyer2, Decimal('200'))
        winning_bid = self.auction.determine_sealed_bid_winner()
        self.assertIsNotNone(winning_bid)
        self.auction.refresh_from_db()
        self.assertEqual(self.auction.current_winner, self.buyer2)
        self.assertEqual(self.auction.current_price, Decimal('200'))

    def test_determine_winner_with_no_bids_returns_none(self):
        result = self.auction.determine_sealed_bid_winner()
        self.assertIsNone(result)

    def test_seller_cannot_submit_sealed_bid(self):
        success, msg = self.auction.place_bid(self.seller, Decimal('150'))
        self.assertFalse(success)
        self.assertIn('own auction', msg.lower())

    def test_bid_log_created_for_sealed_bid(self):
        self.auction.place_bid(self.buyer1, Decimal('150'))
        log = BidLog.objects.filter(auction=self.auction, event_type='bid_placed').first()
        self.assertIsNotNone(log)

    def test_negative_amount_rejected(self):
        success, msg = self.auction.place_bid(self.buyer1, Decimal('0'))
        self.assertFalse(success)


# ---------------------------------------------------------------------------
# Dutch auction
# ---------------------------------------------------------------------------

class DutchAuctionTest(TestCase):

    def setUp(self):
        self.seller = make_user('dutch_seller')
        self.buyer1 = make_user('dutch_buyer1')
        self.buyer2 = make_user('dutch_buyer2')
        self.auction = make_auction(self.seller, auction_type='dutch', start_price=500)

    def test_first_bidder_wins_dutch_auction(self):
        success, bid = self.auction.place_bid(self.buyer1, Decimal('500'))
        self.assertTrue(success)
        self.auction.refresh_from_db()
        self.assertEqual(self.auction.current_winner, self.buyer1)
        self.assertEqual(self.auction.status, 'ended')

    def test_dutch_winner_pays_current_price(self):
        self.auction.place_bid(self.buyer1, Decimal('500'))
        self.auction.refresh_from_db()
        self.assertEqual(self.auction.current_price, Decimal('500'))

    def test_second_bidder_cannot_bid_after_dutch_ends(self):
        self.auction.place_bid(self.buyer1, Decimal('500'))
        self.auction.refresh_from_db()
        success, msg = self.auction.place_bid(self.buyer2, Decimal('500'))
        self.assertFalse(success)

    def test_seller_cannot_bid_dutch(self):
        success, msg = self.auction.place_bid(self.seller, Decimal('500'))
        self.assertFalse(success)

    def test_auction_ended_log_created(self):
        self.auction.place_bid(self.buyer1, Decimal('500'))
        log = BidLog.objects.filter(auction=self.auction, event_type='auction_ended').first()
        self.assertIsNotNone(log)


# ---------------------------------------------------------------------------
# Vickrey (second-price sealed-bid)
# ---------------------------------------------------------------------------

class VickreyAuctionTest(TestCase):

    def setUp(self):
        self.seller = make_user('vck_seller')
        self.buyer1 = make_user('vck_buyer1')
        self.buyer2 = make_user('vck_buyer2')
        self.buyer3 = make_user('vck_buyer3')
        self.auction = make_auction(self.seller, auction_type='vickrey')

    def test_bidder_can_submit_vickrey_bid(self):
        success, result = self.auction.place_bid(self.buyer1, Decimal('300'))
        self.assertTrue(success)

    def test_bidder_cannot_bid_twice(self):
        self.auction.place_bid(self.buyer1, Decimal('300'))
        success, _ = self.auction.place_bid(self.buyer1, Decimal('400'))
        self.assertFalse(success)

    def test_vickrey_winner_is_highest_bidder(self):
        self.auction.place_bid(self.buyer1, Decimal('300'))
        self.auction.place_bid(self.buyer2, Decimal('500'))
        self.auction.place_bid(self.buyer3, Decimal('400'))
        winning_bid = self.auction.determine_vickrey_winner()
        self.auction.refresh_from_db()
        self.assertEqual(self.auction.current_winner, self.buyer2)

    def test_vickrey_winner_pays_second_price(self):
        self.auction.place_bid(self.buyer1, Decimal('300'))
        self.auction.place_bid(self.buyer2, Decimal('500'))
        self.auction.determine_vickrey_winner()
        self.auction.refresh_from_db()
        # Buyer2 wins, pays second-highest = 300
        self.assertEqual(self.auction.current_price, Decimal('300'))

    def test_vickrey_single_bidder_pays_own_bid(self):
        self.auction.place_bid(self.buyer1, Decimal('300'))
        self.auction.determine_vickrey_winner()
        self.auction.refresh_from_db()
        self.assertEqual(self.auction.current_price, Decimal('300'))

    def test_vickrey_no_bids_returns_none(self):
        result = self.auction.determine_vickrey_winner()
        self.assertIsNone(result)

    def test_vickrey_log_created_on_end(self):
        self.auction.place_bid(self.buyer1, Decimal('300'))
        self.auction.determine_vickrey_winner()
        log = BidLog.objects.filter(auction=self.auction, event_type='auction_ended').first()
        self.assertIsNotNone(log)
        self.assertIn('Vickrey', log.description)

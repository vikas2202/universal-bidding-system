from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
import datetime
import random
from auctions.models import Category, Item, Auction
from accounts.models import UserProfile
from bidding.models import BidLog


class Command(BaseCommand):
    help = 'Seed the database with sample auction data'

    def add_arguments(self, parser):
        parser.add_argument('--users', type=int, default=5, help='Number of sample users')
        parser.add_argument('--auctions', type=int, default=20, help='Number of sample auctions')

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write('Seeding database...')

        # Load categories
        try:
            from django.core.management import call_command
            call_command('loaddata', 'auctions/fixtures/initial_data.json', verbosity=0)
            self.stdout.write(self.style.SUCCESS('Categories loaded.'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Categories may already exist: {e}'))

        categories = list(Category.objects.all())
        if not categories:
            self.stdout.write(self.style.ERROR('No categories found. Run loaddata first.'))
            return

        # Create sample users
        users = []
        for i in range(1, options['users'] + 1):
            username = f'user{i}'
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@example.com',
                    'first_name': f'User',
                    'last_name': f'{i}',
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                UserProfile.objects.get_or_create(user=user)
                self.stdout.write(f'  Created user: {username}')
            users.append(user)

        # Sample auction data
        sample_items = [
            ("Vintage MacBook Pro 2019", "electronics", "Excellent condition MacBook Pro with 16GB RAM and 512GB SSD.", "used"),
            ("iPhone 15 Pro Max 256GB", "electronics", "Brand new, sealed box. Natural Titanium color.", "new"),
            ("1967 Ford Mustang Fastback", "vehicles", "Classic muscle car, fully restored, numbers matching.", "used"),
            ("Oil Painting - Sunset Over Mountains", "art", "Original oil on canvas, 24x36 inches, signed.", "used"),
            ("Rare 1952 Mickey Mantle Baseball Card", "collectibles", "PSA graded 7 NM. One of the most iconic baseball cards.", "used"),
            ("Louis Vuitton Monogram Bag", "fashion", "Authentic LV bag, gently used, with dust bag.", "used"),
            ("Signed Michael Jordan Jersey", "sports", "Game-worn jersey from the 1996 Championship season, COA included.", "used"),
            ("18K Gold Diamond Ring", "jewelry", "2.5 carat diamond solitaire, GIA certified.", "new"),
            ("First Edition Harry Potter", "books", "Harry Potter and the Philosopher's Stone, UK first edition.", "used"),
            ("Gaming PC RTX 4090", "electronics", "Custom built, RTX 4090, Intel i9-13900K, 64GB DDR5 RAM.", "new"),
            ("Rolex Submariner Watch", "jewelry", "2022 model, box and papers included.", "used"),
            ("Acoustic Guitar Martin D-45", "other", "Premium Martin acoustic guitar, barely played.", "used"),
            ("Abstract Bronze Sculpture", "art", "Hand-crafted bronze sculpture, limited edition 3/10.", "new"),
            ("Vintage Levi's 501 Jeans", "fashion", "1980s deadstock Levi's, never worn, size 32x32.", "new"),
            ("Mountain Bike Trek Fuel EX", "sports", "Full suspension trail bike, 2023 model.", "used"),
        ]

        num_auctions = min(options['auctions'], len(sample_items))
        now = timezone.now()

        for i, (title, cat_slug, desc, condition) in enumerate(sample_items[:num_auctions]):
            seller = random.choice(users)
            try:
                category = Category.objects.get(slug=cat_slug)
            except Category.DoesNotExist:
                category = random.choice(categories)

            start_price = Decimal(str(random.choice([10, 25, 50, 100, 200, 500, 1000, 2500])))
            has_reserve = random.random() > 0.5
            has_buy_now = random.random() > 0.6

            days_offset = random.randint(-2, 5)
            hours_ahead = random.randint(1, 72)
            start_time = now - datetime.timedelta(days=1)
            end_time = now + datetime.timedelta(days=days_offset, hours=hours_ahead)
            if end_time <= now:
                status = 'ended'
                end_time = now - datetime.timedelta(hours=random.randint(1, 48))
            else:
                status = 'active'

            item = Item.objects.create(
                title=title,
                description=desc,
                category=category,
                condition=condition,
            )

            reserve = start_price * Decimal('1.5') if has_reserve else None
            buy_now = start_price * Decimal('2.5') if has_buy_now else None

            auction = Auction.objects.create(
                item=item,
                seller=seller,
                status=status,
                start_price=start_price,
                reserve_price=reserve,
                buy_now_price=buy_now,
                current_price=start_price,
                start_time=start_time,
                end_time=end_time,
                auto_extend=True,
            )

            BidLog.objects.create(
                auction=auction,
                event_type='auction_started',
                description=f"Auction started by {seller.username} at ${start_price}"
            )

            # Add some bids
            if status == 'active' or status == 'ended':
                bidders = [u for u in users if u != seller]
                if bidders:
                    current = start_price
                    winner = None
                    for _ in range(random.randint(0, 5)):
                        bidder = random.choice(bidders)
                        increment = max(Decimal('1.00'), current * Decimal('0.05'))
                        new_amount = current + increment + Decimal(str(random.uniform(0, float(increment))))
                        new_amount = new_amount.quantize(Decimal('0.01'))

                        from bidding.models import Bid
                        if winner:
                            Bid.objects.filter(auction=auction, is_winning=True).update(
                                is_winning=False, status='outbid'
                            )
                        bid = Bid.objects.create(
                            auction=auction,
                            bidder=bidder,
                            amount=new_amount,
                            is_winning=True,
                            status='active' if status == 'active' else 'won',
                        )
                        current = new_amount
                        winner = bidder

                    auction.current_price = current
                    auction.current_winner = winner
                    auction.save()

            self.stdout.write(f'  Created auction: {title} ({status})')

        self.stdout.write(self.style.SUCCESS(
            f'\nSeeding complete! Created {num_auctions} auctions for {len(users)} users.'
        ))
        self.stdout.write('Test credentials: username=user1, password=password123')

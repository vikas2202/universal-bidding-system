from django.db import migrations


CATEGORIES = [
    {"pk": 1,  "name": "Electronics",              "slug": "electronics",             "description": "Phones, laptops, gadgets and more",           "icon": "bi-cpu",                "group": "physical"},
    {"pk": 2,  "name": "Clothing & Fashion",        "slug": "clothing-fashion",        "description": "Apparel, shoes, accessories",                 "icon": "bi-handbag",            "group": "physical"},
    {"pk": 3,  "name": "Furniture & Home Decor",    "slug": "furniture-home-decor",    "description": "Furniture, décor and household items",        "icon": "bi-house-door",         "group": "physical"},
    {"pk": 4,  "name": "Vehicles",                  "slug": "vehicles",                "description": "Cars, bikes, EVs and more",                   "icon": "bi-car-front",          "group": "physical"},
    {"pk": 5,  "name": "Books & Stationery",        "slug": "books-stationery",        "description": "Books, notebooks, pens and stationery",       "icon": "bi-book",               "group": "physical"},
    {"pk": 6,  "name": "Toys & Games",              "slug": "toys-games",              "description": "Toys, board games, kids' items",              "icon": "bi-controller",         "group": "physical"},
    {"pk": 7,  "name": "Sports Equipment",          "slug": "sports-equipment",        "description": "Sports gear and memorabilia",                 "icon": "bi-trophy",             "group": "physical"},
    {"pk": 8,  "name": "Jewelry & Watches",         "slug": "jewelry-watches",         "description": "Rings, necklaces, watches and more",          "icon": "bi-stars",              "group": "physical"},
    {"pk": 9,  "name": "Antiques & Collectibles",   "slug": "antiques-collectibles",   "description": "Rare, vintage and collector items",           "icon": "bi-gem",                "group": "physical"},
    {"pk": 10, "name": "Art Pieces",                "slug": "art-pieces",              "description": "Paintings, sculptures and fine art",          "icon": "bi-palette",            "group": "physical"},
    {"pk": 11, "name": "Musical Instruments",       "slug": "musical-instruments",     "description": "Guitars, pianos, studio gear and more",      "icon": "bi-music-note-beamed",  "group": "physical"},
    {"pk": 12, "name": "Domain Names",              "slug": "domain-names",            "description": "Premium and expired domain names",            "icon": "bi-globe",              "group": "digital"},
    {"pk": 13, "name": "Websites & Web Apps",       "slug": "websites-web-apps",       "description": "Revenue-generating websites and web apps",   "icon": "bi-browser-chrome",     "group": "digital"},
    {"pk": 14, "name": "Mobile Apps",               "slug": "mobile-apps",             "description": "iOS and Android app listings",                "icon": "bi-phone",              "group": "digital"},
    {"pk": 15, "name": "NFTs & Digital Art",        "slug": "nfts-digital-art",        "description": "NFTs, digital collectibles and crypto art",   "icon": "bi-shield-lock",        "group": "digital"},
    {"pk": 16, "name": "Software & SaaS Licenses",  "slug": "software-saas",           "description": "Software licenses, SaaS subscriptions",      "icon": "bi-box-seam",           "group": "digital"},
    {"pk": 17, "name": "Game Assets & Accounts",    "slug": "game-assets-accounts",    "description": "Game skins, in-game items, accounts",        "icon": "bi-joystick",           "group": "digital"},
    {"pk": 18, "name": "Social Media Handles",      "slug": "social-media-handles",    "description": "Social media pages and handle listings",     "icon": "bi-people",             "group": "digital"},
    {"pk": 19, "name": "Digital Templates",         "slug": "digital-templates",       "description": "UI kits, website themes, design assets",     "icon": "bi-layout-wtf",         "group": "digital"},
    {"pk": 20, "name": "Freelance Work",            "slug": "freelance-work",          "description": "Dev, design, writing and other freelance",   "icon": "bi-laptop",             "group": "services"},
    {"pk": 21, "name": "Graphic Design & Logos",    "slug": "graphic-design-logos",    "description": "Logo design, branding and graphic work",     "icon": "bi-vector-pen",         "group": "services"},
    {"pk": 22, "name": "Video Editing & Animation", "slug": "video-editing",           "description": "Video production, animation and editing",    "icon": "bi-camera-video",       "group": "services"},
    {"pk": 23, "name": "Digital Marketing & SEO",   "slug": "digital-marketing-seo",   "description": "Marketing campaigns, SEO and growth",        "icon": "bi-bar-chart-line",     "group": "services"},
    {"pk": 24, "name": "Consulting",                "slug": "consulting",              "description": "Business, tech and legal consulting",         "icon": "bi-briefcase",          "group": "services"},
    {"pk": 25, "name": "Tutoring & Coaching",       "slug": "tutoring-coaching",       "description": "Online tutoring, mentoring and coaching",    "icon": "bi-mortarboard",        "group": "services"},
    {"pk": 26, "name": "Fitness Training",          "slug": "fitness-training",        "description": "Personal training and fitness programs",     "icon": "bi-heart-pulse",        "group": "services"},
    {"pk": 27, "name": "Home Services",             "slug": "home-services",           "description": "Repair, cleaning and household services",    "icon": "bi-tools",              "group": "services"},
    {"pk": 28, "name": "Houses & Flats",            "slug": "houses-flats",            "description": "Residential property listings",              "icon": "bi-house",              "group": "realestate"},
    {"pk": 29, "name": "Land & Plots",              "slug": "land-plots",              "description": "Land parcels and development plots",          "icon": "bi-map",                "group": "realestate"},
    {"pk": 30, "name": "Commercial Spaces",         "slug": "commercial-spaces",       "description": "Office and commercial real estate",          "icon": "bi-building",           "group": "realestate"},
    {"pk": 31, "name": "Rental Listings",           "slug": "rental-listings",         "description": "Short and long term rental properties",      "icon": "bi-key",                "group": "realestate"},
    {"pk": 32, "name": "Parking Spaces",            "slug": "parking-spaces",          "description": "Parking spots and garage spaces",            "icon": "bi-p-circle",           "group": "realestate"},
    {"pk": 33, "name": "Event Tickets",             "slug": "event-tickets",           "description": "Concert, sports and festival tickets",        "icon": "bi-ticket-perforated",  "group": "tickets"},
    {"pk": 34, "name": "VIP Passes",                "slug": "vip-passes",              "description": "Backstage passes, VIP access and more",      "icon": "bi-star",               "group": "tickets"},
    {"pk": 35, "name": "Travel Tickets",            "slug": "travel-tickets",          "description": "Flight, train and bus ticket resale",         "icon": "bi-airplane",           "group": "tickets"},
    {"pk": 36, "name": "Membership Access",         "slug": "membership-access",       "description": "Club, gym and subscription memberships",     "icon": "bi-person-badge",       "group": "tickets"},
    {"pk": 37, "name": "Courses & Certifications",  "slug": "courses-certifications",  "description": "Online courses, certifications and diplomas", "icon": "bi-award",              "group": "education"},
    {"pk": 38, "name": "Mentorship Programs",       "slug": "mentorship-programs",     "description": "1-on-1 and group mentorship offerings",      "icon": "bi-person-check",       "group": "education"},
    {"pk": 39, "name": "Internship Opportunities",  "slug": "internship-opportunities","description": "Paid and unpaid internship placements",      "icon": "bi-person-workspace",   "group": "education"},
    {"pk": 40, "name": "Project Collaborations",    "slug": "project-collaborations",  "description": "Open-source and paid project collabs",       "icon": "bi-diagram-3",          "group": "education"},
    {"pk": 41, "name": "Machinery",                 "slug": "machinery",               "description": "Industrial and agricultural machinery",      "icon": "bi-gear-wide-connected", "group": "industrial"},
    {"pk": 42, "name": "Construction Equipment",    "slug": "construction-equipment",  "description": "Heavy equipment and construction tools",     "icon": "bi-wrench-adjustable",  "group": "industrial"},
    {"pk": 43, "name": "Raw Materials",             "slug": "raw-materials",           "description": "Steel, wood, cement and bulk materials",     "icon": "bi-boxes",              "group": "industrial"},
    {"pk": 44, "name": "Bulk Inventory / Wholesale","slug": "bulk-inventory",          "description": "Wholesale lots and bulk stock listings",     "icon": "bi-stack",              "group": "industrial"},
    {"pk": 45, "name": "Ad Slots",                  "slug": "ad-slots",                "description": "Website and app advertising slots",          "icon": "bi-megaphone",          "group": "financial"},
    {"pk": 46, "name": "Sponsorship Deals",         "slug": "sponsorship-deals",       "description": "Brand sponsorships and partnership deals",   "icon": "bi-handshake",          "group": "financial"},
    {"pk": 47, "name": "Contract Bidding",          "slug": "contract-bidding",        "description": "Government and enterprise contract tenders", "icon": "bi-file-earmark-text",  "group": "financial"},
    {"pk": 48, "name": "API & Cloud Resources",     "slug": "api-cloud-resources",     "description": "API credits, cloud resource auctions",      "icon": "bi-cloud",              "group": "financial"},
    {"pk": 49, "name": "Data Sets",                 "slug": "data-sets",               "description": "Curated and labelled data set listings",     "icon": "bi-database",           "group": "financial"},
    {"pk": 50, "name": "Gaming Accounts",           "slug": "gaming-accounts",         "description": "Levelled-up game accounts and profiles",     "icon": "bi-controller",         "group": "entertainment"},
    {"pk": 51, "name": "In-Game Items & Currency",  "slug": "in-game-items",           "description": "Virtual currency, skins and rare items",     "icon": "bi-coin",               "group": "entertainment"},
    {"pk": 52, "name": "Streaming Shoutouts",       "slug": "streaming-shoutouts",     "description": "Shoutouts from streamers and influencers",   "icon": "bi-broadcast",          "group": "entertainment"},
    {"pk": 53, "name": "Content Collaborations",    "slug": "content-collaborations",  "description": "YouTube, TikTok and social media collabs",   "icon": "bi-camera",             "group": "entertainment"},
    {"pk": 54, "name": "Post Anything",             "slug": "post-anything",           "description": "Open listing – bid on anything",             "icon": "bi-plus-circle",        "group": "custom"},
    {"pk": 55, "name": "Reverse Bidding",           "slug": "reverse-bidding",         "description": "Lowest price wins auction format",           "icon": "bi-arrow-down-circle",  "group": "custom"},
    {"pk": 56, "name": "Time-Based Auctions",       "slug": "time-based-auctions",     "description": "Flash and time-limited auction listings",    "icon": "bi-clock-history",      "group": "custom"},
    {"pk": 57, "name": "Group & Team Bidding",      "slug": "group-team-bidding",      "description": "Collaborative group or team bidding",        "icon": "bi-people-fill",        "group": "custom"},
]


def load_categories(apps, schema_editor):
    Category = apps.get_model('auctions', 'Category')
    for data in CATEGORIES:
        Category.objects.get_or_create(
            slug=data['slug'],
            defaults={
                'name': data['name'],
                'description': data['description'],
                'icon': data['icon'],
                'group': data['group'],
            },
        )


def unload_categories(apps, schema_editor):
    Category = apps.get_model('auctions', 'Category')
    slugs = [d['slug'] for d in CATEGORIES]
    Category.objects.filter(slug__in=slugs).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0003_add_category_group'),
    ]

    operations = [
        migrations.RunPython(load_categories, reverse_code=unload_categories),
    ]

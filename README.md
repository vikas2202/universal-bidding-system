# BidHub – Universal Bidding System

A full-featured, production-ready **Universal Bidding System** built with **Django & Python**.  
Designed with strict anti-fraud rules and complete transparency to ensure fair, tamper-proof auctions.

---

## ✨ Features

### Bidding & Auction Engine
| Feature | Description |
|---|---|
| **Live Auctions** | Real-time price updates via AJAX polling (every 15 s) |
| **Proxy Bidding** | Set a maximum – the system auto-bids on your behalf up to that amount |
| **Auto-extension** | A bid placed in the last 5 minutes extends the auction by 5 minutes |
| **Reserve Price** | Hidden minimum price; seller is notified when met |
| **Buy-Now Price** | Instant purchase option that ends the auction immediately |
| **Bid Increment** | Enforced as `max($1.00, 5% of current price)` – server-side only |
| **Countdown Timer** | Live JavaScript timer on every auction page |

### Anti-Fraud & Fairness
| Rule | Implementation |
|---|---|
| **Shill bidding prevention** | Sellers are blocked from bidding on their own auctions |
| **Immutable bid history** | `BidLog` audit trail – admin panel disables deletion |
| **Server-side time checks** | Auction end times enforced on the server, not the client |
| **IP rate limiting** | Max 10 bids per minute per IP address (Django cache) |
| **Public transparency** | Full bid history (including auto-bids) visible to all users |

### User Features
- Registration & authentication
- User profiles with seller/buyer ratings
- Personal dashboard (active bids, won auctions, selling)
- Watchlist management
- In-app notifications (outbid, won, reserve met, buy-now)

### Admin
- Full Django admin for all models
- Auction moderation and monitoring
- Bid log audit trail

---

## 🚀 Quick Start

### 1. Clone & install dependencies

```bash
git clone <repo-url>
cd universal-bidding-system
pip install -r requirements.txt
```

### 2. Set environment variables

```bash
export DJANGO_SECRET_KEY='your-secret-key-here'   # required
export DJANGO_DEBUG='True'                         # development only
export DJANGO_ALLOWED_HOSTS='localhost,127.0.0.1'  # optional; defaults to localhost in DEBUG
```

### 3. Database setup

```bash
python manage.py migrate
python manage.py loaddata auctions/fixtures/initial_data.json  # load categories
python manage.py seed_data                                     # create sample auctions
```

### 4. Create superuser (optional)

```bash
python manage.py createsuperuser
```

### 5. Run the development server

```bash
python manage.py runserver
```

Visit **http://127.0.0.1:8000/** to see the application.

**Test credentials** (created by `seed_data`):
- Username: `user1` | Password: `password123`
- Username: `user2` | Password: `password123`

**Admin panel**: http://127.0.0.1:8000/admin/

---

## 🗂 Project Structure

```
universal-bidding-system/
├── universal_bidding/       # Django project settings & URLs
├── accounts/                # User registration, auth, profiles, ratings
├── auctions/                # Auction & item models, views, templates
│   ├── fixtures/            # Initial categories fixture
│   └── management/commands/ # seed_data command
├── bidding/                 # Bid placement, proxy bidding, BidLog
│   └── tests/               # 25 unit tests for all anti-fraud rules
├── notifications/           # In-app notification system
├── static/
│   ├── css/style.css        # Bootstrap 5 customisation
│   └── js/bidding.js        # Countdown timers, AJAX bidding, auto-refresh
└── templates/               # Base templates (base.html, 404, 500)
```

---

## 🧪 Running Tests

```bash
DJANGO_DEBUG=True python manage.py test
```

The test suite covers:
- Shill bidding prevention
- Bid increment validation
- Proxy bidding logic
- Auto-extension on last-minute bids
- Reserve price tracking
- Bid history immutability
- Ended-auction bid rejection

---

## ⚙️ Configuration

| Environment Variable | Default | Description |
|---|---|---|
| `DJANGO_SECRET_KEY` | *required in production* | Django secret key |
| `DJANGO_DEBUG` | `False` | Enable debug mode |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` (in DEBUG) | Comma-separated allowed hosts |

---

## 📸 Pages

| URL | Description |
|---|---|
| `/` | Homepage – featured auctions, categories, stats |
| `/auctions/` | Browse all active auctions |
| `/auctions/<id>/` | Auction detail – bidding, history, countdown |
| `/auctions/create/` | Create a new auction |
| `/accounts/register/` | User registration |
| `/accounts/login/` | Login |
| `/accounts/dashboard/` | Personal dashboard |
| `/accounts/profile/<username>/` | Public user profile |
| `/notifications/` | Notification inbox |
| `/admin/` | Admin panel |

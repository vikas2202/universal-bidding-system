# BidHub – Universal Bidding System

A full-featured, production-ready **Universal Bidding System** built with **Django & Python**.  
Designed with strict anti-fraud rules and complete transparency to ensure fair, tamper-proof auctions.

---

## ✨ Features

### Multi-Strategy Bidding Engine
| Auction Type | Description |
|---|---|
| **English Auction** | Ascending price; highest bid wins at end |
| **Sealed-Bid Auction** | All bids are hidden; highest bid wins when auction ends |
| **Dutch Auction** | Descending price; first bidder to accept wins immediately |
| **Vickrey Auction** | Second-price sealed bid; winner pays the second-highest bid |

### Bidding Engine
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
| **Blacklist system** | Admins can blacklist users; blacklisted users cannot bid |
| **Bid anomaly detection** | Z-score analysis flags statistically unusual bid amounts |
| **Rapid-fire detection** | Flags > 5 bids by the same user on one auction within 10 minutes |
| **Collusion detection** | Flags multiple different accounts bidding from the same IP |
| **Shill-pattern detection** | Flags bidders who bid on ≥ 5 of a seller's auctions but never win |
| **Trust score** | Per-user 0–100 score reduced automatically when fraud flags are raised |

### User Management & Compliance
- User roles: **Bidder**, **Auctioneer**, **Moderator**, **Admin**
- KYC (Know Your Customer) status tracking: None → Pending → Approved / Rejected
- Bidder trust score (0–100; reduced by fraud flags)
- User profiles with seller/buyer ratings
- Personal dashboard (active bids, won auctions, selling)
- Watchlist management
- In-app notifications (outbid, won, reserve met, buy-now)

### Admin & Monitoring
- Full Django admin for all models
- **Fraud detection dashboard** at `/fraud/dashboard/` (staff only)
- **Per-user risk profile** with collusion, anomaly and shill scores
- Auction moderation with auction-type filter
- KYC approval/rejection bulk actions
- Blacklist management actions
- Immutable bid log and fraud flag audit trails

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
**Fraud dashboard**: http://127.0.0.1:8000/fraud/dashboard/ (staff only)

---

## 🌐 Deploy Online (Production)

### Recommended hosting options
- **Fastest:** Docker on a VPS (AWS Lightsail / DigitalOcean / EC2)
- **Managed:** Render / Railway / Fly (web + Postgres + Redis as separate services)

### A) VPS deployment with Docker (step-by-step)

1. **Provision server + domain**
   - Create Ubuntu server
   - Point your DNS A record to the server IP
   - Open only ports `80` and `443` in firewall/security group

2. **Install Docker**
```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin
sudo usermod -aG docker $USER
```

3. **Clone project and configure env**
```bash
git clone <repo-url>
cd universal-bidding-system
cp .env.example .env
```
Edit `.env` with:
- Strong `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG=False`
- Real `DJANGO_ALLOWED_HOSTS` and `DJANGO_CSRF_TRUSTED_ORIGINS`

4. **Start production stack**
```bash
docker compose -f docker/docker-compose.yml up -d --build
```
Services started:
- `web` (Django + Gunicorn)
- `worker` (Celery worker)
- `beat` (Celery scheduler)
- `db` (PostgreSQL)
- `redis` (cache/broker)
- `nginx` (reverse proxy, serves static/media)

5. **First-time setup**
```bash
docker compose -f docker/docker-compose.yml exec web python manage.py migrate
docker compose -f docker/docker-compose.yml exec web python manage.py createsuperuser
```
Optional demo data:
```bash
docker compose -f docker/docker-compose.yml exec web python manage.py loaddata auctions/fixtures/initial_data.json
docker compose -f docker/docker-compose.yml exec web python manage.py seed_data
```

6. **HTTPS**
- Use Nginx + Certbot on the VPS, or put Cloudflare/Load Balancer in front and terminate TLS there.
- Set `DJANGO_CSRF_TRUSTED_ORIGINS` to your `https://` domain values.

7. **Validate live behavior**
- Login, create auction, place bids, verify notifications/fraud pages
- Confirm Celery is healthy:
```bash
docker compose -f docker/docker-compose.yml logs -f worker beat
```
- Confirm web/db/redis health:
```bash
docker compose -f docker/docker-compose.yml ps
```

8. **Ongoing operations**
- Enable automated Postgres backups
- Back up media volume
- Add monitoring/alerts and central log collection
- Deploy via CI/CD on push to `main`

### B) Managed platform notes (Render/Railway/Fly)
- Use a **web service** for Django/Gunicorn
- Add managed **PostgreSQL** and **Redis**
- Add separate **worker** and **beat** services using Celery commands
- Set environment variables from `.env.example`
- Run migrations during deploy and create superuser once

---

## 🗂 Project Structure

```
universal-bidding-system/
├── universal_bidding/       # Django project settings & URLs
├── accounts/                # User registration, auth, profiles, roles, KYC, ratings
├── auctions/                # Auction & item models, multi-strategy bidding engines
│   ├── fixtures/            # Initial categories fixture
│   └── management/commands/ # seed_data command
├── bidding/                 # Bid placement, proxy bidding, BidLog
│   └── tests/               # 25 unit tests for all anti-fraud rules
├── fraud_detection/         # Fraud analysis services, FraudFlag, BidderRiskProfile
├── notifications/           # In-app notification system
├── docker/                  # Dockerfile, docker-compose.yml, nginx.conf
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

The test suite (**63 tests**) covers:

**Core bidding rules** (`bidding/tests/`)
- Shill bidding prevention (seller can't bid on own auction)
- Bid increment validation
- Proxy bidding logic
- Auto-extension on last-minute bids
- Reserve price tracking
- Bid history immutability
- Ended-auction bid rejection

**Auction types** (`auctions/tests.py`)
- Sealed-bid: single submission, winner determination, seller blocked
- Dutch: first-bidder wins, auction ends immediately, duplicate prevention
- Vickrey: second-price logic, winner determination, edge cases

**Fraud detection** (`fraud_detection/tests.py`)
- Bid anomaly detection (Z-score outlier analysis)
- Rapid-fire bidding detection (time-window check)
- Collusion detection (shared IP, different users)
- Shill-pattern detection (bidder never wins seller's auctions)
- Risk profile updates and score calculations
- Trust score floor enforcement
- Blacklisted user bid rejection

---

## ⚙️ Configuration

| Environment Variable | Default | Description |
|---|---|---|
| `DJANGO_SECRET_KEY` | *required in production* | Django secret key |
| `DJANGO_DEBUG` | `False` | Enable debug mode |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` (in DEBUG) | Comma-separated allowed hosts |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `` | Comma-separated trusted origins (use `https://...` in production) |
| `DJANGO_SECURE_SSL_REDIRECT` | `True` (when `DJANGO_DEBUG=False`) | Redirect HTTP to HTTPS |
| `DJANGO_SECURE_HSTS_SECONDS` | `3600` | HSTS max age |
| `DB_ENGINE` | `postgresql` (when set) | Database backend selector |
| `DATABASE_URL` | `` | Optional Postgres URL (takes priority over `POSTGRES_*`) |
| `POSTGRES_DB` | `bidding_db` | PostgreSQL database name |
| `POSTGRES_USER` | `bidding_user` | PostgreSQL username |
| `POSTGRES_PASSWORD` | `` | PostgreSQL password |
| `POSTGRES_HOST` | `db` | PostgreSQL host |
| `POSTGRES_PORT` | `5432` | PostgreSQL port |
| `POSTGRES_SSLMODE` | `` | Optional SSL mode for PostgreSQL (`require`, etc.) |
| `DB_CONN_MAX_AGE` | `60` | Persistent DB connection lifetime (seconds) |
| `REDIS_URL` | `redis://127.0.0.1:6379/0` | Redis URL for cache/channels/celery |

---

## 📸 Pages

| URL | Description |
|---|---|
| `/` | Homepage – featured auctions, categories, stats |
| `/auctions/` | Browse all active auctions |
| `/auctions/<id>/` | Auction detail – bidding, history, countdown |
| `/auctions/create/` | Create a new auction (choose auction type) |
| `/accounts/register/` | User registration |
| `/accounts/login/` | Login |
| `/accounts/dashboard/` | Personal dashboard |
| `/accounts/profile/<username>/` | Public user profile |
| `/notifications/` | Notification inbox |
| `/fraud/dashboard/` | Fraud detection dashboard (staff only) |
| `/fraud/user/<id>/` | Per-user risk profile (staff only) |
| `/admin/` | Admin panel |

import os
import sqlite3
import uuid
import re
import secrets
import logging
from datetime import datetime, date
from functools import wraps
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, g, jsonify, abort
)

# ---------- Environment Configuration & Secrets ----------
# Load from environment variables with safe development fallbacks
SECRET_KEY = os.environ.get('SECRET_KEY', 'glowgrace-luxury-sanctuary-production-key-2026')
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'GlowGrace@2024')
FLASK_DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() in ('true', '1', 'yes')
DATABASE = os.environ.get('DATABASE_PATH', os.path.join(os.path.dirname(__file__), 'salon.db'))

app = Flask(__name__)
app.secret_key = SECRET_KEY

# Secure session cookies configuration
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=False, # Set to True when running under HTTPS in production
    PERMANENT_SESSION_LIFETIME=86400 # 24 hours
)

# ---------- Logging Configuration ----------
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
)
logger = logging.getLogger('glow_grace_salon')

# ---------- Configurable Business Details (Single Source of Truth) ----------
SALON_CONFIG = {
    "name": "Glow & Grace Salon",
    "tagline": "Luxury Beauty & Personal Care Sanctuary",
    "whatsapp_number": "919876543210", 
    "whatsapp_display": "+91 98765 43210",
    "phone": "+1 (234) 567-890",
    "phone_clean": "+1234567890",
    "email": "concierge@glowandgracesalon.com",
    "address_line1": "123 Beauty Ave, Citytown",
    "address_line2": "Convenient street & valet parking available",
    "working_days": "Monday through Sunday (7 Days a Week)",
    "hours_weekday": "9:00 AM – 8:00 PM (Monday – Friday)",
    "hours_saturday": "9:00 AM – 7:00 PM (Saturday)",
    "hours_sunday": "10:00 AM – 5:00 PM (Sunday)",
    "maps_embed_url": None,
    "social": {
        "instagram": "https://instagram.com",
        "facebook": "https://facebook.com",
        "pinterest": "https://pinterest.com",
        "tiktok": "https://tiktok.com"
    }
}

# ---------- CSRF Protection Helper ----------
def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(24)
    return session['_csrf_token']

def validate_csrf():
    token = session.get('_csrf_token', None)
    req_token = request.form.get('csrf_token') or request.headers.get('X-CSRFToken')
    if not token or not req_token or not secrets.compare_digest(token, req_token):
        logger.warning(f"CSRF validation failed for route: {request.path} from IP: {request.remote_addr}")
        return False
    return True

@app.before_request
def csrf_protect():
    # Only protect state-changing requests (POST, PUT, DELETE, PATCH)
    if request.method in ('POST', 'PUT', 'DELETE', 'PATCH'):
        # Allow JSON API endpoints if any, or validate form
        if not validate_csrf():
            flash('Your session expired or the request was invalid. Please try again.', 'warning')
            return redirect(request.referrer or url_for('index'))

@app.context_processor
def inject_globals():
    return {
        "salon_config": SALON_CONFIG,
        "default_whatsapp_msg": "Hello Glow & Grace Salon! I would like to enquire about your services and appointment availability.",
        "csrf_token": generate_csrf_token
    }

# ---------- Database Helpers ----------
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA foreign_keys=ON")
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def generate_ref():
    """Generate a short unique appointment reference number: GG-XXXXXX."""
    return 'GG-' + uuid.uuid4().hex[:6].upper()

# ---------- Database Schema & Seeding ----------
INITIAL_SERVICES = [
    # HAIR SERVICES
    ("hair-1", "Basic Haircut", "Hair", "hair", 500, 399, "35 mins", "Popular", 1, "Precision haircut tailored to your face shape and hair texture, completed with a blow-dry finish."),
    ("hair-2", "Hair Wash & Blow Dry", "Hair", "hair", 600, 499, "40 mins", "Everyday Favorite", 0, "Gentle scalp cleansing shampoo followed by deep conditioning and a salon-style blowout for bouncy volume."),
    ("hair-3", "Hair Spa", "Hair", "hair", 1500, 1199, "60 mins", "Deep Care", 1, "Intense moisture-infusion hair spa with soothing acupressure scalp massage and therapeutic steam treatment."),
    ("hair-4", "Hair Smoothening", "Hair", "hair", 4000, 3499, "180 mins", "Silk Finish", 0, "Smoothing formula that tames stubborn frizz, seals the cuticle layer, and leaves hair naturally soft and manageable."),
    ("hair-5", "Hair Straightening", "Hair", "hair", 5000, 4499, "180 mins", "Sleek Look", 0, "Permanent straightening system with protective agents to deliver sleek, straight, and glossy tresses."),
    ("hair-6", "Global Hair Colour", "Hair", "hair", 3000, 2499, "90 mins", "Signature Colour", 1, "All-over rich uniform hair colouring with conditioning botanicals for vibrant tone and multidimensional shine."),
    ("hair-7", "Hair Highlights", "Hair", "hair", 3500, 2999, "120 mins", "Dimension", 0, "Customized streak or foil highlights placed strategically to illuminate your features and add visual depth."),
    ("hair-8", "Hair Styling", "Hair", "hair", 800, 699, "45 mins", "Party Ready", 0, "Iron curls, beach waves, or super-straight thermal styling tailored for casual dinners and day celebrations."),
    # SKINCARE & FACIAL SERVICES
    ("skin-1", "Basic Cleanup", "Skin", "skin", 800, 599, "40 mins", "Instant Refresh", 0, "Essential skin detox featuring pore cleansing, steam, blackhead removal, and a balancing clay face pack."),
    ("skin-2", "Fruit Facial", "Skin", "skin", 1200, 999, "50 mins", "Natural Glow", 0, "Natural fruit extracts rich in essential vitamins to gently exfoliate, rehydrate, and brighten dull tired skin."),
    ("skin-3", "Gold Facial", "Skin", "skin", 1800, 1499, "60 mins", "Radiance", 1, "Luxurious skin treatment utilizing gold dust and herbal serums to improve firmness and reveal radiant glow."),
    ("skin-4", "Hydrating Facial", "Skin", "skin", 2000, 1699, "60 mins", "Moisture Lock", 0, "Intense hyaluronic acid hydration therapy tailored for dry or dehydrated skin to restore elasticity."),
    ("skin-5", "Deep Cleansing Facial", "Skin", "skin", 1500, 1299, "60 mins", "Clarifying", 0, "Purifying facial targeting acne-prone or congested skin with gentle exfoliation and antibacterial mask."),
    ("skin-6", "Face Bleach", "Skin", "skin", 500, 399, "25 mins", "Even Tone", 0, "Gentle herbal bleach to lighten facial hair, diminish tan, and provide an even, brightened complexion."),
    # MAKEUP SERVICES
    ("makeup-1", "Party Makeup", "Makeup", "makeup", 2500, 1999, "60 mins", "Celebration", 0, "Flawless evening makeup with glowing base, eye definition, and lip tint customized to your party outfit."),
    ("makeup-2", "Engagement Makeup", "Makeup", "makeup", 5000, 4499, "90 mins", "High Definition", 0, "HD makeup finish with radiant highlighting, smudge-proof eye artistry, and lasting coverage for photo shoots."),
    ("makeup-3", "Bridal Makeup", "Makeup", "makeup", 15000, 12999, "180 mins", "Exclusive Bridal", 1, "Complete luxury bridal makeover including HD makeup, hair placement, jewelry styling, and dupatta draping."),
    ("makeup-4", "Hairstyling for Events", "Makeup", "makeup", 1500, 1199, "60 mins", "Artistic", 0, "Intricate event hairstyles including messy buns, structured updos, and delicate waterfall braids."),
    # NAIL SERVICES
    ("nails-1", "Basic Manicure", "Nails", "nails", 700, 599, "40 mins", "Hand Care", 0, "Nail shaping, cuticle trimming, exfoliating hand scrub, relaxing massage, and salon polish application."),
    ("nails-2", "Basic Pedicure", "Nails", "nails", 900, 749, "50 mins", "Relaxing", 1, "Warm foot bath, dead-skin buffing, nail grooming, foot massage, and fresh long-wear polish finish."),
    ("nails-3", "Nail Art", "Nails", "nails", 1000, 799, "45 mins", "Creative", 0, "Expressive nail art ranging from minimalist French tips to custom chrome powder, foils, and motifs."),
    ("nails-4", "Gel Nail Polish", "Nails", "nails", 1200, 999, "45 mins", "Long Lasting", 0, "High-shine UV gel polish providing chip-resistant wear and mirror gloss for up to three weeks."),
    # WAXING & THREADING
    ("wax-1", "Full Arms Waxing", "Waxing", "waxing", 600, 499, "25 mins", "Gentle", 0, "Thorough hair removal for full arms followed by calming aloe vera lotion to prevent redness."),
    ("wax-2", "Half Legs Waxing", "Waxing", "waxing", 500, 399, "25 mins", "Quick Care", 0, "Smooth lower-leg waxing utilizing sensitive-skin wax for a silky, stubble-free feel."),
    ("wax-3", "Full Legs Waxing", "Waxing", "waxing", 900, 749, "45 mins", "Silky Smooth", 0, "Complete leg waxing treatment delivering clean, silky, hair-free skin with soothing aftercare."),
    ("wax-4", "Full Body Waxing", "Waxing", "waxing", 2500, 2199, "90 mins", "Full Body Care", 1, "Complete head-to-toe waxing package performed with hygienic, temperature-controlled wax."),
    ("wax-5", "Eyebrow Threading", "Waxing", "waxing", 100, 79, "15 mins", "Essential", 0, "Precise brow arch definition with 100% antibacterial cotton thread for clean, sharp lines."),
    ("wax-6", "Upper Lip Threading", "Waxing", "waxing", 80, 59, "10 mins", "Quick Touch-up", 0, "Fast and gentle upper-lip threading for a smooth, makeup-friendly skin surface.")
]

def init_db():
    with app.app_context():
        db = get_db()
        db.executescript('''
            CREATE TABLE IF NOT EXISTS appointments (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                ref_number  TEXT    NOT NULL UNIQUE,
                name        TEXT    NOT NULL,
                phone       TEXT    NOT NULL,
                email       TEXT,
                category    TEXT    NOT NULL,
                service     TEXT    NOT NULL,
                price       TEXT    NOT NULL,
                duration    TEXT    NOT NULL,
                appt_date   TEXT    NOT NULL,
                appt_time   TEXT    NOT NULL,
                message     TEXT,
                status      TEXT    NOT NULL DEFAULT 'pending',
                admin_note  TEXT,
                created_at  TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS contacts (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT    NOT NULL,
                email       TEXT    NOT NULL,
                phone       TEXT,
                subject     TEXT    NOT NULL,
                message     TEXT    NOT NULL,
                status      TEXT    NOT NULL DEFAULT 'new', -- 'new', 'responded', 'archived'
                created_at  TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS services (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                slug_id         TEXT    NOT NULL UNIQUE,
                name            TEXT    NOT NULL,
                category        TEXT    NOT NULL,
                category_slug   TEXT    NOT NULL,
                original_price  INTEGER NOT NULL,
                offer_price     INTEGER NOT NULL,
                duration        TEXT    NOT NULL,
                badge           TEXT,
                is_popular      INTEGER NOT NULL DEFAULT 0,
                description     TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS reviews (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                author_name TEXT    NOT NULL,
                service     TEXT    NOT NULL,
                rating      INTEGER NOT NULL DEFAULT 5,
                comment     TEXT    NOT NULL,
                review_date TEXT    NOT NULL,
                is_sample   INTEGER NOT NULL DEFAULT 0,
                status      TEXT    NOT NULL DEFAULT 'pending',
                created_at  TEXT    NOT NULL
            );
        ''')
        db.commit()

        # Seed services table if empty
        row = db.execute("SELECT COUNT(*) FROM services").fetchone()
        if row and row[0] == 0:
            for s in INITIAL_SERVICES:
                db.execute('''
                    INSERT INTO services (slug_id, name, category, category_slug, original_price, offer_price, duration, badge, is_popular, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', s)
            db.commit()
            logger.info("Seeded initial 28 salon services into SQLite database.")

        # Seed reviews table if empty
        r_row = db.execute("SELECT COUNT(*) FROM reviews").fetchone()
        if r_row and r_row[0] == 0:
            sample_seed = [
                ("Emily R.", "Global Hair Colour & Blowout", 5, "Fantastic service and friendly staff! My balayage colour has never looked so naturally dimensional. The calm environment made my visit feel genuinely restful.", "14 October 2026", 1, "approved"),
                ("Michael T.", "Basic Haircut & Hair Spa", 5, "A cozy atmosphere and professional care. You never feel rushed here. The consultation was thorough, and the stylist listened carefully to my hair goals.", "22 October 2026", 1, "approved"),
                ("Sarah L.", "Gold Radiance Facial", 5, "The Gold Facial was deeply relaxing and my skin felt wonderfully soft and luminous. Cleanliness and hygiene were evident in every single step.", "28 October 2026", 1, "approved"),
                ("Ananya M.", "Bridal Makeup & Hairstyling", 5, "The bridal trial and final makeover were both extraordinary. The makeup stayed fresh and radiant throughout my reception. Highly recommended!", "02 November 2026", 1, "approved"),
                ("Pooja K.", "Gel Nail Polish & Manicure", 5, "Flawless nail art with mirror shine that lasted over three weeks without a single chip. Beautiful salon aesthetic and very gentle technicians.", "04 November 2026", 1, "approved"),
                ("Rohan V.", "Deep Cleansing Facial", 5, "Clean, hygienic, and very calming experience. The aesthetician gave great aftercare guidance for my sensitive skin.", "05 November 2026", 1, "approved")
            ]
            for author, svc, rating, comment, rdate, is_samp, stat in sample_seed:
                db.execute(
                    '''INSERT INTO reviews (author_name, service, rating, comment, review_date, is_sample, status, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                    (author, svc, rating, comment, rdate, is_samp, stat, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                )
            db.commit()

# Helper: format a service row with discount percentage and formatted currency
def format_service_row(row):
    d = dict(row)
    orig = d["original_price"]
    offer = d["offer_price"]
    discount = round(((orig - offer) / orig) * 100) if orig > 0 else 0
    d["price"] = f"₹{offer:,}"
    d["original_price_formatted"] = f"₹{orig:,}"
    d["offer_price_formatted"] = f"₹{offer:,}"
    d["savings_formatted"] = f"₹{orig - offer:,}"
    d["discount_percent"] = discount
    d["is_popular"] = bool(d.get("is_popular", 0))
    return d

def get_all_services():
    db = get_db()
    rows = db.execute("SELECT * FROM services ORDER BY id ASC").fetchall()
    return [format_service_row(r) for r in rows]

CATEGORIES = [
    {"name": "Hair", "slug": "hair"},
    {"name": "Skin", "slug": "skin"},
    {"name": "Makeup", "slug": "makeup"},
    {"name": "Nails", "slug": "nails"},
    {"name": "Waxing", "slug": "waxing"}
]

# ---------- Demonstration Combo Packages & Offers ----------
SAMPLE_OFFERS = [
    {
        "title": "New Client Glow Welcome",
        "tag": "First Visit",
        "discount": "20% OFF",
        "code": "WELCOMEGLOW",
        "description": "Experience the Glow & Grace difference with 20% off your first appointment across any hair or skin ritual.",
        "expires": "Valid ongoing for new guests",
        "recommended_for": "New Clients"
    },
    {
        "title": "Radiant Skin & Hair Duo",
        "tag": "Signature Package",
        "discount": "Save ₹450",
        "code": "GLOWDUO",
        "description": "Combine any Signature Haircut & Styling with our Luxury Botanical Facial for ultimate rejuvenation.",
        "expires": "Limited seasonal package",
        "recommended_for": "Hair & Skin Revitalisation"
    },
    {
        "title": "Midweek Sanctuary Special",
        "tag": "Tue – Thu Only",
        "discount": "15% OFF",
        "code": "MIDWEEKSIP",
        "description": "Enjoy peaceful relaxation with 15% off all spa manicure, pedicure, and facial rituals on Tuesdays through Thursdays.",
        "expires": "Tuesday - Thursday bookings",
        "recommended_for": "Weekday Pampering"
    },
    {
        "title": "Bridal Elegance Suite",
        "tag": "Bridal Party",
        "discount": "Complimentary Touch-up Kit",
        "code": "BRIDALGRACE",
        "description": "Book for a bridal party of 3 or more and receive complimentary styling touch-up kits and refreshment service.",
        "expires": "Advance booking required",
        "recommended_for": "Weddings & Bridal Groups"
    }
]

RAW_PACKAGES = [
    {
        "id": "pkg-1",
        "name": "Glow Facial Package",
        "badge": "Radiance Duo",
        "tag": "Skincare Special",
        "image": "gallery/facial-skincare-1.jpg",
        "included_services": ["Basic Cleanup", "Facial"],
        "category": "Skin",
        "duration": "90 mins",
        "original_price": 2000,
        "offer_price": 1599,
        "description": "Comprehensive skin detox combining gentle pore purification, steaming, extraction, and our signature botanical hydration facial."
    },
    {
        "id": "pkg-2",
        "name": "Hair Makeover Package",
        "badge": "Total Transformation",
        "tag": "Hair Artistry",
        "image": "gallery/haircut-styling-1.jpg",
        "included_services": ["Haircut", "Hair Spa", "Blow Dry"],
        "category": "Hair",
        "duration": "120 mins",
        "original_price": 2600,
        "offer_price": 2099,
        "description": "Precision layered haircut tailored to your features, followed by an intensive nourishing hair spa ritual and a bouncy salon blowout."
    },
    {
        "id": "pkg-3",
        "name": "Nail Care Package",
        "badge": "Hands & Feet Bliss",
        "tag": "Nail Couture",
        "image": "gallery/manicure-pedicure-1.jpg",
        "included_services": ["Manicure", "Pedicure"],
        "category": "Nails",
        "duration": "90 mins",
        "original_price": 1600,
        "offer_price": 1299,
        "description": "Deluxe dual ritual including soothing foot soak, exfoliation, cuticle care, deep hand/foot massage, and long-wear salon finish."
    },
    {
        "id": "pkg-4",
        "name": "Party Ready Package",
        "badge": "Evening Glamour",
        "tag": "Makeup & Hair",
        "image": "gallery/bridal-makeup-2.jpg",
        "included_services": ["Party Makeup", "Hairstyling"],
        "category": "Makeup",
        "duration": "120 mins",
        "original_price": 4000,
        "offer_price": 3299,
        "description": "Flawless HD event makeup customized to your outfit, paired with bespoke curling, beach waves, or elegant event updos."
    },
    {
        "id": "pkg-5",
        "name": "Bridal Beauty Package",
        "badge": "Couture Wedding",
        "tag": "Signature Bridal",
        "image": "gallery/bridal-makeup-1.jpg",
        "included_services": ["Bridal Makeup", "Hairstyling"],
        "category": "Bridal",
        "duration": "240 mins",
        "original_price": 18000,
        "offer_price": 15499,
        "description": "The quintessential royal bridal experience featuring high-definition makeup, luxury hair design, jewelry placement, and dupatta draping."
    },
    {
        "id": "pkg-6",
        "name": "Complete Beauty Package",
        "badge": "Head-to-Toe Luxury",
        "tag": "All-in-One Ritual",
        "image": "gallery/transformation-1.jpg",
        "included_services": ["Facial", "Hair Spa", "Manicure", "Pedicure"],
        "category": "All-in-One",
        "duration": "210 mins",
        "original_price": 5500,
        "offer_price": 4499,
        "description": "The ultimate head-to-toe salon indulgence: rejuvenating facial, deeply restorative scalp spa, soothing spa manicure, and relaxing pedicure."
    }
]

def format_package(pkg):
    orig = pkg["original_price"]
    offer = pkg["offer_price"]
    discount = round(((orig - offer) / orig) * 100) if orig > 0 else 0
    return {
        **pkg,
        "price": f"₹{offer:,}",
        "original_price_formatted": f"₹{orig:,}",
        "offer_price_formatted": f"₹{offer:,}",
        "savings_formatted": f"₹{orig - offer:,}",
        "discount_percent": discount
    }

SAMPLE_PACKAGES = [format_package(p) for p in RAW_PACKAGES]
PACKAGE_LOOKUP = {p["name"]: p for p in SAMPLE_PACKAGES}

# ---------- Beauty Transformations Data ----------
TRANSFORMATION_CATEGORIES = [
    {"name": "All", "slug": "all"},
    {"name": "Haircuts", "slug": "haircuts"},
    {"name": "Hair Colour", "slug": "hair-colour"},
    {"name": "Hairstyling", "slug": "hairstyling"},
    {"name": "Skincare", "slug": "skincare"},
    {"name": "Makeup", "slug": "makeup"},
    {"name": "Nail Art", "slug": "nail-art"}
]

SAMPLE_TRANSFORMATIONS = [
    {
        "id": "trans-1",
        "title": "Layered Contour & Dimensional Lob",
        "category": "Haircuts",
        "category_slug": "haircuts",
        "before_img": "gallery/transformation-2.jpg",
        "after_img": "gallery/haircut-styling-1.jpg",
        "before_label": "Before: Uneven Ends & Heavy Texture",
        "after_label": "After: Face-Framing Feathered Cut & Volume",
        "service_name": "Basic Haircut",
        "description": "Graduated soft layers designed to frame cheekbones, remove dry weight, and introduce bouncy natural movement.",
        "stylist": "Senior Hair Stylist"
    },
    {
        "id": "trans-2",
        "title": "Warm Honey Balayage & Glaze",
        "category": "Hair Colour",
        "category_slug": "hair-colour",
        "before_img": "gallery/haircut-styling-2.jpg",
        "after_img": "gallery/hair-colour-1.jpg",
        "before_label": "Before: Flat Monotone Brunette",
        "after_label": "After: Sun-Kissed Multi-Tone Honey Balayage",
        "service_name": "Global Hair Colour",
        "description": "Hand-painted foil balayage with botanical gloss treatment for rich dimension, seamless root blend, and reflective shine.",
        "stylist": "Master Colorist"
    },
    {
        "id": "trans-3",
        "title": "Hollywood Glamour Waves & Texture",
        "category": "Hairstyling",
        "category_slug": "hairstyling",
        "before_img": "gallery/haircut-styling-3.jpg",
        "after_img": "gallery/transformation-3.jpg",
        "before_label": "Before: Natural Straight Texture",
        "after_label": "After: Sculpted Thermal Red-Carpet Waves",
        "service_name": "Hair Styling",
        "description": "Thermal wave sculpture setting with high-hold protective serum for sleek, glossy red-carpet party glamour.",
        "stylist": "Lead Hair Stylist"
    },
    {
        "id": "trans-4",
        "title": "Gold Radiance Rejuvenation & Pore Clarifying",
        "category": "Skincare",
        "category_slug": "skincare",
        "before_img": "gallery/facial-skincare-2.jpg",
        "after_img": "gallery/facial-skincare-1.jpg",
        "before_label": "Before: Dull Complexion & Sun Congestion",
        "after_label": "After: Plump, Clarified & Luminous Glow",
        "service_name": "Gold Facial",
        "description": "Deep enzymatic purification followed by gold-leaf essence infusion, hyaluronic acid seal, and soothing lymphatic massage.",
        "stylist": "Lead Aesthetician"
    },
    {
        "id": "trans-5",
        "title": "Couture Bridal Glow & Soft Smokey Contour",
        "category": "Makeup",
        "category_slug": "makeup",
        "before_img": "gallery/bridal-makeup-3.jpg",
        "after_img": "gallery/bridal-makeup-1.jpg",
        "before_label": "Before: Fresh Bare Skin Prepped",
        "after_label": "After: Royal HD Airbrush Bridal Glamour",
        "service_name": "Bridal Makeup",
        "description": "Long-wearing HD base with sculpted cheek contours, soft bronze eye artistry, lash extensions, and defined rosy lip tone.",
        "stylist": "Master Bridal Artist"
    },
    {
        "id": "trans-6",
        "title": "Champagne Foil & Velvet Gel Couture",
        "category": "Nail Art",
        "category_slug": "nail-art",
        "before_img": "gallery/manicure-pedicure-2.jpg",
        "after_img": "gallery/nail-art-1.jpg",
        "before_label": "Before: Bare Ungroomed Nails",
        "after_label": "After: Almond Sculpted Nails with Gold Foil",
        "service_name": "Nail Art",
        "description": "Precision cuticle cleanup, almond nail shaping, milky nude UV gel application, and handcrafted 24k champagne foil leaf accents.",
        "stylist": "Nail Art Artisan"
    }
]

# ---------- Authentication Decorator ----------
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Please log in with administrator credentials to access this dashboard.', 'warning')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

# ---------- Validation Helpers ----------
def validate_phone(phone):
    """Accept Indian mobile numbers: 10 digits, optionally starting with +91 or 0."""
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)
    patterns = [
        r'^\+91[6-9]\d{9}$',
        r'^91[6-9]\d{9}$',
        r'^0?[6-9]\d{9}$',
    ]
    return any(re.match(p, cleaned) for p in patterns)

def validate_email(email):
    if not email:
        return True
    return bool(re.match(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$', email))

def validate_date(date_str):
    try:
        appt_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        return appt_date >= date.today()
    except (ValueError, TypeError):
        return False

def validate_time(time_str):
    try:
        t = datetime.strptime(time_str, '%H:%M').time()
        from datetime import time as dtime
        return dtime(9, 0) <= t <= dtime(20, 0)
    except (ValueError, TypeError):
        return False

# ---------- Status Display Metadata ----------
STATUS_META = {
    'pending':   {'label': 'Pending Review',    'color': '#c5a059', 'bg': '#fdf6e9', 'icon': '⏳'},
    'confirmed': {'label': 'Confirmed',          'color': '#5a8f7b', 'bg': '#eef5f2', 'icon': '✅'},
    'completed': {'label': 'Completed',          'color': '#7b8f78', 'bg': '#f3f6f2', 'icon': '🌟'},
    'cancelled': {'label': 'Cancelled',          'color': '#a45860', 'bg': '#fdf0f1', 'icon': '❌'},
}

# ---------- AJAX: Dynamic Services by Category ----------
@app.route('/api/services/<category>')
def api_services_by_category(category):
    services = get_all_services()
    filtered = [s for s in services if s["category"].lower() == category.lower()]
    return jsonify(filtered)

# ---------- Public Routes ----------
@app.route('/')
def index():
    db = get_db()
    approved_reviews = db.execute(
        "SELECT * FROM reviews WHERE status='approved' ORDER BY id DESC LIMIT 6"
    ).fetchall()
    services = get_all_services()
    popular = [s for s in services if s.get("is_popular")]
    offers_list = [s for s in services if s.get("discount_percent", 0) >= 20]

    return render_template(
        'index.html',
        services=services,
        popular_services=popular[:6],
        special_offers=offers_list[:3],
        offers=SAMPLE_OFFERS,
        reviews=approved_reviews,
        transformations=SAMPLE_TRANSFORMATIONS[:4]
    )

@app.route('/services')
def services():
    all_s = get_all_services()
    popular = [s for s in all_s if s.get("is_popular")]
    special = [s for s in all_s if s.get("discount_percent", 0) >= 20]
    return render_template(
        'services.html',
        services=all_s,
        categories=CATEGORIES,
        popular_services=popular,
        special_offers=special
    )

@app.route('/offers')
def offers():
    return render_template('offers.html', offers=SAMPLE_OFFERS, packages=SAMPLE_PACKAGES)

@app.route('/transformations')
def transformations():
    return render_template(
        'transformations.html',
        transformations=SAMPLE_TRANSFORMATIONS,
        categories=TRANSFORMATION_CATEGORIES
    )

@app.route('/reviews', methods=['GET', 'POST'])
def reviews():
    db = get_db()
    errors = {}
    form_data = {}
    all_services = get_all_services()

    if request.method == 'POST':
        author_name = request.form.get('author_name', '').strip()
        service     = request.form.get('service', '').strip()
        rating_str  = request.form.get('rating', '5').strip()
        comment     = request.form.get('comment', '').strip()

        form_data = {
            'author_name': author_name,
            'service': service,
            'rating': rating_str,
            'comment': comment
        }

        # Parameterized form validation
        if not author_name or len(author_name) < 2:
            errors['author_name'] = 'Please enter your name or initials (at least 2 characters).'
        if not service:
            errors['service'] = 'Please specify the service you received.'
        try:
            rating = int(rating_str)
            if not (1 <= rating <= 5):
                errors['rating'] = 'Rating must be between 1 and 5 stars.'
        except ValueError:
            rating = 5
            errors['rating'] = 'Invalid rating value.'
        if not comment or len(comment) < 10:
            errors['comment'] = 'Please write a brief comment about your experience (minimum 10 characters).'

        if not errors:
            today_str = datetime.now().strftime('%d %B %Y')
            db.execute(
                '''INSERT INTO reviews
                   (author_name, service, rating, comment, review_date, is_sample, status, created_at)
                   VALUES (?, ?, ?, ?, ?, 0, 'pending', ?)''',
                (author_name, service, rating, comment, today_str, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            )
            db.commit()
            logger.info(f"New customer review submitted by '{author_name}' for service '{service}'. Status: pending moderation.")
            flash('Thank you for your feedback! Your review has been submitted for moderation and will appear publicly once verified by our salon concierge.', 'success')
            return redirect(url_for('reviews'))

    approved_reviews = db.execute(
        "SELECT * FROM reviews WHERE status='approved' ORDER BY id DESC"
    ).fetchall()

    return render_template(
        'reviews.html',
        reviews=approved_reviews,
        services=all_services,
        errors=errors,
        form_data=form_data
    )

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    errors = {}
    form_data = {}

    if request.method == 'POST':
        name    = request.form.get('name', '').strip()
        email   = request.form.get('email', '').strip()
        phone   = request.form.get('phone', '').strip()
        subject = request.form.get('subject', 'General Inquiry').strip()
        message = request.form.get('message', '').strip()

        form_data = {
            'name': name,
            'email': email,
            'phone': phone,
            'subject': subject,
            'message': message
        }

        # Validation
        if not name or len(name) < 2:
            errors['name'] = 'Please enter your full name.'
        if not email or not validate_email(email):
            errors['email'] = 'Please enter a valid email address.'
        if phone and not validate_phone(phone):
            errors['phone'] = 'Please enter a valid 10-digit mobile number, or leave blank.'
        if not message or len(message) < 5:
            errors['message'] = 'Please enter a message (at least 5 characters).'

        if errors:
            flash('Please correct the highlighted fields before sending your inquiry.', 'warning')
            return render_template('contact.html', errors=errors, form_data=form_data)

        # Parameterized query to store contact enquiry in SQLite
        db = get_db()
        db.execute(
            '''INSERT INTO contacts (name, email, phone, subject, message, status, created_at)
               VALUES (?, ?, ?, ?, ?, 'new', ?)''',
            (name, email, phone or None, subject, message, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        )
        db.commit()
        logger.info(f"New contact inquiry received from '{name}' ({email}) regarding '{subject}'.")

        flash(f'Thank you, {name}! Your message has been received by our salon concierge. We will respond to your inquiry via phone or email within one business day.', 'success')
        return redirect(url_for('success'))

    return render_template('contact.html', errors={}, form_data={})

@app.route('/success')
def success():
    return render_template('success.html')

@app.route('/appointment', methods=['GET', 'POST'])
def appointment():
    selected_service = request.args.get('service', '')
    errors = {}
    all_services = get_all_services()

    if request.method == 'POST':
        name      = request.form.get('name', '').strip()
        phone     = request.form.get('phone', '').strip()
        email     = request.form.get('email', '').strip()
        category  = request.form.get('category', '').strip()
        service   = request.form.get('service', '').strip()
        appt_date = request.form.get('date', '').strip()
        appt_time = request.form.get('time', '').strip()
        message   = request.form.get('message', '').strip()

        # Server-side validation
        if not name or len(name) < 2:
            errors['name'] = 'Please enter your full name (at least 2 characters).'
        if not phone:
            errors['phone'] = 'Mobile number is required.'
        elif not validate_phone(phone):
            errors['phone'] = 'Please enter a valid Indian mobile number (10 digits).'
        if email and not validate_email(email):
            errors['email'] = 'Please enter a valid email address.'
        if not category:
            errors['category'] = 'Please select a service category.'
        if not service:
            errors['service'] = 'Please select a specific service.'
        if not appt_date:
            errors['date'] = 'Please choose an appointment date.'
        elif not validate_date(appt_date):
            errors['date'] = 'Please select a future date.'
        if not appt_time:
            errors['time'] = 'Please choose a preferred time.'
        elif not validate_time(appt_time):
            errors['time'] = 'Please choose a time between 9:00 AM and 8:00 PM.'

        if errors:
            form_data = {
                'name': name, 'phone': phone, 'email': email,
                'category': category, 'service': service,
                'date': appt_date, 'time': appt_time, 'message': message
            }
            return render_template(
                'appointment.html',
                services=all_services,
                categories=CATEGORIES,
                selected_service=selected_service,
                errors=errors,
                form_data=form_data
            )

        # Lookup price & duration from DB or Package dict
        service_lookup = {s["name"]: s for s in all_services}
        svc_data = service_lookup.get(service) or PACKAGE_LOOKUP.get(service, {})
        price    = svc_data.get('price', '—')
        duration = svc_data.get('duration', '—')

        ref = generate_ref()

        # Parameterized query to store appointment in SQLite
        db = get_db()
        db.execute(
            '''INSERT INTO appointments
               (ref_number, name, phone, email, category, service,
                price, duration, appt_date, appt_time, message, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)''',
            (ref, name, phone, email or None, category, service,
             price, duration, appt_date, appt_time,
             message or None, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        )
        db.commit()
        logger.info(f"New appointment request [{ref}] booked by '{name}' for '{service}' on {appt_date} at {appt_time}.")

        try:
            display_date = datetime.strptime(appt_date, '%Y-%m-%d').strftime('%A, %d %B %Y')
        except ValueError:
            display_date = appt_date

        try:
            display_time = datetime.strptime(appt_time, '%H:%M').strftime('%I:%M %p')
        except ValueError:
            display_time = appt_time

        return redirect(url_for('booking_confirmation',
                                ref=ref,
                                name=name,
                                service=service,
                                category=category,
                                price=price,
                                duration=duration,
                                display_date=display_date,
                                display_time=display_time))

    return render_template(
        'appointment.html',
        services=all_services,
        categories=CATEGORIES,
        selected_service=selected_service,
        errors={},
        form_data={}
    )

@app.route('/booking-confirmation')
def booking_confirmation():
    ref = request.args.get('ref', '')
    if not ref:
        return redirect(url_for('appointment'))

    return render_template('booking_confirmation.html',
        ref=ref,
        name=request.args.get('name', 'Valued Guest'),
        service=request.args.get('service', ''),
        category=request.args.get('category', ''),
        price=request.args.get('price', ''),
        duration=request.args.get('duration', ''),
        display_date=request.args.get('display_date', ''),
        display_time=request.args.get('display_time', ''),
        status_meta=STATUS_META['pending']
    )

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/gallery')
def gallery():
    return render_template('gallery.html')

# ---------- Admin Portal & Management Routes ----------
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard'))

    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        # Constant-time comparison for authentication security
        if secrets.compare_digest(username, ADMIN_USERNAME) and secrets.compare_digest(password, ADMIN_PASSWORD):
            session['admin_logged_in'] = True
            session.permanent = True
            logger.info(f"Successful administrator login from IP: {request.remote_addr}")
            flash('Welcome back! You are now authenticated to the administration panel.', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            logger.warning(f"Failed administrator login attempt with username '{username}' from IP: {request.remote_addr}")
            error = 'Invalid administrative username or password. Please try again.'

    return render_template('admin_login.html', error=error)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('You have been logged out of the admin panel.', 'success')
    return redirect(url_for('admin_login'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    db = get_db()
    search   = request.args.get('q', '').strip()
    status   = request.args.get('status', '').strip()
    page     = max(1, int(request.args.get('page', 1)))
    per_page = 20

    query  = "SELECT * FROM appointments WHERE 1=1"
    params = []

    if search:
        query  += " AND (name LIKE ? OR phone LIKE ? OR ref_number LIKE ? OR service LIKE ?)"
        like    = f'%{search}%'
        params += [like, like, like, like]

    if status and status in STATUS_META:
        query  += " AND status = ?"
        params.append(status)

    count_row = db.execute(f"SELECT COUNT(*) FROM ({query})", params).fetchone()
    total = count_row[0] if count_row else 0
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = min(page, total_pages)

    query  += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params += [per_page, (page - 1) * per_page]

    appointments = db.execute(query, params).fetchall()

    counts = {}
    for s in STATUS_META:
        row = db.execute("SELECT COUNT(*) FROM appointments WHERE status=?", (s,)).fetchone()
        counts[s] = row[0] if row else 0
    counts['total'] = total

    pending_reviews_count = db.execute("SELECT COUNT(*) FROM reviews WHERE status='pending'").fetchone()[0]
    new_contacts_count    = db.execute("SELECT COUNT(*) FROM contacts WHERE status='new'").fetchone()[0]

    return render_template('admin.html',
        appointments=appointments,
        status_meta=STATUS_META,
        counts=counts,
        search=search,
        status_filter=status,
        page=page,
        total_pages=total_pages,
        total=total,
        pending_reviews_count=pending_reviews_count,
        new_contacts_count=new_contacts_count
    )

@app.route('/admin/appointment/<int:appt_id>', methods=['GET', 'POST'])
@admin_required
def admin_appointment_detail(appt_id):
    db = get_db()
    appt = db.execute("SELECT * FROM appointments WHERE id=?", (appt_id,)).fetchone()
    if not appt:
        flash('Appointment request was not found.', 'warning')
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        new_status = request.form.get('status', '').strip()
        admin_note = request.form.get('admin_note', '').strip()

        if new_status not in STATUS_META:
            flash('Invalid status selected.', 'warning')
        else:
            db.execute(
                "UPDATE appointments SET status=?, admin_note=? WHERE id=?",
                (new_status, admin_note or None, appt_id)
            )
            db.commit()
            logger.info(f"Appointment [{appt['ref_number']}] updated to '{new_status}' by admin.")
            flash(f'Appointment [{appt["ref_number"]}] updated to {STATUS_META[new_status]["label"]}.', 'success')
            return redirect(url_for('admin_appointment_detail', appt_id=appt_id))

    appt = db.execute("SELECT * FROM appointments WHERE id=?", (appt_id,)).fetchone()
    return render_template('admin_detail.html',
        appt=appt,
        status_meta=STATUS_META,
        statuses=list(STATUS_META.keys())
    )

@app.route('/admin/appointment/<int:appt_id>/delete', methods=['POST'])
@admin_required
def admin_delete_appointment(appt_id):
    db = get_db()
    appt = db.execute("SELECT ref_number FROM appointments WHERE id=?", (appt_id,)).fetchone()
    if appt:
        db.execute("DELETE FROM appointments WHERE id=?", (appt_id,))
        db.commit()
        logger.info(f"Appointment [{appt['ref_number']}] permanently deleted by admin.")
        flash(f'Appointment [{appt["ref_number"]}] has been permanently removed.', 'success')
    return redirect(url_for('admin_dashboard'))

# ---------- Admin: Contact Enquiries Management ----------
@app.route('/admin/contacts')
@admin_required
def admin_contacts():
    db = get_db()
    status_filter = request.args.get('status', '').strip()

    query = "SELECT * FROM contacts"
    params = []
    if status_filter:
        query += " WHERE status = ?"
        params.append(status_filter)
    query += " ORDER BY id DESC"

    all_contacts = db.execute(query, params).fetchall()
    counts = {
        'all': db.execute("SELECT COUNT(*) FROM contacts").fetchone()[0],
        'new': db.execute("SELECT COUNT(*) FROM contacts WHERE status='new'").fetchone()[0],
        'responded': db.execute("SELECT COUNT(*) FROM contacts WHERE status='responded'").fetchone()[0],
        'archived': db.execute("SELECT COUNT(*) FROM contacts WHERE status='archived'").fetchone()[0],
    }

    return render_template(
        'admin_contacts.html',
        contacts=all_contacts,
        counts=counts,
        current_status=status_filter
    )

@app.route('/admin/contacts/<int:contact_id>/status', methods=['POST'])
@admin_required
def admin_update_contact_status(contact_id):
    db = get_db()
    new_status = request.form.get('status', '').strip()
    if new_status in ('new', 'responded', 'archived'):
        db.execute("UPDATE contacts SET status=? WHERE id=?", (new_status, contact_id))
        db.commit()
        flash(f'Contact inquiry #{contact_id} marked as {new_status}.', 'success')
    return redirect(url_for('admin_contacts'))

@app.route('/admin/contacts/<int:contact_id>/delete', methods=['POST'])
@admin_required
def admin_delete_contact(contact_id):
    db = get_db()
    db.execute("DELETE FROM contacts WHERE id=?", (contact_id,))
    db.commit()
    flash(f'Contact inquiry #{contact_id} has been permanently deleted.', 'success')
    return redirect(url_for('admin_contacts'))

# ---------- Admin: Service Catalogue Management ----------
@app.route('/admin/services')
@admin_required
def admin_services():
    services = get_all_services()
    return render_template('admin_services.html', services=services, categories=CATEGORIES)

@app.route('/admin/services/<int:service_id>/update', methods=['POST'])
@admin_required
def admin_update_service(service_id):
    db = get_db()
    try:
        orig = int(request.form.get('original_price', 0))
        offer = int(request.form.get('offer_price', 0))
        duration = request.form.get('duration', '').strip()
        badge = request.form.get('badge', '').strip()
        is_pop = 1 if request.form.get('is_popular') else 0

        if orig <= 0 or offer <= 0:
            flash('Prices must be positive integers.', 'warning')
            return redirect(url_for('admin_services'))

        db.execute('''
            UPDATE services 
            SET original_price=?, offer_price=?, duration=?, badge=?, is_popular=?
            WHERE id=?
        ''', (orig, offer, duration, badge or None, is_pop, service_id))
        db.commit()

        svc = db.execute("SELECT name FROM services WHERE id=?", (service_id,)).fetchone()
        svc_name = svc['name'] if svc else f"#{service_id}"
        logger.info(f"Service '{svc_name}' pricing updated: Original ₹{orig}, Offer ₹{offer}.")
        flash(f"Service '{svc_name}' pricing and details updated successfully.", 'success')
    except (ValueError, TypeError) as e:
        logger.error(f"Error updating service: {e}")
        flash('Invalid price format submitted.', 'warning')

    return redirect(url_for('admin_services'))

# ---------- Admin: Customer Reviews Moderation ----------
@app.route('/admin/reviews')
@admin_required
def admin_reviews():
    db = get_db()
    filter_status = request.args.get('status', '').strip()
    
    query = "SELECT * FROM reviews"
    params = []
    if filter_status:
        query += " WHERE status = ?"
        params.append(filter_status)
    query += " ORDER BY id DESC"
    
    all_reviews = db.execute(query, params).fetchall()
    
    counts = {
        'all': db.execute("SELECT COUNT(*) FROM reviews").fetchone()[0],
        'pending': db.execute("SELECT COUNT(*) FROM reviews WHERE status='pending'").fetchone()[0],
        'approved': db.execute("SELECT COUNT(*) FROM reviews WHERE status='approved'").fetchone()[0],
        'rejected': db.execute("SELECT COUNT(*) FROM reviews WHERE status='rejected'").fetchone()[0],
    }
    
    return render_template(
        'admin_reviews.html',
        reviews=all_reviews,
        counts=counts,
        current_status=filter_status
    )

@app.route('/admin/reviews/<int:review_id>/update', methods=['POST'])
@admin_required
def admin_update_review(review_id):
    db = get_db()
    new_status = request.form.get('status', '').strip()
    if new_status in ['approved', 'rejected', 'pending']:
        db.execute("UPDATE reviews SET status=? WHERE id=?", (new_status, review_id))
        db.commit()
        flash(f'Review #{review_id} has been marked as {new_status}.', 'success')
    return redirect(url_for('admin_reviews'))

@app.route('/admin/reviews/<int:review_id>/delete', methods=['POST'])
@admin_required
def admin_delete_review(review_id):
    db = get_db()
    db.execute("DELETE FROM reviews WHERE id=?", (review_id,))
    db.commit()
    flash(f'Review #{review_id} has been permanently deleted.', 'success')
    return redirect(url_for('admin_reviews'))

# ---------- Global HTTP Error Handlers ----------
@app.errorhandler(404)
def page_not_found(e):
    logger.info(f"404 Not Found: {request.path}")
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    logger.error(f"500 Internal Server Error encountered at {request.path}: {e}")
    return render_template('500.html'), 500

# ---------- Initialize DB Schema ----------
init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    logger.info(f"Starting Glow & Grace Salon application on http://{host}:{port} (Debug: {FLASK_DEBUG})")
    app.run(debug=FLASK_DEBUG, host=host, port=port)

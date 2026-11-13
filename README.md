# Glow & Grace Salon — Luxury Beauty & Spa

A modern, elegant salon website built with **Flask**, **Jinja2**, and vanilla **HTML5 / CSS3 / JavaScript**.

## Features
- **Sophisticated Aesthetic:** Tailored luxury color palette with soft blush pink, warm beige, ivory white, muted sage green, champagne gold accents, and dark charcoal typography.
- **Editorial Typography:** Cormorant Garamond headings paired with Plus Jakarta Sans body text.
- **Responsive Navigation:** Complete navigation bar with Home, About Us, Services, Gallery, Offers, Appointment, and Contact links, plus an accessible mobile drawer menu.
- **Professional Service Catalogue:** 28 centralized services priced in Indian Rupees (₹) across Hair, Skin, Makeup, Nails, and Waxing/Threading.
- **Transparent Pricing & Verified Discounts:** Exact percentage discounts, strikethrough original prices, highlighted offer prices, and estimated service durations.
- **Live Search & Category Filtering:** Instant search bar with clear button and category pills (All, Hair, Skin, Makeup, Nails, Waxing & Threading).
- **Popular Services & Special Offers Sections:** Spotlights guest favorites and top-discounted packages.
- **Curated Offers & Packages:** Dedicated `/offers` route with promotional codes, packages, and VIP club enrollment.
- **Interactive Visual Gallery:** Filterable portfolio (Hair, Skin, Nails, Bridal, Ambience) with full-screen lightbox modal.
- **Bespoke Appointment Booking & SQLite System:** Multi-step booking request form with category-to-service cascading dropdowns, live price & duration display, past date prevention, mobile validation, unique reference numbers (`GG-XXXXXX`), and transparent requested-slot labeling.
- **Customer Reviews & Moderation System:** Star rating display, reviewer initials/name, service enjoyed, review date, transparent sample badges, public submission form with validation, and an authenticated admin moderation workflow (`/reviews` & `/admin/reviews`).
- **Beauty Transformations (Before & After):** Interactive transformation showcase across 6 categories (Haircuts, Hair Colour, Hairstyling, Skincare, Makeup, Nail Art) with side-by-side comparison cards, category filters, click-to-enlarge lightbox, and honest illustrative demonstration notices (`/transformations`).
- **Curated Offers & Packages:** Dedicated `/offers` route showcasing 6 demonstration combo packages (Glow Facial, Hair Makeover, Nail Care, Party Ready, Bridal Beauty, Complete Beauty), seasonal promotion banners, promo codes, and clear terms & conditions.
- **Contact & WhatsApp Concierge:** Studio address, phone, email, opening/closing hours, weekly working days, social media links, Google Maps embed placeholder, sitewide floating WhatsApp button, and pre-filled WhatsApp enquiry buttons across services and packages (`/contact`).
- **Protected Admin Panel:** Authenticated dashboard (`/admin/login`, `/admin`, `/admin/appointment/<id>`, `/admin/reviews`) to review, search, filter, update appointment statuses, add staff notes, or moderate reviews.
- **Detailed About Us Page:** 8 structured sections covering Our Story, About Our Salon, Mission, Vision, Why Choose Us (8 cards), Our Expertise, Customer Experience, and Call to Action.
- **Contact & Location:** Studio details, opening hours, interactive form, and clearly marked editable business information.
- **Consistent Layout & Professional Footer:** Brand overview, social media channels, signature services, opening hours, and legal links across all pages.

## Project Structure
```
glow-and-grace-salon/
├── app.py                     # Flask application, routing & centralized catalogue data
├── requirements.txt           # Python dependencies (Flask)
├── README.md                  # Project documentation
├── salon.db                   # SQLite database storing appointment requests
├── static/
│   ├── css/
│   │   ├── style.css          # Premium design system, catalogue, booking & responsive styling
│   │   └── admin.css          # Dedicated styling for admin management dashboard
│   ├── js/main.js             # Mobile nav, dynamic cascading dropdowns, live preview & lightbox
│   └── images/                # Local illustrative photography & brand assets
└── templates/
    ├── base.html              # Shared layout, header, footer & flash alerts
    ├── index.html             # Home page with luxury hero & popular rituals
    ├── about.html             # Detailed 8-section salon introduction
    ├── services.html          # Full catalogue with search, filters, popular & offers
    ├── gallery.html           # Filterable gallery & lightbox modal
    ├── offers.html            # Seasonal packages & promo codes
    ├── appointment.html       # Dynamic booking form with price & duration preview
    ├── booking_confirmation.html # Booking request confirmation with reference number
    ├── admin_login.html       # Protected admin authentication portal
    ├── admin.html             # Admin appointment requests dashboard & filters
    ├── admin_detail.html      # Individual appointment review & status editor
    ├── contact.html           # Inquiries, studio address & hours
    └── success.html           # Elegant general contact submission confirmation
```

## Setup & Run

```bash
# Activate the virtual environment
.\.venv\Scripts\activate      # Windows PowerShell

# Install dependencies (Flask)
pip install -r requirements.txt

# Start the Flask development server
python app.py
```

Open your browser and navigate to `http://127.0.0.1:5000/`.

## Business Information & Customization
All business details and service prices are centralized and easily editable in:
- `app.py` (`RAW_SERVICES` for all services, prices, durations, and categories; `SAMPLE_OFFERS` for seasonal deals)
- `templates/base.html` (Footer & header announcement bar)
- `templates/contact.html` (Studio sidebar)
- `templates/appointment.html` (Hours sidebar)

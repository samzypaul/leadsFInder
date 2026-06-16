"""Deterministic demo fixtures.

These let the entire pipeline run end-to-end with no network access, no API keys, and no
ToS exposure. Each entry is keyed by a normalized Instagram username or business-name slug.
Realistic Tanzanian SMB examples; none have an owned website (so they become qualified leads),
except `kilizotech` which intentionally has one (to exercise the "Website Found" path).
"""
from __future__ import annotations

INSTAGRAM_FIXTURES: dict[str, dict] = {
    "serengetidreamsafaris": {
        "business_name": "Serengeti Dreams Safaris",
        "username": "serengetidreamsafaris",
        "bio": "🦁 Tailor-made safaris & Kilimanjaro treks | Airport transfers | "
               "📍 Arusha | 📞 +255 754 123 456 | DM to book",
        "category": "Tour Agency",
        "phone": "+255754123456",
        "whatsapp": "+255754123456",
        "email": "bookings@serengetidreams.co.tz",
        "location": "Arusha, Tanzania",
        "external_links": ["https://wa.me/255754123456"],
        "followers": 18400,
        "posts_count": 642,
        "facebook_url": "https://facebook.com/serengetidreamsafaris",
    },
    "mamandogokitchen": {
        "business_name": "Mama Ndogo Kitchen",
        "username": "mamandogokitchen",
        "bio": "Authentic Tanzanian home food 🍛 | Catering & daily lunch | "
               "Mwenge, Dar es Salaam | Order: 0712 888 999",
        "category": "Restaurant",
        "phone": "+255712888999",
        "whatsapp": "+255712888999",
        "email": None,
        "location": "Dar es Salaam, Tanzania",
        "external_links": [],
        "followers": 5200,
        "posts_count": 311,
        "facebook_url": "https://facebook.com/mamandogokitchen",
    },
    "zanzibarpearlproperties": {
        "business_name": "Zanzibar Pearl Properties",
        "username": "zanzibarpearlproperties",
        "bio": "🏝️ Beachfront villas & plots for sale | Stone Town & Nungwi | "
               "info@ via DM | ☎ +255 778 222 333",
        "category": "Real Estate",
        "phone": "+255778222333",
        "whatsapp": "+255778222333",
        "email": "sales@zanzibarpearl.co.tz",
        "location": "Zanzibar, Tanzania",
        "external_links": ["https://linktr.ee/zanzibarpearl"],
        "followers": 9800,
        "posts_count": 187,
        "facebook_url": None,
    },
    "glamoursalondar": {
        "business_name": "Glamour Salon & Spa",
        "username": "glamoursalondar",
        "bio": "💅 Hair, nails & spa | Masaki, Dar es Salaam | Book: 0683 444 555",
        "category": "Beauty Salon",
        "phone": "+255683444555",
        "whatsapp": "+255683444555",
        "email": None,
        "location": "Dar es Salaam, Tanzania",
        "external_links": [],
        "followers": 12600,
        "posts_count": 488,
        "facebook_url": None,
    },
    "kilimanjaroviewlodge": {
        "business_name": "Kilimanjaro View Lodge",
        "username": "kilimanjaroviewlodge",
        "bio": "🏔️ Boutique lodge in Moshi | Mountain views | reservations@ via DM | +255 765 777 888",
        "category": "Hotel",
        "phone": "+255765777888",
        "whatsapp": "+255765777888",
        "email": "reservations@kiliviewlodge.co.tz",
        "location": "Moshi, Tanzania",
        "external_links": ["https://wa.me/255765777888"],
        "followers": 23100,
        "posts_count": 754,
        "facebook_url": "https://facebook.com/kilimanjaroviewlodge",
    },
    "mwanzaautogarage": {
        "business_name": "Mwanza Auto Garage",
        "username": "mwanzaautogarage",
        "bio": "🔧 Car service & spare parts | Nyamagana, Mwanza | Call 0754 909 090",
        "category": "Automotive",
        "phone": "+255754909090",
        "whatsapp": None,
        "email": None,
        "location": "Mwanza, Tanzania",
        "external_links": [],
        "followers": 3400,
        "posts_count": 142,
        "facebook_url": None,
    },
    "kilizotech": {  # has a real website -> exercises the "Website Found" path
        "business_name": "Kilizo Tech Solutions",
        "username": "kilizotech",
        "bio": "Software & IT services in Dodoma 💻 | www.kilizotech.co.tz",
        "category": "Information Technology",
        "phone": "+255767000111",
        "whatsapp": None,
        "email": "hello@kilizotech.co.tz",
        "location": "Dodoma, Tanzania",
        "external_links": ["https://www.kilizotech.co.tz"],
        "followers": 2100,
        "posts_count": 94,
        "facebook_url": "https://facebook.com/kilizotech",
    },
}

FACEBOOK_FIXTURES: dict[str, dict] = {
    "serengetidreamsafaris": {
        "business_name": "Serengeti Dreams Safaris",
        "about": "Licensed tour operator since 2014. Safaris, Kilimanjaro & Zanzibar packages.",
        "category": "Tour Agency",
        "phone": "+255754123456",
        "email": "bookings@serengetidreams.co.tz",
        "website": None,  # no website on FB either
        "location": "Arusha, Tanzania",
    },
    "mamandogokitchen": {
        "business_name": "Mama Ndogo Kitchen",
        "about": "Home-style Tanzanian catering for events and daily office lunch delivery.",
        "category": "Caterer",
        "phone": "+255712888999",
        "email": None,
        "website": None,
        "location": "Dar es Salaam, Tanzania",
    },
    "kilizotech": {
        "business_name": "Kilizo Tech Solutions",
        "about": "Custom software, web & IT support.",
        "category": "IT Company",
        "phone": "+255767000111",
        "email": "hello@kilizotech.co.tz",
        "website": "https://www.kilizotech.co.tz",
        "location": "Dodoma, Tanzania",
    },
}

# Keyed by lowercase business name.
GOOGLE_BUSINESS_FIXTURES: dict[str, dict] = {
    "serengeti dreams safaris": {
        "business_name": "Serengeti Dreams Safaris",
        "address": "Plot 14, Sokoine Rd, Arusha",
        "phone": "+255754123456",
        "category": "Safari tour operator",
        "reviews_count": 213,
        "rating": 4.8,
        "hours": "Mon–Sat 08:00–18:00",
        "website": None,
        "city": "Arusha",
        "region": "Arusha",
    },
    "mama ndogo kitchen": {
        "business_name": "Mama Ndogo Kitchen",
        "address": "Mwenge, Kinondoni, Dar es Salaam",
        "phone": "+255712888999",
        "category": "Tanzanian restaurant",
        "reviews_count": 64,
        "rating": 4.5,
        "hours": "Mon–Sun 10:00–22:00",
        "website": None,
        "city": "Dar es Salaam",
        "region": "Dar es Salaam",
    },
    "zanzibar pearl properties": {
        "business_name": "Zanzibar Pearl Properties",
        "address": "Shangani St, Stone Town, Zanzibar",
        "phone": "+255778222333",
        "category": "Real estate agency",
        "reviews_count": 28,
        "rating": 4.6,
        "hours": "Mon–Fri 09:00–17:00",
        "website": None,
        "city": "Zanzibar City",
        "region": "Zanzibar Urban/West",
    },
}

# Deep-search fixtures: business name -> list of result URLs (none are owned websites
# except for kilizo, which won't reach this step anyway).
DEEP_SEARCH_FIXTURES: dict[str, list[str]] = {
    "serengeti dreams safaris": [
        "https://www.instagram.com/serengetidreamsafaris",
        "https://www.facebook.com/serengetidreamsafaris",
        "https://www.tripadvisor.com/Attraction_Review-Serengeti-Dreams.html",
        "https://www.safaribookings.com/operator/serengeti-dreams",
    ],
    "mama ndogo kitchen": [
        "https://www.instagram.com/mamandogokitchen",
        "https://www.facebook.com/mamandogokitchen",
        "https://foursquare.com/v/mama-ndogo-kitchen",
    ],
    "zanzibar pearl properties": [
        "https://www.instagram.com/zanzibarpearlproperties",
        "https://linktr.ee/zanzibarpearl",
        "https://www.property24.co.tz/agent/zanzibar-pearl",
    ],
}

# Competitor fixtures by category (used when live search is unavailable).
COMPETITOR_FIXTURES: dict[str, list[dict]] = {
    "Tour Agency": [
        {"name": "Easy Travel & Tours", "website_url": "https://www.easytravel.co.tz",
         "key_services": "Safaris, Kilimanjaro treks, Zanzibar beach holidays, online booking"},
        {"name": "Shadows of Africa", "website_url": "https://www.shadowsofafrica.com",
         "key_services": "Custom safaris with instant online quotes and live chat"},
        {"name": "Tanzania Specialist", "website_url": "https://www.tanzaniaspecialist.com",
         "key_services": "SEO-driven safari packages, reviews integration, booking engine"},
    ],
    "Restaurant": [
        {"name": "Mamboz Restaurant", "website_url": "https://www.mambozrestaurant.com",
         "key_services": "Online menu, table reservations, delivery integrations"},
        {"name": "Akemi Revolving Restaurant", "website_url": "https://www.akemirestaurant.com",
         "key_services": "Online booking, events, gallery, Google Maps integration"},
    ],
    "Real Estate": [
        {"name": "Knight Frank Tanzania", "website_url": "https://www.knightfrank.co.tz",
         "key_services": "Property listings, valuations, lead-capture forms"},
        {"name": "Mrisho Consult", "website_url": "https://www.mrishoconsult.co.tz",
         "key_services": "Searchable listings, WhatsApp + enquiry funnels"},
    ],
}


# ── Discovery catalog ──────────────────────────────────────────────────
# A searchable directory of candidate businesses for targeted/NL discovery in fallback
# mode (live mode discovers via Google Places/CSE instead). `has_website` lets discovery
# pre-filter to likely opportunities. Entries with an `instagram` handle scan into rich
# leads via INSTAGRAM_FIXTURES; the rest scan into basic leads.
BUSINESS_DIRECTORY: list[dict] = [
    {"business_name": "Serengeti Dreams Safaris", "instagram": "serengetidreamsafaris",
     "category": "Tour Agency", "industry": "Travel & Tourism", "city": "Arusha",
     "region": "Arusha", "followers": 18400, "has_website": False},
    {"business_name": "Zanzibar Pearl Properties", "instagram": "zanzibarpearlproperties",
     "category": "Real Estate", "industry": "Real Estate", "city": "Zanzibar City",
     "region": "Zanzibar Urban/West", "followers": 9800, "has_website": False},
    {"business_name": "Mama Ndogo Kitchen", "instagram": "mamandogokitchen",
     "category": "Restaurant", "industry": "Food & Beverage", "city": "Dar es Salaam",
     "region": "Dar es Salaam", "followers": 5200, "has_website": False},
    {"business_name": "Glamour Salon & Spa", "instagram": "glamoursalondar",
     "category": "Beauty Salon", "industry": "Beauty & Wellness", "city": "Dar es Salaam",
     "region": "Dar es Salaam", "followers": 12600, "has_website": False},
    {"business_name": "Kilimanjaro View Lodge", "instagram": "kilimanjaroviewlodge",
     "category": "Hotel", "industry": "Hospitality", "city": "Moshi",
     "region": "Kilimanjaro", "followers": 23100, "has_website": False},
    {"business_name": "Mwanza Auto Garage", "instagram": "mwanzaautogarage",
     "category": "Automotive", "industry": "Automotive", "city": "Mwanza",
     "region": "Mwanza", "followers": 3400, "has_website": False},
    {"business_name": "Kilizo Tech Solutions", "instagram": "kilizotech",
     "category": "Information Technology", "industry": "Information Technology",
     "city": "Dodoma", "region": "Dodoma", "followers": 2100, "has_website": True},
    # directory-only entries (no IG fixture; scan to basic leads)
    {"business_name": "Arusha Coffee Roasters", "instagram": None,
     "category": "Cafe", "industry": "Food & Beverage", "city": "Arusha",
     "region": "Arusha", "followers": 7600, "has_website": False},
    {"business_name": "Bagamoyo Beach Resort", "instagram": None,
     "category": "Hotel", "industry": "Hospitality", "city": "Bagamoyo",
     "region": "Pwani", "followers": 14200, "has_website": False},
    {"business_name": "Dar Dental Clinic", "instagram": None,
     "category": "Dental Clinic", "industry": "Healthcare", "city": "Dar es Salaam",
     "region": "Dar es Salaam", "followers": 1800, "has_website": False},
    {"business_name": "Tanga Fresh Produce", "instagram": None,
     "category": "Wholesale", "industry": "Agriculture", "city": "Tanga",
     "region": "Tanga", "followers": 900, "has_website": False},
    {"business_name": "Iringa Builders Ltd", "instagram": None,
     "category": "Construction", "industry": "Construction", "city": "Iringa",
     "region": "Iringa", "followers": 1200, "has_website": False},
    {"business_name": "Stone Town Boutique Hotel", "instagram": None,
     "category": "Hotel", "industry": "Hospitality", "city": "Zanzibar City",
     "region": "Zanzibar Urban/West", "followers": 16700, "has_website": False},
    {"business_name": "Mbeya Highlands Tours", "instagram": None,
     "category": "Tour Agency", "industry": "Travel & Tourism", "city": "Mbeya",
     "region": "Mbeya", "followers": 4300, "has_website": False},
]

# Canonical vocabularies for the natural-language fallback parser.
TZ_CITIES = [
    "Arusha", "Dar es Salaam", "Dodoma", "Mwanza", "Moshi", "Zanzibar City", "Zanzibar",
    "Mbeya", "Tanga", "Morogoro", "Bagamoyo", "Iringa", "Kigoma", "Tabora", "Songea",
]
CITY_TO_REGION = {
    "Arusha": "Arusha", "Dar es Salaam": "Dar es Salaam", "Dodoma": "Dodoma",
    "Mwanza": "Mwanza", "Moshi": "Kilimanjaro", "Zanzibar City": "Zanzibar Urban/West",
    "Zanzibar": "Zanzibar Urban/West", "Mbeya": "Mbeya", "Tanga": "Tanga",
    "Morogoro": "Morogoro", "Bagamoyo": "Pwani", "Iringa": "Iringa",
}
# keyword -> canonical category bucket used for matching
INDUSTRY_KEYWORDS = {
    "safari": "Tour Agency", "tour": "Tour Agency", "travel": "Tour Agency",
    "tourism": "Tour Agency", "restaurant": "Restaurant", "food": "Restaurant",
    "cafe": "Cafe", "coffee": "Cafe", "hotel": "Hotel", "lodge": "Hotel",
    "resort": "Hotel", "hospitality": "Hotel", "real estate": "Real Estate",
    "property": "Real Estate", "properties": "Real Estate", "salon": "Beauty Salon",
    "spa": "Beauty Salon", "beauty": "Beauty Salon", "auto": "Automotive",
    "garage": "Automotive", "car": "Automotive", "tech": "Information Technology",
    "software": "Information Technology", "it ": "Information Technology",
    "dental": "Dental Clinic", "clinic": "Healthcare", "health": "Healthcare",
    "construction": "Construction", "builder": "Construction",
    "agriculture": "Agriculture", "produce": "Agriculture", "farm": "Agriculture",
}


def slug(text: str) -> str:
    return text.strip().lower()

"""Seed the database with an admin account and demo data.

Usage:
    python seed.py

Idempotent: the admin is upserted by email, and demo products/users/reviews
are only inserted when the products table is empty. To reseed from scratch
(e.g. after a schema change), delete the dev database first.
"""

from sqlalchemy import select

from app.config.config import settings
from app.config.database import SessionLocal, init_db
from app.constants.app_constants import REVIEW_STATUS_APPROVED, REVIEW_STATUS_PENDING
from app.constants.roles import ROLE_ADMIN, ROLE_MODERATOR
from app.modules.products.models import Product
from app.modules.reviews.models import Review
from app.modules.users.models import User
from app.utils.security import hash_password
from app.utils.utils import normalize_email

# ---- Demo people who write the reviews (referenced by index below) ----
DEMO_USERS = [
    ("John Carter", "john@example.com"),
    ("Jane Mills", "jane@example.com"),
    ("Mia Chen", "mia@example.com"),
    ("Leo Alvarez", "leo@example.com"),
    ("Sofia Rossi", "sofia@example.com"),
    ("Noah Patel", "noah@example.com"),
]


def _img(seed: str) -> str:
    return f"https://picsum.photos/seed/{seed}/800/600"


def _photo(seed: str) -> str:
    return f"https://picsum.photos/seed/{seed}/700/520"


# Each product: title, description, image, and reviews as
# (user_index, rating, comment, [photo urls]).
PRODUCTS = [
    {
        "title": "Aurora Wireless Headphones",
        "description": "Over-ear noise-cancelling headphones with 30-hour battery and plush memory-foam cushions.",
        "image": _img("aurora-headphones"),
        "reviews": [
            (0, 5, "Excellent sound and the noise cancelling is genuinely impressive on flights.", [_photo("aurora-a"), _photo("aurora-b")]),
            (1, 4, "Great audio, just a touch heavy after a few hours.", []),
            (2, 5, "Battery easily lasts my work week. No regrets.", []),
            (3, 4, "Crisp highs, balanced bass. Worth it on sale.", []),
        ],
    },
    {
        "title": "Pulse Fitness Smartwatch",
        "description": "Lightweight smartwatch with heart-rate, sleep tracking, GPS and a bright always-on display.",
        "image": _img("pulse-watch"),
        "reviews": [
            (4, 4, "Accurate tracking and the screen is easy to read outdoors.", []),
            (1, 3, "Decent, but the app could be more polished.", []),
            (5, 4, "Comfortable to wear overnight for sleep data.", []),
        ],
    },
    {
        "title": "Nimbus Mechanical Keyboard",
        "description": "Hot-swappable 75% mechanical keyboard with PBT keycaps and a satisfying tactile feel.",
        "image": _img("nimbus-keyboard"),
        "reviews": [
            (3, 5, "Typing on this is a joy. The stabilisers are pre-lubed and rattle-free.", [_photo("nimbus-a")]),
            (2, 5, "Compact, sturdy, and the keycaps feel premium.", []),
            (0, 4, "Love it, wish it had more backlight modes.", []),
        ],
    },
    {
        "title": 'Vista 27" 4K Monitor',
        "description": "27-inch 4K IPS monitor with 99% sRGB, USB-C charging and slim bezels.",
        "image": _img("vista-monitor"),
        "reviews": [
            (5, 5, "Colours are gorgeous and USB-C powers my laptop with one cable.", []),
            (1, 4, "Sharp and bright. Stand is a little wobbly.", []),
        ],
    },
    {
        "title": "Terra Pour-Over Coffee Maker",
        "description": "Borosilicate glass pour-over set with a reusable stainless filter and walnut collar.",
        "image": _img("terra-coffee"),
        "reviews": [
            (2, 4, "Makes a clean, bright cup. Looks great on the counter.", []),
            (4, 4, "Simple and effective once you dial in the grind.", []),
            (0, 3, "Good, but the filter can clog with finer grounds.", []),
            (3, 4, "My morning ritual upgraded.", []),
        ],
    },
    {
        "title": "Drift Portable Bluetooth Speaker",
        "description": "Pocket-sized IPX7 waterproof speaker with surprisingly full sound and 12-hour battery.",
        "image": _img("drift-speaker"),
        "reviews": [
            (1, 3, "Fine for the size, but bass is limited.", []),
            (5, 4, "Took it to the beach, survived the splashes!", []),
            (2, 3, "Loud enough for a small room.", []),
        ],
    },
    {
        "title": "Summit 30L Trail Backpack",
        "description": "Ventilated 30-litre hiking pack with rain cover, hip belt and hydration sleeve.",
        "image": _img("summit-backpack"),
        "reviews": [
            (3, 5, "Carried it for a 3-day trek — comfortable and well organised.", [_photo("summit-a")]),
            (4, 5, "The back ventilation actually works. Highly recommend.", []),
            (0, 5, "Tough materials, smart pockets, fair price.", []),
        ],
    },
    {
        "title": "Lumen LED Desk Lamp",
        "description": "Dimmable desk lamp with adjustable colour temperature, USB charging port and timer.",
        "image": _img("lumen-lamp"),
        "reviews": [
            (2, 4, "Even, flicker-free light. The warm setting is lovely in the evening.", []),
            (5, 5, "Great build and the USB port is handy.", []),
        ],
    },
    {
        "title": 'Forge 8" Chef\'s Knife',
        "description": "Full-tang high-carbon stainless chef's knife, hand-finished with an ergonomic handle.",
        "image": _img("forge-knife"),
        "reviews": [
            (0, 5, "Razor sharp out of the box and holds an edge well.", [_photo("forge-a")]),
            (1, 4, "Well balanced. Needs careful drying to avoid spots.", []),
            (3, 5, "My go-to knife now. Beautiful piece.", []),
        ],
    },
    {
        "title": "Glide Ergonomic Wireless Mouse",
        "description": "Sculpted ergonomic mouse with silent clicks, 4000 DPI sensor and USB-C charging.",
        "image": _img("glide-mouse"),
        "reviews": [
            (4, 4, "Comfortable for long sessions, no more wrist ache.", []),
            (2, 4, "Silent clicks are great in shared spaces.", []),
        ],
    },
    {
        "title": "Haven Weighted Blanket",
        "description": "7kg weighted blanket with breathable cotton cover and evenly distributed glass beads.",
        "image": _img("haven-blanket"),
        "reviews": [
            (1, 3, "Cozy, but runs a little warm in summer.", []),
            (5, 4, "Helped me fall asleep faster. Soft cover.", []),
        ],
    },
    {
        "title": "Orbit Robot Vacuum",
        "description": "Self-charging robot vacuum with lidar mapping, app control and a quiet eco mode.",
        "image": _img("orbit-vacuum"),
        "reviews": [
            (0, 2, "Mapping is clever but it gets stuck under low furniture.", []),
            (3, 3, "Decent daily maintenance, not a deep clean.", []),
            (4, 4, "Set-and-forget for the kitchen floor. Happy overall.", []),
        ],
    },
]


def _seed_admin(db) -> User:
    if settings.seed_admin_password == "admin12345" and not settings.is_dev_env:
        raise SystemExit(
            "Refusing to seed the admin with the default password outside development. "
            "Set SEED_ADMIN_PASSWORD to a strong value first."
        )
    email = normalize_email(settings.seed_admin_email)
    admin = db.scalar(select(User).where(User.email == email))
    if admin is None:
        admin = User(
            name=settings.seed_admin_name,
            email=email,
            password_hash=hash_password(settings.seed_admin_password),
            role=ROLE_ADMIN,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        print(f"  + admin created: {email}")
    else:
        print(f"  = admin already exists: {email}")
    return admin


def _seed_demo(db) -> None:
    if db.scalar(select(Product).limit(1)) is not None:
        print("  = products already present, skipping demo data")
        return

    users = [User(name=name, email=normalize_email(email)) for name, email in DEMO_USERS]
    db.add_all(users)

    # A demo moderator (has a password, so can sign in and work the queue).
    moderator = User(
        name="Maya Moderator",
        email="moderator@reviewdibo.com",
        password_hash=hash_password("moderator12345"),
        role=ROLE_MODERATOR,
    )
    db.add(moderator)
    db.flush()

    products: list[Product] = []
    review_count = 0
    for spec in PRODUCTS:
        product = Product(
            title=spec["title"],
            description=spec["description"],
            image_url=spec["image"],
        )
        db.add(product)
        db.flush()
        products.append(product)
        for user_index, rating, comment, photos in spec["reviews"]:
            db.add(
                Review(
                    product_id=product.id,
                    user_id=users[user_index].id,
                    rating=rating,
                    comment=comment,
                    images=list(photos),
                    status=REVIEW_STATUS_APPROVED,
                )
            )
            review_count += 1

    # A few guest reviews awaiting moderation (populates the moderation queue).
    pending = [
        (products[0], 0, 1, "Counterfeit unit — very disappointed.", []),
        (products[3], 1, 2, "Screen had dead pixels out of the box.", []),
        (products[6], 2, 5, "AMAZING!!! buy now!!! best deal ever!!!", []),
    ]
    for product, user_index, rating, comment, photos in pending:
        db.add(
            Review(
                product_id=product.id,
                user_id=users[user_index].id,
                rating=rating,
                comment=comment,
                images=list(photos),
                status=REVIEW_STATUS_PENDING,
            )
        )
        review_count += 1

    db.commit()
    print(
        f"  + {len(users) + 1} users (incl. a moderator), {len(PRODUCTS)} products "
        f"and {review_count} reviews created"
    )


def main() -> None:
    print("Seeding database...")
    init_db()
    db = SessionLocal()
    try:
        _seed_admin(db)
        _seed_demo(db)
    finally:
        db.close()
    print("Done.")


if __name__ == "__main__":
    main()

"""Seed the database with an admin account and demo data.

Usage:
    python seed.py

Idempotent: the admin is upserted by email, and demo products/users/reviews
are only inserted when the products table is empty.
"""

from sqlalchemy import select

from app.config.config import settings
from app.config.database import SessionLocal, init_db
from app.modules.products.models import Product
from app.modules.reviews.models import Review
from app.modules.users.models import User
from app.utils.security import hash_password
from app.utils.utils import normalize_email


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
            is_admin=True,
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

    john = User(name="John", email="john@example.com")
    jane = User(name="Jane", email="jane@example.com")
    db.add_all([john, jane])
    db.flush()

    laptop = Product(
        title="Gaming Laptop",
        description="High-performance laptop for gaming and development.",
        image_url="https://placehold.co/600x400?text=Laptop",
    )
    headphones = Product(
        title="Wireless Headphones",
        description="Noise-cancelling over-ear headphones with 30h battery.",
        image_url="https://placehold.co/600x400?text=Headphones",
    )
    coffee = Product(
        title="Coffee Maker",
        description="Programmable drip coffee maker with thermal carafe.",
        image_url="https://placehold.co/600x400?text=Coffee+Maker",
    )
    db.add_all([laptop, headphones, coffee])
    db.flush()

    db.add_all(
        [
            Review(product_id=laptop.id, user_id=john.id, rating=5, comment="Excellent product"),
            Review(product_id=laptop.id, user_id=jane.id, rating=4, comment="Great but pricey"),
            Review(product_id=headphones.id, user_id=john.id, rating=5, comment="Amazing sound"),
            Review(product_id=headphones.id, user_id=jane.id, rating=3, comment="Comfortable, average bass"),
            Review(product_id=coffee.id, user_id=jane.id, rating=4, comment="Makes good coffee"),
        ]
    )
    db.commit()
    print("  + demo users, products and reviews created")


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

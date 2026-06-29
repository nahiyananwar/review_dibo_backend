"""End-to-end smoke tests covering the full API surface.

Run with: pytest -q
"""

from tests.conftest import auth


def _create_product(client, admin_token, title="Test Product") -> dict:
    resp = client.post(
        "/api/products",
        json={"title": title, "description": "desc", "image_url": None},
        headers=auth(admin_token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _create_user(client, name, email) -> dict:
    resp = client.post("/api/users", json={"name": name, "email": email})
    assert resp.status_code in (200, 201), resp.text
    return resp.json()


def _register_member(client, name, email, password="password123") -> tuple[str, int]:
    """Register a real member (has a password) -> returns (token, user_id).

    Member reviews must be posted authenticated (the server attributes the author
    from the session), so callers pass the token on POST /api/reviews.
    """
    resp = client.post(
        "/api/auth/register", json={"name": name, "email": email, "password": password}
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["access_token"], resp.json()["user"]["id"]


# ----------------------------- health -----------------------------------


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_root(client):
    assert client.get("/").status_code == 200


# ----------------------- products & reviews -----------------------------


def test_create_product_requires_admin(client):
    resp = client.post("/api/products", json={"title": "Nope"})
    assert resp.status_code == 401


def test_full_review_flow(client, admin_token):
    product = _create_product(client, admin_token, title="Aggregate Laptop")
    assert product["average_rating"] == 0.0
    assert product["review_count"] == 0
    pid = product["id"]

    john_tok, john_id = _register_member(client, "John Flow", "john_flow@example.com")
    jane_tok, jane_id = _register_member(client, "Jane Flow", "jane_flow@example.com")

    r1 = client.post(
        "/api/reviews",
        json={"product_id": pid, "user_id": john_id, "rating": 5, "comment": "Excellent"},
        headers=auth(john_tok),
    )
    assert r1.status_code == 201, r1.text
    client.post(
        "/api/reviews",
        json={"product_id": pid, "user_id": jane_id, "rating": 3, "comment": "Okay"},
        headers=auth(jane_tok),
    )

    detail = client.get(f"/api/products/{pid}").json()
    assert detail["review_count"] == 2
    assert detail["average_rating"] == 4.0
    assert len(detail["reviews"]) == 2
    assert {rev["user"] for rev in detail["reviews"]} == {"John Flow", "Jane Flow"}

    # search finds it, min_rating filters it
    found = client.get("/api/products", params={"search": "Aggregate"}).json()
    assert any(p["id"] == pid for p in found)
    high = client.get("/api/products", params={"min_rating": 5}).json()
    assert all(p["id"] != pid for p in high)  # avg 4.0 < 5
    ok = client.get("/api/products", params={"min_rating": 4}).json()
    assert any(p["id"] == pid for p in ok)


def test_review_create_validation(client):
    resp = client.post(
        "/api/reviews",
        json={"product_id": 1, "user_id": 1, "rating": 6, "comment": "too high"},
    )
    assert resp.status_code == 422


def test_review_fk_validation(client, admin_token):
    product = _create_product(client, admin_token, title="FK Product")
    # nonexistent user
    resp = client.post(
        "/api/reviews",
        json={"product_id": product["id"], "user_id": 999999, "rating": 4},
    )
    assert resp.status_code == 404


def test_product_not_found(client):
    assert client.get("/api/products/999999").status_code == 404


def test_cascade_delete_product(client, admin_token):
    product = _create_product(client, admin_token, title="Cascade Product")
    user = _create_user(client, "Casey", "casey@example.com")
    client.post(
        "/api/reviews",
        json={"product_id": product["id"], "user_id": user["id"], "rating": 4},
    )
    resp = client.delete(f"/api/products/{product['id']}", headers=auth(admin_token))
    assert resp.status_code == 204
    assert client.get(f"/api/products/{product['id']}").status_code == 404


# ------------------------------ auth ------------------------------------


def test_auth_register_login_me(client):
    reg = client.post(
        "/api/auth/register",
        json={"name": "Alice", "email": "alice@example.com", "password": "password123"},
    )
    assert reg.status_code == 201, reg.text
    body = reg.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["is_admin"] is False

    # duplicate email -> 409
    dup = client.post(
        "/api/auth/register",
        json={"name": "Alice2", "email": "alice@example.com", "password": "password123"},
    )
    assert dup.status_code == 409

    # login (OAuth2 form) -> token
    login = client.post(
        "/api/auth/login",
        data={"username": "alice@example.com", "password": "password123"},
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]

    me = client.get("/api/auth/me", headers=auth(token))
    assert me.status_code == 200
    assert me.json()["email"] == "alice@example.com"

    # wrong password -> 401
    bad = client.post(
        "/api/auth/login",
        data={"username": "alice@example.com", "password": "wrong"},
    )
    assert bad.status_code == 401


def test_update_requires_auth(client, admin_token):
    product = _create_product(client, admin_token, title="Auth Product")
    user = _create_user(client, "Bob", "bob@example.com")
    review = client.post(
        "/api/reviews",
        json={"product_id": product["id"], "user_id": user["id"], "rating": 4},
    ).json()

    # no token
    assert client.put(f"/api/reviews/{review['id']}", json={"rating": 2}).status_code == 401

    # admin can update
    upd = client.put(
        f"/api/reviews/{review['id']}", json={"rating": 2}, headers=auth(admin_token)
    )
    assert upd.status_code == 200
    assert upd.json()["rating"] == 2


def test_non_owner_cannot_delete(client, admin_token):
    product = _create_product(client, admin_token, title="Owner Product")
    guest = _create_user(client, "Guest", "guest@example.com")
    review = client.post(
        "/api/reviews",
        json={"product_id": product["id"], "user_id": guest["id"], "rating": 4},
    ).json()

    # a different, non-admin registered user
    client.post(
        "/api/auth/register",
        json={"name": "Eve", "email": "eve@example.com", "password": "password123"},
    )
    token = client.post(
        "/api/auth/login", data={"username": "eve@example.com", "password": "password123"}
    ).json()["access_token"]

    resp = client.delete(f"/api/reviews/{review['id']}", headers=auth(token))
    assert resp.status_code == 403


# ------------------------------ admin -----------------------------------


def test_admin_moderation(client, admin_token):
    product = _create_product(client, admin_token, title="Moderation Product")
    user = _create_user(client, "Mallory", "mallory@example.com")
    review = client.post(
        "/api/reviews",
        json={"product_id": product["id"], "user_id": user["id"], "rating": 1, "comment": "spam"},
    ).json()

    listing = client.get("/api/admin/reviews", headers=auth(admin_token))
    assert listing.status_code == 200
    assert any(r["id"] == review["id"] for r in listing.json())

    # non-admin cannot list
    assert client.get("/api/admin/reviews").status_code == 401

    # admin override delete
    dele = client.delete(f"/api/admin/reviews/{review['id']}", headers=auth(admin_token))
    assert dele.status_code == 204


# ------------------------- review images --------------------------------

_TINY_PNG = (
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0"
    "lEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


def test_review_with_images(client, admin_token):
    product = _create_product(client, admin_token, title="Photo Product")
    tok, uid = _register_member(client, "Photographer", "photog@example.com")
    resp = client.post(
        "/api/reviews",
        json={
            "product_id": product["id"],
            "user_id": uid,
            "rating": 5,
            "comment": "See the photo",
            "images": [_TINY_PNG],
        },
        headers=auth(tok),
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["images"] == [_TINY_PNG]

    detail = client.get(f"/api/products/{product['id']}").json()
    assert detail["reviews"][0]["images"] == [_TINY_PNG]


def test_review_too_many_images(client, admin_token):
    product = _create_product(client, admin_token, title="Too Many Images")
    user = _create_user(client, "Spammer", "spammer@example.com")
    resp = client.post(
        "/api/reviews",
        json={"product_id": product["id"], "user_id": user["id"], "rating": 4, "images": ["x"] * 7},
    )
    assert resp.status_code == 422


def test_review_images_default_empty(client, admin_token):
    product = _create_product(client, admin_token, title="No Images Product")
    user = _create_user(client, "Plain", "plain@example.com")
    resp = client.post(
        "/api/reviews",
        json={"product_id": product["id"], "user_id": user["id"], "rating": 4},
    )
    assert resp.status_code == 201
    assert resp.json()["images"] == []


# ---------------- regression: /me must not re-validate stored email ------


def test_me_with_reserved_tld_email(client):
    """A user whose stored email uses a reserved TLD (e.g. seeded admin) must
    not 500 on /me — output schemas serialize email as a plain string."""
    from app.config.database import SessionLocal
    from app.constants.roles import ROLE_ADMIN
    from app.modules.users.models import User
    from app.services.auth.auth_service import issue_token
    from app.utils.security import hash_password

    db = SessionLocal()
    try:
        user = User(
            name="Local User",
            email="weird@reviewdibo.local",
            password_hash=hash_password("password123"),
            role=ROLE_ADMIN,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        token = issue_token(user)
    finally:
        db.close()

    resp = client.get("/api/auth/me", headers=auth(token))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["email"] == "weird@reviewdibo.local"
    assert body["is_admin"] is True
    assert body["role"] == "admin"


# --------------------- regression: filter/display consistency ---------------


def test_min_rating_filter_matches_displayed_average(client, admin_token):
    """A product whose RAW average rounds up across an integer boundary must be
    INCLUDED by a min_rating filter equal to its DISPLAYED average (no mismatch).

    20x rating 4 + 1x rating 3 -> raw 3.952..., displayed average_rating 4.0.
    """
    from app.config.database import SessionLocal
    from app.constants.app_constants import REVIEW_STATUS_APPROVED
    from app.modules.products.models import Product
    from app.modules.reviews.models import Review
    from app.modules.users.models import User

    db = SessionLocal()
    try:
        user = User(name="Boundary", email="boundary@example.com")
        product = Product(title="Boundary Product")
        db.add_all([user, product])
        db.flush()
        db.add_all(
            [
                Review(product_id=product.id, user_id=user.id, rating=4, status=REVIEW_STATUS_APPROVED)
                for _ in range(20)
            ]
        )
        db.add(Review(product_id=product.id, user_id=user.id, rating=3, status=REVIEW_STATUS_APPROVED))
        db.commit()
        pid = product.id
    finally:
        db.close()

    detail = client.get(f"/api/products/{pid}").json()
    assert detail["average_rating"] == 4.0  # displayed value

    listed = client.get("/api/products", params={"min_rating": 4}).json()
    match = [p for p in listed if p["id"] == pid]
    assert match and match[0]["average_rating"] == 4.0  # included, consistent

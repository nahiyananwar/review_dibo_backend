"""Battle tests — exhaustive edge/use cases across every endpoint.

Goal: every error path returns a correct 4xx (never a 500), and every contract
boundary is enforced. Complements tests/test_smoke.py (happy paths).
"""

from tests.conftest import auth


# ----------------------------- helpers ----------------------------------


def _admin_product(client, admin_token, title="Battle Product"):
    r = client.post("/api/products", json={"title": title}, headers=auth(admin_token))
    assert r.status_code == 201, r.text
    return r.json()


def _register(client, name, email, password="password123"):
    """Return (token, user_id) for a freshly registered user."""
    reg = client.post(
        "/api/auth/register", json={"name": name, "email": email, "password": password}
    )
    assert reg.status_code == 201, reg.text
    token = reg.json()["access_token"]
    return token, reg.json()["user"]["id"]


def _resolve_user(client, name, email):
    r = client.post("/api/users", json={"name": name, "email": email})
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


# ----------------------------- products ---------------------------------


def test_product_detail_not_found(client):
    assert client.get("/api/products/999999").status_code == 404


def test_product_detail_non_integer_id(client):
    assert client.get("/api/products/not-a-number").status_code == 422


def test_product_create_auth_and_validation(client, admin_token):
    # auth
    assert client.post("/api/products", json={"title": "X"}).status_code == 401
    user_token, _ = _register(client, "NonAdmin", "nonadmin_pc@example.com")
    assert client.post("/api/products", json={"title": "X"}, headers=auth(user_token)).status_code == 403
    # validation (as admin)
    h = auth(admin_token)
    assert client.post("/api/products", json={}, headers=h).status_code == 422
    assert client.post("/api/products", json={"title": ""}, headers=h).status_code == 422
    assert client.post("/api/products", json={"title": "   "}, headers=h).status_code == 422
    assert client.post("/api/products", json={"title": "x" * 256}, headers=h).status_code == 422
    ok = client.post("/api/products", json={"title": "  Trimmed Title  "}, headers=h)
    assert ok.status_code == 201
    assert ok.json()["title"] == "Trimmed Title"  # stored trimmed


def test_product_delete_auth_and_missing(client, admin_token):
    assert client.delete("/api/products/1").status_code == 401
    user_token, _ = _register(client, "NonAdmin2", "nonadmin_pd@example.com")
    assert client.delete("/api/products/1", headers=auth(user_token)).status_code == 403
    assert client.delete("/api/products/999999", headers=auth(admin_token)).status_code == 404


def test_min_rating_validation(client):
    assert client.get("/api/products", params={"min_rating": 6}).status_code == 422
    assert client.get("/api/products", params={"min_rating": -1}).status_code == 422
    assert client.get("/api/products", params={"min_rating": "abc"}).status_code == 422
    assert client.get("/api/products", params={"min_rating": 4.5}).status_code == 200


def test_search_is_safe(client):
    for q in ["'; DROP TABLE products; --", "café ☕ 日本語", "x" * 1000, "%_%", "<script>"]:
        assert client.get("/api/products", params={"search": q}).status_code == 200


# ------------------------------ users -----------------------------------


def test_user_create_validation(client):
    assert client.post("/api/users", json={"name": "A", "email": "notanemail"}).status_code == 422
    assert client.post("/api/users", json={"name": "A", "email": "x@y.local"}).status_code == 422
    assert client.post("/api/users", json={"email": "a@b.com"}).status_code == 422
    assert client.post("/api/users", json={"name": "   ", "email": "blank@b.com"}).status_code == 422
    assert client.post("/api/users", json={"name": "x" * 121, "email": "long@b.com"}).status_code == 422


def test_user_create_idempotent_and_case_insensitive(client):
    a = client.post("/api/users", json={"name": "Case", "email": "Case.User@Example.com"})
    assert a.status_code == 201
    b = client.post("/api/users", json={"name": "Case Again", "email": "case.user@example.com"})
    assert b.status_code == 200
    assert a.json()["id"] == b.json()["id"]  # same user, idempotent on normalized email


# ----------------------------- reviews ----------------------------------


def test_review_create_validation(client, admin_token):
    product = _admin_product(client, admin_token, title="Review Validation")
    uid = _resolve_user(client, "Rv", "rv@example.com")
    pid = product["id"]

    def post(body):
        return client.post("/api/reviews", json=body)

    base = {"product_id": pid, "user_id": uid, "rating": 5}
    assert post({**base, "rating": 0}).status_code == 422
    assert post({**base, "rating": 6}).status_code == 422
    assert post({**base, "rating": 3.5}).status_code == 422
    assert post({**base, "rating": "x"}).status_code == 422
    assert post({"product_id": pid, "user_id": uid}).status_code == 422  # missing rating
    assert post({**base, "product_id": 999999}).status_code == 404
    assert post({**base, "user_id": 999999}).status_code == 404
    assert post({**base, "comment": "x" * 2001}).status_code == 422
    assert post({**base, "comment": "ok"}).status_code == 201


def test_review_images_validation(client, admin_token):
    product = _admin_product(client, admin_token, title="Review Images Validation")
    uid = _resolve_user(client, "Iv", "iv@example.com")
    base = {"product_id": product["id"], "user_id": uid, "rating": 4}

    assert client.post("/api/reviews", json={**base, "images": ["x"] * 7}).status_code == 422
    assert client.post("/api/reviews", json={**base, "images": [""]}).status_code == 422
    assert client.post("/api/reviews", json={**base, "images": [123]}).status_code == 422
    assert client.post("/api/reviews", json={**base, "images": "notalist"}).status_code == 422
    assert client.post("/api/reviews", json={**base, "images": ["x" * 4_000_001]}).status_code == 422
    assert client.post("/api/reviews", json={**base, "images": ["justastring"]}).status_code == 422
    assert client.post("/api/reviews", json={**base, "images": ["data:image/png;base64,AAAA"]}).status_code == 201
    assert client.post("/api/reviews", json={**base, "images": ["http://example.com/p.jpg"]}).status_code == 201


def test_review_update_auth_and_ownership(client, admin_token):
    product = _admin_product(client, admin_token, title="Review Update")
    owner_token, owner_id = _register(client, "Owner", "owner_ru@example.com")
    other_token, _ = _register(client, "Other", "other_ru@example.com")
    review = client.post(
        "/api/reviews",
        json={"product_id": product["id"], "user_id": owner_id, "rating": 3},
        headers=auth(owner_token),
    ).json()
    rid = review["id"]

    assert client.put(f"/api/reviews/{rid}", json={"rating": 5}).status_code == 401
    assert client.put(f"/api/reviews/{rid}", json={"rating": 5}, headers=auth(other_token)).status_code == 403
    assert client.put(f"/api/reviews/{rid}", json={}, headers=auth(owner_token)).status_code == 422
    assert client.put(f"/api/reviews/{rid}", json={"rating": 6}, headers=auth(owner_token)).status_code == 422
    assert client.put(f"/api/reviews/{rid}", json={"rating": 5}, headers=auth(owner_token)).status_code == 200
    assert client.put(f"/api/reviews/{rid}", json={"comment": "by admin"}, headers=auth(admin_token)).status_code == 200
    assert client.put("/api/reviews/999999", json={"rating": 5}, headers=auth(admin_token)).status_code == 404


def test_review_delete_auth_and_ownership(client, admin_token):
    product = _admin_product(client, admin_token, title="Review Delete")
    owner_token, owner_id = _register(client, "DOwner", "downer@example.com")
    other_token, _ = _register(client, "DOther", "dother@example.com")
    review = client.post(
        "/api/reviews",
        json={"product_id": product["id"], "user_id": owner_id, "rating": 3},
        headers=auth(owner_token),
    ).json()
    rid = review["id"]

    assert client.delete(f"/api/reviews/{rid}").status_code == 401
    assert client.delete(f"/api/reviews/{rid}", headers=auth(other_token)).status_code == 403
    assert client.delete(f"/api/reviews/{rid}", headers=auth(owner_token)).status_code == 204
    assert client.delete("/api/reviews/999999", headers=auth(admin_token)).status_code == 404


# ------------------------------ auth ------------------------------------


def test_register_validation(client):
    base = {"name": "Reg", "email": "reg_v@example.com", "password": "password123"}
    assert client.post("/api/auth/register", json={**base, "password": "short"}).status_code == 422
    assert client.post("/api/auth/register", json={**base, "password": "x" * 73}).status_code == 422
    assert client.post("/api/auth/register", json={**base, "email": "bad"}).status_code == 422
    assert client.post("/api/auth/register", json={**base, "name": "   "}).status_code == 422
    assert client.post("/api/auth/register", json={"name": "x"}).status_code == 422  # missing fields
    first = client.post("/api/auth/register", json=base)
    assert first.status_code == 201
    assert client.post("/api/auth/register", json=base).status_code == 409  # duplicate


def test_login_edge_cases(client):
    _register(client, "Login", "login_e@example.com", password="password123")
    assert client.post("/api/auth/login", data={"username": "login_e@example.com", "password": "wrong"}).status_code == 401
    assert client.post("/api/auth/login", data={"username": "nobody@example.com", "password": "password123"}).status_code == 401
    assert client.post("/api/auth/login", data={"username": "login_e@example.com"}).status_code == 422  # missing password
    # a user created via /api/users has no password -> cannot log in
    _resolve_user(client, "NoPass", "nopass@example.com")
    assert client.post("/api/auth/login", data={"username": "nopass@example.com", "password": "whatever"}).status_code == 401


def test_me_token_edge_cases(client):
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer not.a.jwt"}).status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer"}).status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": "Basic abc"}).status_code == 401
    token, _ = _register(client, "Me", "me_edge@example.com")
    assert client.get("/api/auth/me", headers=auth(token)).status_code == 200


# ------------------------------ admin -----------------------------------


def test_admin_endpoints_auth(client, admin_token):
    assert client.get("/api/admin/reviews").status_code == 401
    user_token, _ = _register(client, "AdminNo", "adminno@example.com")
    assert client.get("/api/admin/reviews", headers=auth(user_token)).status_code == 403
    assert client.get("/api/admin/reviews", headers=auth(admin_token)).status_code == 200
    assert client.delete("/api/admin/reviews/1").status_code == 401
    assert client.delete("/api/admin/reviews/1", headers=auth(user_token)).status_code == 403
    assert client.delete("/api/admin/reviews/999999", headers=auth(admin_token)).status_code == 404


# ----------------------------- general ----------------------------------


def test_unknown_route_404(client):
    assert client.get("/api/does-not-exist").status_code == 404


def test_method_not_allowed_405(client):
    assert client.patch("/api/products").status_code == 405


def test_malformed_json_422(client):
    resp = client.post(
        "/api/reviews", content="{not valid json", headers={"content-type": "application/json"}
    )
    assert resp.status_code == 422


def test_health_and_root(client):
    assert client.get("/health").status_code == 200
    assert client.get("/").status_code == 200

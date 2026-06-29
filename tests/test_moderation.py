"""Tests for the moderation workflow + hybrid auto-approval + RBAC."""

from tests.conftest import auth


def _product(client, admin_token, title="Mod Product") -> dict:
    return client.post("/api/products", json={"title": title}, headers=auth(admin_token)).json()


def _guest_review(client, product_id, name, email, rating=4, comment="guest review") -> dict:
    uid = client.post("/api/users", json={"name": name, "email": email}).json()["id"]
    return client.post(
        "/api/reviews",
        json={"product_id": product_id, "user_id": uid, "rating": rating, "comment": comment},
    ).json()


def _register(client, name, email, password="password123"):
    r = client.post(
        "/api/auth/register", json={"name": name, "email": email, "password": password}
    )
    return r.json()["access_token"], r.json()["user"]["id"]


# ----------------------- hybrid auto-approval ---------------------------


def test_guest_review_is_pending_and_hidden(client, admin_token):
    product = _product(client, admin_token, "Pending Visibility")
    rv = _guest_review(client, product["id"], "Guesty", "guesty@example.com")
    assert rv["status"] == "pending"
    detail = client.get(f"/api/products/{product['id']}").json()
    assert detail["review_count"] == 0
    assert detail["reviews"] == []


def test_member_review_is_auto_approved(client, admin_token):
    product = _product(client, admin_token, "Auto Approve")
    tok, uid = _register(client, "Mem", "mem_auto@example.com")
    rv = client.post(
        "/api/reviews",
        json={"product_id": product["id"], "user_id": uid, "rating": 5, "comment": "great"},
        headers=auth(tok),
    ).json()
    assert rv["status"] == "approved"
    assert client.get(f"/api/products/{product['id']}").json()["review_count"] == 1


def test_cannot_impersonate_member_without_auth(client, admin_token):
    """An anonymous request may not post under a credentialed member's user_id."""
    product = _product(client, admin_token, "Impersonation")
    _, member_id = _register(client, "Victim", "victim_imp@example.com")
    resp = client.post(
        "/api/reviews",
        json={"product_id": product["id"], "user_id": member_id, "rating": 5, "comment": "fake"},
    )
    assert resp.status_code == 403


def test_member_edit_returns_review_to_moderation(client, admin_token):
    """A member editing their auto-approved review sends it back to pending."""
    product = _product(client, admin_token, "Edit Re-moderation")
    tok, uid = _register(client, "Editor", "editor_remod@example.com")
    rv = client.post(
        "/api/reviews",
        json={"product_id": product["id"], "user_id": uid, "rating": 5, "comment": "v1"},
        headers=auth(tok),
    ).json()
    assert rv["status"] == "approved"
    assert client.get(f"/api/products/{product['id']}").json()["review_count"] == 1

    upd = client.put(f"/api/reviews/{rv['id']}", json={"comment": "v2 edited"}, headers=auth(tok))
    assert upd.status_code == 200 and upd.json()["status"] == "pending"
    assert client.get(f"/api/products/{product['id']}").json()["review_count"] == 0


# --------------------------- queue + RBAC -------------------------------


def test_moderation_queue_auth(client, admin_token, moderator_token):
    assert client.get("/api/moderation/reviews").status_code == 401
    user_token, _ = _register(client, "Reg", "reg_mod@example.com")
    assert client.get("/api/moderation/reviews", headers=auth(user_token)).status_code == 403
    assert client.get("/api/moderation/reviews", headers=auth(moderator_token)).status_code == 200
    assert client.get("/api/moderation/reviews", headers=auth(admin_token)).status_code == 200


def test_approve_makes_review_visible(client, admin_token, moderator_token):
    product = _product(client, admin_token, "Approve Flow")
    rv = _guest_review(client, product["id"], "Gx", "gx@example.com", rating=5)
    assert rv["status"] == "pending"

    queue = client.get(
        "/api/moderation/reviews", params={"status": "pending"}, headers=auth(moderator_token)
    ).json()
    assert any(item["id"] == rv["id"] for item in queue)

    res = client.patch(
        f"/api/moderation/reviews/{rv['id']}", json={"status": "approved"}, headers=auth(moderator_token)
    )
    assert res.status_code == 200 and res.json()["status"] == "approved"

    detail = client.get(f"/api/products/{product['id']}").json()
    assert detail["review_count"] == 1
    assert any(r["id"] == rv["id"] for r in detail["reviews"])


def test_reject_keeps_review_hidden(client, admin_token, moderator_token):
    product = _product(client, admin_token, "Reject Flow")
    rv = _guest_review(client, product["id"], "Gy", "gy@example.com")
    res = client.patch(
        f"/api/moderation/reviews/{rv['id']}",
        json={"status": "rejected", "rejection_reason": "spam"},
        headers=auth(moderator_token),
    )
    assert res.status_code == 200
    assert res.json()["status"] == "rejected"
    assert res.json()["rejection_reason"] == "spam"
    assert client.get(f"/api/products/{product['id']}").json()["review_count"] == 0


def test_moderate_validation(client, admin_token, moderator_token):
    product = _product(client, admin_token, "Mod Validation")
    rv = _guest_review(client, product["id"], "Gz", "gz@example.com")
    assert client.patch(
        f"/api/moderation/reviews/{rv['id']}", json={"status": "bogus"}, headers=auth(moderator_token)
    ).status_code == 422
    assert client.patch(
        "/api/moderation/reviews/999999", json={"status": "approved"}, headers=auth(moderator_token)
    ).status_code == 404
    user_token, _ = _register(client, "NoMod", "nomod@example.com")
    assert client.patch(
        f"/api/moderation/reviews/{rv['id']}", json={"status": "approved"}, headers=auth(user_token)
    ).status_code == 403


def test_pending_count_reflects_queue(client, admin_token, moderator_token):
    assert client.get("/api/moderation/pending-count").status_code == 401
    user_token, _ = _register(client, "Counter", "counter_pc@example.com")
    assert client.get("/api/moderation/pending-count", headers=auth(user_token)).status_code == 403

    base = client.get("/api/moderation/pending-count", headers=auth(moderator_token)).json()["count"]
    product = _product(client, admin_token, "Count Product")
    rv = _guest_review(client, product["id"], "Cnt", "cnt_pc@example.com")
    after = client.get("/api/moderation/pending-count", headers=auth(moderator_token)).json()["count"]
    assert after == base + 1

    client.patch(
        f"/api/moderation/reviews/{rv['id']}",
        json={"status": "approved"},
        headers=auth(moderator_token),
    )
    final = client.get("/api/moderation/pending-count", headers=auth(moderator_token)).json()["count"]
    assert final == base


def test_assigned_moderator_can_moderate_immediately(client, admin_token):
    """Promoting a user to moderator takes effect at once (role read from DB)."""
    user_token, uid = _register(client, "Future Mod", "futuremod@example.com")
    assert client.get("/api/moderation/reviews", headers=auth(user_token)).status_code == 403
    client.patch(f"/api/admin/users/{uid}", json={"role": "moderator"}, headers=auth(admin_token))
    # token was issued before promotion; authz reads the live DB role
    assert client.get("/api/moderation/reviews", headers=auth(user_token)).status_code == 200

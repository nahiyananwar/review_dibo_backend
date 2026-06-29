"""Tests for profile, admin user management, and password reset."""

from tests.conftest import auth


def _register(client, name, email, password="password123"):
    r = client.post(
        "/api/auth/register", json={"name": name, "email": email, "password": password}
    )
    assert r.status_code == 201, r.text
    return r.json()["access_token"], r.json()["user"]["id"]


def _admin_id(client, admin_token):
    return client.get("/api/auth/me", headers=auth(admin_token)).json()["id"]


def test_admin_can_view_user_profile(client, admin_token):
    token, uid = _register(client, "Profilee", "profilee@example.com")
    product = client.post(
        "/api/products", json={"title": "Profile Product"}, headers=auth(admin_token)
    ).json()
    client.post(
        "/api/reviews",
        json={"product_id": product["id"], "user_id": uid, "rating": 4, "comment": "nice"},
        headers=auth(token),
    )

    res = client.get(f"/api/admin/users/{uid}", headers=auth(admin_token))
    assert res.status_code == 200
    body = res.json()
    assert body["email"] == "profilee@example.com"
    assert body["review_count"] == 1
    assert body["reviews"][0]["product_title"] == "Profile Product"

    # non-admins cannot view, and a missing user is a clean 404
    assert client.get(f"/api/admin/users/{uid}", headers=auth(token)).status_code == 403
    assert client.get("/api/admin/users/999999", headers=auth(admin_token)).status_code == 404


# ----------------------------- profile ----------------------------------


def test_profile_update_and_me(client):
    token, _ = _register(client, "Pat", "pat_profile@example.com")
    upd = client.put("/api/auth/me", json={"name": "Patricia"}, headers=auth(token))
    assert upd.status_code == 200
    assert upd.json()["name"] == "Patricia"
    assert client.get("/api/auth/me", headers=auth(token)).json()["name"] == "Patricia"


def test_profile_update_blank_rejected(client):
    token, _ = _register(client, "Blank", "blank_profile@example.com")
    assert client.put("/api/auth/me", json={"name": "   "}, headers=auth(token)).status_code == 422


def test_profile_update_requires_auth(client):
    assert client.put("/api/auth/me", json={"name": "X"}).status_code == 401


_TINY_AVATAR = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


def test_profile_update_email_and_avatar(client):
    token, _ = _register(client, "Ed", "ed_old@example.com")
    # changing email requires the current password (step-up)
    res = client.put(
        "/api/auth/me",
        json={
            "name": "Eddie",
            "email": "ed_new@example.com",
            "avatar": _TINY_AVATAR,
            "current_password": "password123",
        },
        headers=auth(token),
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["name"] == "Eddie"
    assert body["email"] == "ed_new@example.com"
    assert body["avatar"] == _TINY_AVATAR
    # the new email is what authenticates now
    assert client.get("/api/auth/me", headers=auth(token)).json()["email"] == "ed_new@example.com"

    # name + avatar can change without a password (no email change)
    cleared = client.put("/api/auth/me", json={"name": "Ed", "avatar": None}, headers=auth(token))
    assert cleared.status_code == 200 and cleared.json()["avatar"] is None


def test_email_change_requires_correct_password(client):
    token, _ = _register(client, "Step", "step_old@example.com")
    # missing password -> 401
    assert client.put(
        "/api/auth/me", json={"email": "step_new@example.com"}, headers=auth(token)
    ).status_code == 401
    # wrong password -> 401
    assert client.put(
        "/api/auth/me",
        json={"email": "step_new@example.com", "current_password": "wrongpass"},
        headers=auth(token),
    ).status_code == 401
    # email unchanged
    assert client.get("/api/auth/me", headers=auth(token)).json()["email"] == "step_old@example.com"


def test_profile_update_email_conflict(client):
    _register(client, "Taken", "taken_email@example.com")
    token, _ = _register(client, "Mover", "mover@example.com")
    res = client.put(
        "/api/auth/me",
        json={"email": "taken_email@example.com", "current_password": "password123"},
        headers=auth(token),
    )
    assert res.status_code == 409


def test_profile_update_rejects_bad_avatar(client):
    token, _ = _register(client, "BadPic", "badpic@example.com")
    # non-data-url
    assert client.put(
        "/api/auth/me", json={"avatar": "not-a-data-url"}, headers=auth(token)
    ).status_code == 422
    # SVG is rejected (only raster images allowed)
    assert client.put(
        "/api/auth/me",
        json={"avatar": "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg'></svg>"},
        headers=auth(token),
    ).status_code == 422
    # empty body (no updatable fields) is a 422 as well
    assert client.put("/api/auth/me", json={}, headers=auth(token)).status_code == 422


def test_my_reviews(client, admin_token):
    product = client.post(
        "/api/products", json={"title": "My Reviews Product"}, headers=auth(admin_token)
    ).json()
    token, uid = _register(client, "Reviewer", "reviewer_mr@example.com")
    client.post(
        "/api/reviews",
        json={"product_id": product["id"], "user_id": uid, "rating": 5, "comment": "mine"},
        headers=auth(token),
    )
    mine = client.get("/api/auth/me/reviews", headers=auth(token))
    assert mine.status_code == 200
    assert any(
        it["product_title"] == "My Reviews Product" and it["comment"] == "mine"
        for it in mine.json()
    )


# -------------------------- admin: users --------------------------------


def test_admin_users_list_auth(client, admin_token):
    assert client.get("/api/admin/users").status_code == 401
    token, _ = _register(client, "NonAdminU", "nonadminu@example.com")
    assert client.get("/api/admin/users", headers=auth(token)).status_code == 403
    r = client.get("/api/admin/users", headers=auth(admin_token))
    assert r.status_code == 200
    assert any(u["email"] == "admintest@reviewdibo.com" for u in r.json())
    assert all("review_count" in u for u in r.json())


def test_admin_assign_roles(client, admin_token):
    _, uid = _register(client, "Promote", "promote@example.com")
    up = client.patch(f"/api/admin/users/{uid}", json={"role": "moderator"}, headers=auth(admin_token))
    assert up.status_code == 200 and up.json()["role"] == "moderator"
    up2 = client.patch(f"/api/admin/users/{uid}", json={"role": "admin"}, headers=auth(admin_token))
    assert up2.status_code == 200 and up2.json()["role"] == "admin"
    down = client.patch(f"/api/admin/users/{uid}", json={"role": "user"}, headers=auth(admin_token))
    assert down.status_code == 200 and down.json()["role"] == "user"
    # invalid role rejected; missing user -> 404
    assert client.patch(f"/api/admin/users/{uid}", json={"role": "superuser"}, headers=auth(admin_token)).status_code == 422
    assert client.patch("/api/admin/users/999999", json={"role": "admin"}, headers=auth(admin_token)).status_code == 404


def test_admin_cannot_demote_or_delete_self(client, admin_token):
    aid = _admin_id(client, admin_token)
    assert client.patch(f"/api/admin/users/{aid}", json={"role": "user"}, headers=auth(admin_token)).status_code == 403
    assert client.delete(f"/api/admin/users/{aid}", headers=auth(admin_token)).status_code == 403


def test_admin_delete_user_cascades(client, admin_token):
    product = client.post(
        "/api/products", json={"title": "Cascade User Product"}, headers=auth(admin_token)
    ).json()
    _, uid = _register(client, "Doomed", "doomed@example.com")
    client.post("/api/reviews", json={"product_id": product["id"], "user_id": uid, "rating": 4})
    assert client.delete(f"/api/admin/users/{uid}", headers=auth(admin_token)).status_code == 204
    detail = client.get(f"/api/products/{product['id']}").json()
    assert all(r["user_id"] != uid for r in detail["reviews"])
    assert client.delete("/api/admin/users/999999", headers=auth(admin_token)).status_code == 404


# -------------------------- password reset ------------------------------


def test_forgot_password_no_enumeration(client):
    _register(client, "Forgot", "forgot@example.com")
    r = client.post("/api/auth/forgot-password", json={"email": "forgot@example.com"})
    assert r.status_code == 200 and r.json()["reset_token"]  # dev returns token
    r2 = client.post("/api/auth/forgot-password", json={"email": "nobody-here@example.com"})
    assert r2.status_code == 200 and r2.json()["reset_token"] is None  # no enumeration


def test_reset_password_flow(client):
    _register(client, "Resetter", "resetter@example.com", password="oldpassword1")
    token = client.post(
        "/api/auth/forgot-password", json={"email": "resetter@example.com"}
    ).json()["reset_token"]
    assert token
    assert client.post(
        "/api/auth/reset-password", json={"token": token, "password": "newpassword1"}
    ).status_code == 204
    assert client.post(
        "/api/auth/login", data={"username": "resetter@example.com", "password": "oldpassword1"}
    ).status_code == 401
    assert client.post(
        "/api/auth/login", data={"username": "resetter@example.com", "password": "newpassword1"}
    ).status_code == 200


def test_reset_password_bad_token_and_weak(client):
    assert client.post(
        "/api/auth/reset-password", json={"token": "not.a.token", "password": "whatever1"}
    ).status_code == 400
    _register(client, "Weak", "weakreset@example.com")
    tok = client.post(
        "/api/auth/forgot-password", json={"email": "weakreset@example.com"}
    ).json()["reset_token"]
    assert client.post(
        "/api/auth/reset-password", json={"token": tok, "password": "short"}
    ).status_code == 422


# --- password-reset security: scoping, single-use, session invalidation --


def test_reset_token_is_not_a_session_token(client):
    _register(client, "Sec", "sec_reset@example.com")
    tok = client.post(
        "/api/auth/forgot-password", json={"email": "sec_reset@example.com"}
    ).json()["reset_token"]
    assert tok
    # a reset token must NOT authenticate normal endpoints
    assert client.get("/api/auth/me", headers=auth(tok)).status_code == 401


def test_reset_is_single_use_and_invalidates_sessions(client):
    session, _ = _register(client, "Inv", "inv_reset@example.com", password="oldpassword1")
    assert client.get("/api/auth/me", headers=auth(session)).status_code == 200

    tok = client.post(
        "/api/auth/forgot-password", json={"email": "inv_reset@example.com"}
    ).json()["reset_token"]
    assert client.post(
        "/api/auth/reset-password", json={"token": tok, "password": "newpassword1"}
    ).status_code == 204

    # the pre-reset session token is now invalid (token_version bumped)
    assert client.get("/api/auth/me", headers=auth(session)).status_code == 401
    # the reset token is single-use (its tv is now stale)
    assert client.post(
        "/api/auth/reset-password", json={"token": tok, "password": "another1"}
    ).status_code == 400

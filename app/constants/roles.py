"""Role-based access control: roles and the capabilities each one grants.

Permission checks throughout the app are expressed in terms of *capabilities*
(not role names), so adding a new role later is just one entry in
``ROLE_PERMISSIONS`` — endpoints don't change.
"""

# ---- Roles ----
ROLE_USER = "user"
ROLE_MODERATOR = "moderator"
ROLE_ADMIN = "admin"

ROLES: tuple[str, ...] = (ROLE_USER, ROLE_MODERATOR, ROLE_ADMIN)
# Roles an admin may assign to others.
ASSIGNABLE_ROLES: tuple[str, ...] = ROLES

# ---- Capabilities ----
PERM_MODERATE_REVIEWS = "moderate_reviews"
PERM_MANAGE_PRODUCTS = "manage_products"
PERM_MANAGE_USERS = "manage_users"
PERM_ASSIGN_ROLES = "assign_roles"

ROLE_PERMISSIONS: dict[str, set[str]] = {
    ROLE_USER: set(),
    ROLE_MODERATOR: {PERM_MODERATE_REVIEWS},
    ROLE_ADMIN: {
        PERM_MODERATE_REVIEWS,
        PERM_MANAGE_PRODUCTS,
        PERM_MANAGE_USERS,
        PERM_ASSIGN_ROLES,
    },
}


def role_has_permission(role: str, permission: str) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, set())

# Review Dibo — Backend API

REST API for the **Review Website Module**: browse products, read and submit
reviews, with JWT authentication, an admin moderation panel, and product
search/filter.

Built with **FastAPI · SQLAlchemy 2.0 · PostgreSQL · Pydantic v2**.

---

## Architecture

A layered, feature-modular structure. Every request flows in one direction:

```
app.py  ->  routes/index.py  ->  modules/<feature>/routes.py
        ->  modules/<feature>/controller.py  ->  services/<feature>/*.py
```

```
app/
├── app.py                  # FastAPI app: CORS, error handlers, router mount, health
├── config/
│   ├── config.py           # Settings (pydantic-settings, reads .env)
│   └── database.py         # Engine, SessionLocal, Base, get_db, init_db
├── constants/              # app_constants.py (rating bounds, prefixes), messages.py
├── middleware/
│   ├── auth.py             # JWT dependencies: get_current_user, require_admin
│   └── error_handlers.py   # Centralized exception -> JSON handlers
├── modules/                # One folder per feature; each has routes.py + controller.py
│   ├── products/           #   (+ models.py, schemas.py)
│   ├── reviews/
│   ├── users/
│   ├── auth/
│   └── admin/
├── routes/
│   └── index.py            # Aggregates every module router under /api
├── services/               # Business/data logic, mirrors modules/ (files < 500 LOC)
│   ├── products/  reviews/  users/  auth/  admin/
└── utils/                  # security.py (hash/JWT), exceptions.py, utils.py
seed.py                     # Admin + demo data
tests/                      # End-to-end smoke tests (pytest + SQLite)
```

**Layer responsibilities**
- **routes** — declare endpoints, dependencies (db, auth) and response models; nothing else.
- **controller** — orchestrate a request: call services, enforce ownership, shape the response.
- **services** — pure business/data logic and DB queries (the only layer that touches the ORM heavily).

---

## Tech stack

| Concern | Choice |
|---|---|
| Web framework / server | FastAPI + Uvicorn |
| ORM / DB | SQLAlchemy 2.0 + PostgreSQL (`psycopg2`) |
| Validation / settings | Pydantic v2 + pydantic-settings |
| Auth | JWT (`python-jose`) + bcrypt (`passlib`) |
| Tests | pytest + Starlette `TestClient` |

---

## Setup

### 1. Prerequisites
- Python 3.11+
- PostgreSQL 13+ (running locally or reachable via URL)

### 2. Create the virtualenv & install

```bash
python -m venv venv
# Windows (PowerShell):
venv\Scripts\Activate.ps1
# Windows (Git Bash):
source venv/Scripts/activate
# macOS / Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
```

Edit `.env` — at minimum set `DATABASE_URL` and a strong `SECRET_KEY`:

```
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/review_dibo
SECRET_KEY=<python -c "import secrets; print(secrets.token_urlsafe(48))">
PORT=8011
```

Create the database once (e.g. `createdb review_dibo`).

### 4. Create tables & seed demo data

```bash
python seed.py
```

This creates all tables (`init_db`) and inserts an admin account plus demo
products/users/reviews. Default admin: `admin@reviewdibo.com` / `admin12345`
(override via `SEED_ADMIN_*` in `.env`).

> The committed [`schema.sql`](./schema.sql) is the PostgreSQL DDL for the
> schema (the "database migration/schema" deliverable). You can also let
> `seed.py`/`init_db()` create the tables for you.

### 5. Run (port 8011)

```bash
python -m app.app
# or:
uvicorn app.app:app --reload --port 8011
```

- API root: <http://localhost:8011/>
- Health: <http://localhost:8011/health>
- **Swagger / OpenAPI docs: <http://localhost:8011/docs>** (ReDoc at `/redoc`)

---

## API overview

Base path: `/api`. Interactive docs at `/docs`.

### Products
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/products` | public | List products with `average_rating` + `review_count`. Query: `?search=`, `?min_rating=` |
| GET | `/api/products/{id}` | public | Product detail with nested `reviews` |
| POST | `/api/products` | admin | Create a product |
| DELETE | `/api/products/{id}` | admin | Delete a product (cascades reviews) |

### Reviews
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/reviews` | public | Create review — body `{product_id, user_id, rating, comment}` |
| PUT | `/api/reviews/{id}` | owner/admin | Update a review |
| DELETE | `/api/reviews/{id}` | owner/admin | Delete a review |

### Users
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/users` | public | Create/resolve a reviewer by `{name, email}` → `user_id` (201 new, 200 existing) |

### Auth
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/register` | public | Register → `{access_token, token_type, user}` |
| POST | `/api/auth/login` | public | **OAuth2 password form** (`username`=email, `password`) → `{access_token, token_type}` |
| GET | `/api/auth/me` | auth | Current user from the bearer token |
| PUT | `/api/auth/me` | auth | Update profile (name / email / avatar; changing email requires `current_password`) |
| GET | `/api/auth/me/reviews` | auth | Reviews authored by the current user |
| POST | `/api/auth/forgot-password` | public | Request a password reset (token emailed in prod) |
| POST | `/api/auth/reset-password` | public | Set a new password with a reset token (single-use) |

### Admin
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/admin/reviews` | admin | List all reviews (every status) |
| DELETE | `/api/admin/reviews/{id}` | admin | Delete any review (override) |
| GET | `/api/admin/users` | admin | List all users with review counts |
| GET | `/api/admin/users/{id}` | admin | A user's profile + their reviews |
| PATCH | `/api/admin/users/{id}` | admin | Assign a role (`user` / `moderator` / `admin`) |
| DELETE | `/api/admin/users/{id}` | admin | Delete a user (cascades reviews) |

### Moderation (moderator or admin)
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/moderation/reviews?status=` | moderator | Queue filtered by `pending` / `approved` / `rejected` / `all` |
| GET | `/api/moderation/pending-count` | moderator | Count of reviews awaiting moderation |
| PATCH | `/api/moderation/reviews/{id}` | moderator | Approve or reject a review |

> **Review moderation:** members' reviews are auto-approved (configurable via
> `REVIEW_AUTO_APPROVE`); guest reviews are held as `pending` until a moderator
> approves them. Only `approved` reviews count toward public ratings/listings.

### Authentication notes
- Send `Authorization: Bearer <token>` on protected routes.
- `/api/auth/login` uses the OAuth2 password flow (form-encoded), so Swagger's
  **Authorize** button works directly — log in there to call protected endpoints.
- **Review creation** takes an explicit `user_id` in the body (resolved
  client-side via `POST /api/users` or the logged-in user), per the brief.
- **Edit/delete** a review requires being its author or an admin.

---

## Data model

| Model | Fields |
|---|---|
| **User** | `id`, `name`, `email` (unique), `avatar` (nullable), `role` (`user`/`moderator`/`admin`), `password_hash` (nullable), `token_version`, `created_at` |
| **Product** | `id`, `title`, `description`, `image_url`, `created_at` |
| **Review** | `id`, `product_id` →Product, `user_id` →User, `rating` (1–5), `comment`, `images`, `status` (`pending`/`approved`/`rejected`), `rejection_reason`, `moderated_at`, `created_at` |

`average_rating` and `review_count` are computed on demand from the reviews
table (never stored), so they can't go stale. Deleting a product or user
cascades to its reviews.

---

## Tests

```bash
pytest -q
```

The suite spins up the app against a throwaway SQLite database and exercises
the full surface: product CRUD, review CRUD + validation, FK checks, cascade
delete, auth (register/login/me), ownership enforcement, and admin moderation.

---

## Environment variables

| Var | Default | Purpose |
|---|---|---|
| `APP_ENV` | `development` | Environment name; any non-dev value enforces a strong `SECRET_KEY` |
| `DATABASE_URL` | `postgresql+psycopg2://…/review_dibo` | SQLAlchemy connection URL |
| `SECRET_KEY` | _change me_ | JWT signing key (must be ≥32 chars in production) |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | Token lifetime |
| `REVIEW_AUTO_APPROVE` | `true` | Auto-approve member reviews (guests always pending) |
| `AUTH_DEV_RETURN_RESET_TOKEN` | `false` | Dev-only: return the reset token in the API response — never enable in prod |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated allowed origins (set to your deployed frontend URL) |
| `HOST` / `PORT` | `0.0.0.0` / `8011` | Bind address |
| `SEED_ADMIN_NAME/EMAIL/PASSWORD` | `Admin` / `admin@reviewdibo.com` / `admin12345` | Seed admin |

See [`.env.example`](./.env.example).

---

## Deployment & keep-alive

Deploy on **Render** (or any host). Set `APP_ENV=production`, a strong `SECRET_KEY`
(≥32 chars), `DATABASE_URL` (a managed Postgres), and `CORS_ORIGINS=<your Vercel URL>`.
Start command:

```bash
uvicorn app.app:app --host 0.0.0.0 --port $PORT
```

Render's **free** tier spins the service down after ~15 min idle (≈50s cold start
on the next hit). Keep it warm with a free **uptime monitor** that pings `/health`
every ~5 min — create an HTTP(s) monitor on
[UptimeRobot](https://uptimerobot.com) or [cron-job.org](https://cron-job.org)
pointing at `https://<your-app>/health`.

> A self-ping from inside the app can't wake it once asleep (the process is gone),
> so the pinger must be external.

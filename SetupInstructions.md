# Setup Instructions — Review Dibo **Backend** (FastAPI API)

A step-by-step guide to run the backend locally. Stack: **FastAPI · SQLAlchemy 2.0 ·
PostgreSQL · Pydantic v2 · JWT auth**. Default port: **8011**.

> Frontend setup lives in the frontend repo's `SetupInstructions.md`.

---

## 1. Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Python | **3.11+** | `python --version` |
| PostgreSQL | **13+** | running locally or reachable via a connection URL |
| pip / venv | bundled with Python | |

---

## 2. Get the code & create a virtual environment

```bash
git clone https://github.com/nahiyananwar/review_dibo.git
cd review_dibo

python -m venv venv
```

Activate the environment:

```bash
# Windows (PowerShell)
venv\Scripts\Activate.ps1

# Windows (Git Bash)
source venv/Scripts/activate

# macOS / Linux
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 3. Configure environment variables

Copy the example file and edit it:

```bash
cp .env.example .env
```

At minimum set **`DATABASE_URL`** and a strong **`SECRET_KEY`**:

```ini
# .env
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/review_dibo
SECRET_KEY=<paste a long random string>
PORT=8011
```

Generate a strong secret:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

> In production (`APP_ENV` set to anything other than `development`) the app
> **refuses to start** unless `SECRET_KEY` is at least 32 characters.

Full reference of every variable is in [`.env.example`](./.env.example) and the
README's *Environment variables* table.

---

## 4. Create the PostgreSQL database

Create an empty database once (the app creates the tables for you in the next step):

```bash
# using the Postgres CLI tools
createdb review_dibo
# …or from psql:
#   CREATE DATABASE review_dibo;
```

Make sure the credentials/host/port in `DATABASE_URL` match your Postgres install.

---

## 5. Create tables & load demo data

```bash
python seed.py
```

This runs `init_db()` (creates all tables from the SQLAlchemy models) and inserts an
admin account plus demo products, users, and reviews.

To wipe everything and start fresh (e.g. after pulling model changes), **stop the
server first**, then:

```bash
python reset_db.py
```

`reset_db.py` drops all tables and re-runs the seed — use it if you ever see a
`column ... does not exist` / schema-mismatch error.

> The committed [`schema.sql`](./schema.sql) is the raw PostgreSQL DDL, provided as
> the "database migration/schema" deliverable. You don't need to run it manually —
> `seed.py` builds the schema from the models.

---

## 6. Run the API

```bash
python -m app.app
# …or, with autoreload:
uvicorn app.app:app --reload --port 8011
```

Verify it's up:

| URL | What you should see |
|---|---|
| <http://localhost:8011/> | `{"message": "Review Dibo API is running", "docs": "/docs"}` |
| <http://localhost:8011/health> | `{"status": "ok"}` |
| <http://localhost:8011/docs> | **Swagger / OpenAPI** interactive docs (ReDoc at `/redoc`) |

---

## 7. Demo accounts (after seeding)

| Role | Email | Password |
|---|---|---|
| Admin | `admin@reviewdibo.com` | `admin12345` |
| Moderator | `moderator@reviewdibo.com` | `moderator12345` |

(Override the admin via `SEED_ADMIN_*` in `.env`.)

Log in from Swagger with the **Authorize** button (`/api/auth/login` uses the OAuth2
password flow — `username` = email) to call protected endpoints.

---

## 8. Run the tests (optional)

```bash
pytest -q
```

The suite runs the full app against a throwaway SQLite database — no Postgres needed.

---

## 9. Connect the frontend

The frontend expects this API at `NEXT_PUBLIC_API_BASE_URL` (default
`http://localhost:8011`). For the browser app to call it, this backend's
**`CORS_ORIGINS`** must include the frontend origin:

```ini
CORS_ORIGINS=http://localhost:3000
```

(Comma-separate multiple origins; add your deployed Vercel URL in production.)

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `column "..." does not exist` / `no such column` on seed | Stale schema — run `python reset_db.py`. |
| `connection refused` / can't reach DB | Postgres isn't running, or `DATABASE_URL` host/port/creds are wrong. |
| App won't boot: *SECRET_KEY too short* | Set a `SECRET_KEY` ≥ 32 chars (see step 3), or keep `APP_ENV=development`. |
| `Address already in use` on :8011 | Another process holds the port — stop it or set a different `PORT`. |
| Frontend shows a load error | This API isn't running, or its URL/`CORS_ORIGINS` don't match the frontend. |

---

## Deployment (Render) — quick reference

A [`render.yaml`](./render.yaml) blueprint is included (provisions the web service +
a free Postgres and wires `DATABASE_URL`). After the first deploy, set
`CORS_ORIGINS` to your Vercel URL and run `python seed.py` once. Keep the free
instance warm with an external uptime monitor pinging `/health`. See the README's
*Deployment & keep-alive* section for details.

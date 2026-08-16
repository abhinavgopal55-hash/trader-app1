# Panchayat Trader Survey (Python + PostgreSQL)

A rebuild of the Panchayat Trader Survey app using **FastAPI** (Python) and
**PostgreSQL** instead of Google Apps Script + Sheets. Same features:
new trader survey, register with search, view/edit/delete, dashboard with
ward-wise counts, and English/Malayalam language toggle.

## Project structure

```
panchayat-trader-app/
├── app/
│   ├── main.py          # FastAPI routes
│   ├── models.py        # SQLAlchemy Trader model
│   ├── database.py      # DB connection/session setup
│   ├── i18n.py           # English/Malayalam text
│   ├── templates/        # Jinja2 HTML templates
│   └── static/style.css
├── requirements.txt
├── render.yaml           # One-click Render deployment blueprint
└── .env.example
```

## Run locally

1. Install PostgreSQL locally (or use a free hosted instance — see below),
   and create a database, e.g. `traders`.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and set your `DATABASE_URL`:
   ```
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/traders
   ```
4. Run the server:
   ```bash
   uvicorn app.main:app --reload
   ```
5. Open `http://localhost:8000`

Tables are created automatically on first run — no manual migration needed.

## Deploy to Render (free tier)

Render can host both the web app and a managed PostgreSQL database for free.

1. Push this folder to a GitHub repository.
2. Go to [render.com](https://render.com) → **New → Blueprint**.
3. Connect your repo. Render will detect `render.yaml` and create:
   - A free PostgreSQL database (`panchayat-traders-db`)
   - A free web service (`panchayat-trader-survey`) wired to that database
     automatically via the `DATABASE_URL` environment variable.
4. Click **Apply**. First deploy takes a few minutes.
5. Once live, Render gives you a URL like:
   `https://panchayat-trader-survey.onrender.com`

That's your permanent app URL — share it directly, no more `/exec` links
or "refused to connect" issues.

**Note on Render's free tier:** free web services spin down after ~15 minutes
of inactivity and take ~30–50 seconds to wake up on the next request. If you
need it always-instant, upgrade the web service to the $7/month "Starter"
plan (the free database is fine to keep either way, up to 1GB).

## Deploy elsewhere

This is a standard FastAPI app, so it also runs as-is on Railway, Fly.io,
Heroku, or any VPS — just set `DATABASE_URL` and run:
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Migrating existing data later

If you ever want to import your old Google Sheet rows, export the sheet as
CSV and load it with a short script using `psycopg2` or `pandas.to_sql()`
against the `traders` table — happy to write that script when you're ready.

# WorkCafe Pune

WorkCafe Pune is a Flask directory for finding cafes around Pune that may suit a work or study session. Visitors can browse published cafes, view details such as area, price level, Wi-Fi and power outlets, and explore cafes by area. The home page features up to three recently created published cafes. A private admin dashboard lets staff manage listings and publish or unpublish them.

## Features

- Public home page, cafe directory, area pages, cafe details, and About page
- Admin login and dashboard for creating, editing, and publishing cafe listings
- Cafe image uploads to Supabase Storage
- Responsive Bootstrap layout with project styles in `app/static/css/style.css`
- SQLite by default, with PostgreSQL supported through `DATABASE_URL`

## Requirements

- Python 3.12 or later
- [uv](https://docs.astral.sh/uv/) for dependency and environment management
- Supabase project credentials to upload cafe images

## Setup

From the project directory, install dependencies:

```bash
uv sync
```

Create a `.env` file in the project root. For local development, the database defaults to `instance/workcafe.db`, so `DATABASE_URL` can be omitted.

```dotenv
SECRET_KEY=replace-with-a-long-random-secret
# Optional PostgreSQL connection string:
# DATABASE_URL=postgresql://user:password@host:5432/database

# Required for cafe image uploads:
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SECRET_KEY=your-supabase-secret-key
```

The app uses the Supabase Storage bucket named `cafe-images`. Create that bucket in your Supabase project and configure its public access if listing images should be visible to visitors.

Apply database migrations:

```bash
uv run flask --app run.py db upgrade
```

Optionally add candidate areas and draft cafe listings:

```bash
uv run python seed_python.py
```

Seeded listings are drafts with unverified details. Review and update each listing before publishing it.

Create the first administrator account:

```bash
uv run python create_admin.py
```

Start the development server:

```bash
uv run python run.py
```

Open <http://127.0.0.1:5000/> for the public site and <http://127.0.0.1:5000/admin/> for the admin dashboard.

## Configuration

| Variable | Purpose |
| --- | --- |
| `SECRET_KEY` | Flask session and CSRF signing key. Set a secure value outside local development. |
| `DATABASE_URL` | Optional database URL. Defaults to SQLite at `instance/workcafe.db`. PostgreSQL URLs are supported. |
| `SUPABASE_URL` | Supabase project URL used for image storage. |
| `SUPABASE_SECRET_KEY` | Supabase secret key used by the server for image uploads and deletion. Keep it private. |

Cafe images accept JPG, PNG, and WEBP formats, with a maximum request size of 5 MB.

## Project structure

```text
app/
  admin/          Admin routes and forms
  public/         Public directory routes
  static/         CSS, JavaScript, and local upload assets
  templates/      Jinja templates
  models.py       Database models
migrations/       Alembic database migrations
create_admin.py   Interactive initial admin setup
seed_python.py   Adds candidate areas and draft listings
run.py            Flask application entry point
```

# SusDevOS — VS Code Setup Guide

A step-by-step walkthrough to go from a fresh clone to a fully running local dev environment.

---

## Prerequisites

Install these before opening VS Code:

| Tool | Version | Download |
|---|---|---|
| Python | 3.12+ | https://www.python.org/downloads/ |
| Node.js | 20 LTS | https://nodejs.org/ |
| Docker Desktop | latest | https://www.docker.com/products/docker-desktop |
| Git | any | https://git-scm.com/ |
| VS Code | latest | https://code.visualstudio.com/ |

Verify with:

```bash
python --version    # Python 3.12.x
node --version      # v20.x.x
docker --version    # Docker version 27.x
```

---

## Step 1 — Open the workspace

1. Open VS Code.
2. **File → Open Folder** → select the `SusDevOS/` root folder.
3. VS Code will prompt *"Do you want to install the recommended extensions?"* — click **Install All**.

If the prompt doesn't appear: open the Extensions panel (`Ctrl+Shift+X` / `Cmd+Shift+X`), type `@recommended`, install everything listed.

---

## Step 2 — Create the Python virtual environment

Open the integrated terminal (`Ctrl+\`` / `Cmd+\``) and run:

```bash
cd backend
python -m venv .venv
```

Activate it:

```bash
# macOS / Linux
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Windows (Command Prompt)
.venv\Scripts\activate.bat
```

You should see `(.venv)` in your prompt.

Install dependencies:

```bash
pip install -r requirements/local.txt
```

> **VS Code Python interpreter**: press `Ctrl+Shift+P` → *Python: Select Interpreter* → choose the `.venv` in `backend/`. The `.vscode/settings.json` already points there, so this may resolve automatically.

---

## Step 3 — Configure environment variables

### Backend

```bash
cp backend/.env.example backend/.env
```

Open `backend/.env` and fill in:

```
SECRET_KEY=any-random-string-50-chars     # python -c "import secrets; print(secrets.token_hex(32))"
DATABASE_URL=postgis://susdевos:susdевos@localhost:5432/susdевos
REDIS_URL=redis://localhost:6379/0
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
```

Everything else in `.env.example` can stay as-is for local development.

### Frontend

```bash
cp frontend/.env.example frontend/.env.local
```

The default value (`NEXT_PUBLIC_API_URL=http://localhost:8000`) works out of the box.

---

## Step 4 — Start the infrastructure with Docker

Make sure Docker Desktop is running, then:

```bash
docker compose up -d db redis minio
```

This starts only the infrastructure services (PostgreSQL + PostGIS, Redis, MinIO) — you run Django and Next.js directly in VS Code for a better debugging experience.

Verify they're healthy:

```bash
docker compose ps
```

All three should show `healthy` or `running`.

---

## Step 5 — Run database migrations

In the backend terminal (with `.venv` active):

```bash
cd backend
python manage.py migrate
```

You should see all migrations applied. Then create a superuser:

```bash
python manage.py createsuperuser
```

---

## Step 6 — Start the Django dev server

**Option A — from the terminal:**

```bash
cd backend
python manage.py runserver
```

**Option B — with the VS Code debugger (recommended):**

1. Switch to the **Run and Debug** panel (`Ctrl+Shift+D` / `Cmd+Shift+D`).
2. Select **Django: runserver** from the dropdown.
3. Press **F5**.

You can now set breakpoints anywhere in the Django code — they will pause execution when hit.

Django is now at **http://localhost:8000**
Admin panel: **http://localhost:8000/admin/**
OpenAPI schema: **http://localhost:8000/api/schema/**
Swagger UI: **http://localhost:8000/api/schema/swagger-ui/**

---

## Step 7 — Start the Next.js dev server

Open a **second terminal tab** in VS Code:

```bash
cd frontend
npm install
npm run dev
```

Frontend is now at **http://localhost:3000**

---

## Step 8 — (Optional) Start a Celery worker

Open a **third terminal tab**:

```bash
cd backend
source .venv/bin/activate
celery -A config.celery worker -Q default -c 2 --loglevel=info
```

Only needed if you're developing features that use background tasks.

---

## Step 9 — Generate TypeScript API client

Whenever the Django API changes, regenerate the orval client:

```bash
# Ensure Django is running first (Step 6)
cd frontend
npx orval
```

This writes typed hooks into `frontend/src/lib/api/` and types into `frontend/src/types/api/`.

---

## Daily workflow

```
Terminal 1 (backend):   python manage.py runserver   # or F5 in debugger
Terminal 2 (frontend):  npm run dev
Terminal 3 (optional):  celery -A config.celery worker -Q default
```

Stop everything at end of day:

```bash
docker compose stop
```

---

## Useful commands

```bash
# Create a new migration after editing models
python manage.py makemigrations

# Open Django shell
python manage.py shell

# Run backend tests
cd backend && pytest

# Lint + format Python
ruff check . --fix
ruff format .

# Type-check Python
mypy .

# Lint frontend
cd frontend && npm run lint

# Access MinIO console (bucket management)
open http://localhost:9001   # user: minioadmin  pass: minioadmin
```

---

## Troubleshooting

**`postgis` extension not found**
```bash
docker compose exec db psql -U susdевos -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

**`ModuleNotFoundError: No module named 'config'`**
Make sure you're running commands from inside the `backend/` directory, not the repo root.

**Port 8000 already in use**
```bash
lsof -i :8000 | grep LISTEN   # macOS/Linux
# then kill the PID shown
```

**Next.js can't reach Django (`ECONNREFUSED`)**
Check that Django is running and that `NEXT_PUBLIC_API_URL=http://localhost:8000` is in `frontend/.env.local`.

**Orval generation fails**
The Django server must be running so orval can fetch `http://localhost:8000/api/schema/`. Start Django first, then run `npx orval`.

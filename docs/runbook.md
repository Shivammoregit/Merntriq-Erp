# Mentriq360 ERP Runbook

## 1. Prerequisites

- Python 3.12+
- Node.js 20+
- `pnpm` 10+
- PostgreSQL 15+ for production-style local runs
- Redis 7+ for cache and future async jobs

## 2. Backend Setup

PowerShell from the repository root:

```powershell
Copy-Item .env.example .env
python -m venv .backend-venv
.\.backend-venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

For fast local execution without PostgreSQL:

```powershell
$env:DJANGO_USE_SQLITE='True'
Set-Location backend
..\.backend-venv\Scripts\python.exe manage.py migrate
..\.backend-venv\Scripts\python.exe manage.py seed_demo
..\.backend-venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
```

For PostgreSQL and Redis:

```powershell
docker compose up postgres redis
```

Then run migrations and start Django with the same commands without `DJANGO_USE_SQLITE=True`.

## 3. Frontend Setup

```powershell
Set-Location web
pnpm install
pnpm dev
```

Open `http://localhost:3000`.

## 4. Demo Data

Run:

```powershell
Set-Location backend
$env:DJANGO_USE_SQLITE='True'
..\.backend-venv\Scripts\python.exe manage.py seed_demo
```

Credentials:

- `super.admin / Mentriq@123` - all campuses and support issue queue
- `it.admin / Mentriq@123` - Main Campus IT admin
- `north.admin / Mentriq@123` - North Campus IT admin
- `academic.admin / Mentriq@123` - academic records and exam workflows
- `finance.admin / Mentriq@123` - fees and payment workflows
- `teacher.meera / Mentriq@123` - assigned class access
- `teacher.dev / Mentriq@123` - North Campus assigned class access
- `student.anaya / Mentriq@123` - own profile only

## 5. Module Execution Order

1. Login with an admin user.
2. Create campus and academic session records.
3. Create sections and assign class teachers.
4. Add students and guardian contact details.
5. Login as teacher and mark attendance.
6. Login as admin and assign fees or record payments.
7. Login as student and verify profile, attendance, fees, and receipts.
8. Login as admin and review reports and audit events.

## Campus Database Operation

Set `CAMPUS_DATABASE_URLS` in `.env` when campuses must use separate databases:

```dotenv
CAMPUS_DATABASE_URLS=M360-MAIN=postgres://user:pass@host:5432/mentriq360_main;M360-NORTH=postgres://user:pass@host:5432/mentriq360_north
```

Then run:

```powershell
Set-Location backend
..\.backend-venv\Scripts\python.exe manage.py migrate_campus_databases
```

Users enter the configured campus code on login to route the session to that campus database.

## 6. Verification

Backend:

```powershell
Set-Location backend
$env:DJANGO_USE_SQLITE='True'
$env:DJANGO_ALLOWED_HOSTS='testserver,localhost,127.0.0.1'
..\.backend-venv\Scripts\python.exe manage.py check
..\.backend-venv\Scripts\python.exe manage.py test
```

Frontend:

```powershell
Set-Location web
pnpm lint
pnpm build
```

## 7. Deployment Checklist

- Set a strong `DJANGO_SECRET_KEY`.
- Set `DJANGO_DEBUG=False`.
- Use PostgreSQL, not SQLite.
- Set production `DJANGO_ALLOWED_HOSTS`.
- Set production `DJANGO_CORS_ALLOWED_ORIGINS`.
- Serve the frontend over HTTPS.
- Use `config.settings.production`.
- Run `python manage.py migrate`.
- Create a real super admin and remove demo users if seeded.

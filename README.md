# Mentriq360 Campus ERP

Mentriq360 is a role-based campus ERP built from the supplied ER/user-flow diagram. It covers authentication, admin setup, student records, teacher attendance, fee assignment, payment entry, reporting, audit logs, student visibility, and optional campus-isolated databases.

## Stack

- `Next.js 16 + TypeScript + Tailwind CSS` for the responsive web app
- `Django 5.2 + Django REST Framework` for the API
- `SimpleJWT` for access and refresh tokens
- `PostgreSQL` for production data
- `SQLite` for quick local execution
- `Redis` for shared cache, rate limits, and future queues/notifications

## Implemented Modules

- Authentication: JWT login, refresh, current user, role-aware dashboard routing
- User management: admin-managed users for admins, teachers, finance teams, and students
- Academic setup: campuses, academic sessions, class sections, class teachers
- Student module: admission records, section assignment, status tracking
- Attendance: teacher section roster, bulk attendance upsert, and student read-only reports
- Fees and payments: fee assignment, payment capture, automatic paid/partial/pending/overdue status refresh
- Reports: dashboard summary, attendance by section, fee status, recent payments
- Notifications and support: admin announcements, role-visible alerts, and user support tickets for super admins
- Campus360 modules: a role-aware suite view covering admissions, SIS, staff, fees, exams, certificates, homework, timetable, library, transport, hostel, inventory, communication, online learning, analytics, director dashboard, and security
- Multi-tenant database routing: optional `X-Campus-Code` tenant context routes each configured campus to its own database alias
- Security audit: login and write-action audit events
- Production controls: installable web app manifest, session idle expiry, request timeouts, global error handling, Redis-backed throttling support, and scoped hardware attendance throttles

## Local Run

PowerShell from the repository root:

```powershell
Copy-Item .env.example .env

python -m venv .backend-venv
.\.backend-venv\Scripts\python.exe -m pip install -r backend\requirements.txt

$env:DJANGO_USE_SQLITE='True'
Set-Location backend
..\.backend-venv\Scripts\python.exe manage.py migrate
..\.backend-venv\Scripts\python.exe manage.py createsuperuser
..\.backend-venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
```

In another terminal:

```powershell
Set-Location web
pnpm install
pnpm dev
```

Open:

- Web app: `http://localhost:3000`
- API health: `http://localhost:8000/api/v1/health/`
- API docs: `http://localhost:8000/api/docs/`
- Django admin: `http://localhost:8000/admin/`

## Authorized Accounts

No default users or passwords are shipped with the ERP. Create the first Super Admin with `python manage.py createsuperuser`, then create School Admin, Account, Teacher, and Student users from the protected admin workspace.

## Campus Databases

Set `CAMPUS_DATABASE_URLS` to route a campus code to a separate database:

```dotenv
CAMPUS_DATABASE_URLS=M360-MAIN=postgres://user:pass@host:5432/mentriq360_main;M360-NORTH=postgres://user:pass@host:5432/mentriq360_north
```

Run tenant migrations with:

```powershell
Set-Location backend
..\.backend-venv\Scripts\python.exe manage.py migrate_campus_databases
```

Campus database routing is controlled by the stored tenant campus context and the `X-Campus-Code` API header. The login form uses the default database and no longer asks users for a campus code.

For tenant subdomains, configure the same suffix on the backend and frontend. For example, with `north.schools.example.com`, set:

```dotenv
DJANGO_TENANT_DOMAIN_SUFFIX=schools.example.com
NEXT_PUBLIC_TENANT_DOMAIN_SUFFIX=schools.example.com
```

You can also set `NEXT_PUBLIC_DEFAULT_TENANT_CODE` for a single-campus deployment. Leave it empty for central deployments.

For production web deployments, set `NEXT_PUBLIC_API_BASE_URL` to the deployed Django API URL, for example:

```dotenv
NEXT_PUBLIC_API_BASE_URL=https://your-backend-domain.vercel.app/api/v1
```

## Verification

Backend checks:

```powershell
Set-Location backend
$env:DJANGO_USE_SQLITE='True'
..\.backend-venv\Scripts\python.exe manage.py check
..\.backend-venv\Scripts\python.exe manage.py test
```

Frontend checks:

```powershell
Set-Location web
pnpm lint
pnpm build
```

## Capacitor Android App

Capacitor is installed in the `web` workspace with an Android project at `web/android`.

```powershell
Set-Location web
pnpm build:mobile
pnpm cap:open:android
```

`pnpm build:mobile` runs a static Next export into `web/out` and syncs it into Android. Android Studio is required to build and sign APK/AAB packages.

For command-line Android builds on Windows, use Android Studio's bundled JDK and the installed SDK:

```powershell
$env:JAVA_HOME='C:\Program Files\Android\Android Studio\jbr'
$env:ANDROID_HOME="$env:LOCALAPPDATA\Android\Sdk"
$env:ANDROID_SDK_ROOT=$env:ANDROID_HOME
$env:PATH="$env:JAVA_HOME\bin;$env:ANDROID_HOME\platform-tools;$env:ANDROID_HOME\cmdline-tools\latest\bin;$env:ANDROID_HOME\emulator;$env:PATH"

Set-Location web\android
.\gradlew.bat assembleDebug
```

The debug APK is written to `web/android/app/build/outputs/apk/debug/app-debug.apk`.

## Docker Deployment Preview

Docker Desktop is supported through the included Compose file:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

The Compose stack starts PostgreSQL, Redis, the Django API, and the web app.

## Documentation

- [Architecture](docs/architecture.md)
- [Runbook](docs/runbook.md)
- [Module and phase plan](docs/module-plan.md)
- [API reference](docs/api.md)
- [Security baseline](docs/security.md)
- [Production readiness](docs/production-readiness.md)
- [Campus360 access matrix](docs/campus360-access-matrix.md)

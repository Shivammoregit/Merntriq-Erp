# Mentriq360 School ERP

Mentriq360 is a role-based, multi-tenant School ERP covering Super Admin school setup, School Admin core modules, finance and payment workflows, Teacher panel, Student portal, real-time academic/finance events, AI-assisted tools, communication settings, attendance hardware readiness, production deployment controls, client handover documentation, and enterprise SaaS management.

## Stack

- `Next.js 16 + TypeScript + Tailwind CSS` for the responsive web app
- `Django 5.2 + Django REST Framework` for the API
- `SimpleJWT` for access and refresh tokens
- `PostgreSQL` for production data
- `SQLite` for quick local execution
- `Redis` for shared cache, rate limits, and future queues/notifications

## Implemented Modules

- Authentication: JWT login, refresh, current user, role-aware dashboard routing
- User management: admin-managed users for School Admin, Account, Teacher, and Student roles
- Academic setup: campuses, academic sessions, class sections, class teachers
- Student module: admission records, section assignment, status tracking
- Attendance: teacher section roster, bulk attendance upsert, and student read-only reports
- Fees and payments: fee assignment, payment capture, automatic paid/partial/pending/overdue status refresh
- Reports: dashboard summary, attendance by section, fee status, recent payments
- Notifications and support: admin announcements, role-visible alerts, and user support tickets for super admins
- Role dashboards: protected dashboards for Super Admin, School Admin, Account, Teacher, and Student users
- Multi-tenant database routing: optional `X-Campus-Code` tenant context routes each configured campus to its own database alias
- Security audit: login and write-action audit events
- Production controls: installable web app manifest, session idle expiry, request timeouts, global error handling, Redis-backed throttling support, and scoped hardware attendance throttles
- Client handover: removable demo school seed command, user manual, permission matrix, deployment guide, backup/recovery guide, maintenance guide, database schema summary, test report, and known limitations
- Enterprise SaaS: Basic/Standard/Premium/Enterprise plans, school subscription billing, GST invoices, white-label controls, SaaS analytics, compliance logs, secure API tokens, backup jobs, queue jobs, health snapshots, and enterprise monitoring
- Commercial ecosystem: admissions, transport drivers, digital library, inventory assets, school website content, mobile bootstrap, push notifications, marketplace plugins, GST ledger reports, report builder, security center, and production audit

## Local Run

PowerShell from the repository root:

```powershell
Copy-Item .env.example .env

python -m venv .backend-venv
.\.backend-venv\Scripts\python.exe -m pip install -r backend\requirements.txt

$env:DJANGO_USE_SQLITE='True'
Set-Location backend
..\.backend-venv\Scripts\python.exe manage.py migrate
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

Migrations seed one permanent Super Admin account from `.env`:

- Username: `MENTRIQ_SUPER_ADMIN_USERNAME` (default `super.admin`)
- Password: `MENTRIQ_SUPER_ADMIN_PASSWORD` (default `SuperAdmin@12345`)

The seeded Super Admin is always active, staff, and superuser. The API and admin protections block deleting or disabling Super Admin accounts. Create School Admin, Account, Teacher, and Student users from the protected dashboard.

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
NEXT_PUBLIC_SITE_URL=https://mentriq-erp.vercel.app
NEXT_PUBLIC_API_BASE_URL=https://backend-nu-self-91.vercel.app/api/v1
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

## Demo School

Create a removable demo school for client walkthroughs:

```powershell
Set-Location backend
python manage.py seed_demo_school
```

Default demo users use password `Demo@12345`. Remove the demo school and demo users with:

```powershell
python manage.py seed_demo_school --remove
```

The command refuses to remove a school unless it has the demo marker. See [Demo Data Guide](docs/demo-data.md).

## Enterprise SaaS

Phase 9 adds commercial SaaS management for Super Admins. Default subscription plans are seeded by migration and can be refreshed with:

```powershell
Set-Location backend
python manage.py enterprise_maintenance --seed-plans
```

Run all subscription expiry, backup queueing, and health snapshot maintenance tasks with:

```powershell
python manage.py enterprise_maintenance --all
```

Use `Super Admin > Enterprise SaaS` in the web app to manage plan limits, school subscriptions, invoices, payments, white-label branding, analytics, compliance logs, backup/restore evidence, secure API tokens, queue jobs, and monitoring. See [Enterprise SaaS Guide](docs/enterprise-saas.md).

## Commercial Ecosystem

Phase 10 adds the final commercial ecosystem surface for Super Admins:

- Public admissions with tracking, document upload, fee status, pipeline review, and admit-to-student conversion
- Transport, digital library, inventory/assets, school website, mobile bootstrap, push notification, marketplace, GST/reporting, security center, and production audit APIs
- `Super Admin > Commercial Ecosystem` web panel for school-scoped launch operations

See [Phase 10 Commercial Ecosystem](docs/phase10-commercial-ecosystem.md).

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
- [Client handover](docs/client-handover.md)
- [User manual](docs/user-manual.md)
- [Demo data guide](docs/demo-data.md)
- [Permission matrix](docs/permission-matrix.md)
- [Deployment guide](docs/deployment-guide.md)
- [Backup and recovery](docs/backup-recovery.md)
- [Maintenance guide](docs/maintenance.md)
- [Database schema](docs/database-schema.md)
- [Final test report](docs/test-report.md)
- [Phase 10 Commercial Ecosystem](docs/phase10-commercial-ecosystem.md)
- [Known limitations](docs/known-limitations.md)

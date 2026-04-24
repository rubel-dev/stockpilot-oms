# StockPilot OMS

Multi-Warehouse Inventory, Order, and Supplier Management Platform

StockPilot OMS is a production-style full-stack portfolio project built to look and feel like a small-to-mid-market B2B SaaS operations product. It focuses on multi-warehouse inventory control, stock movement safety, supplier relationships, order lifecycle management, alerts, auditability, and analytics.

## Project Overview

This project demonstrates:

- Next.js + TypeScript frontend architecture
- FastAPI backend structure
- PostgreSQL with raw SQL only
- transaction-safe inventory and order logic
- Dockerized local development
- multi-page product design, not a single-dashboard demo
- maintainable repository/service separation
- portfolio-quality documentation and project organization

## Why A Hiring Manager Should Care

This repository is strongest when reviewed as a systems project, not a UI-only demo.

It intentionally exercises the kind of work that separates a promising junior engineer from someone who only knows tutorial CRUD:

- transactional inventory flows without an ORM
- workspace-safe multi-tenant data access
- stock reservation and overselling prevention
- modular backend boundaries that are easy to extend
- a real admin product shell instead of a single dashboard screenshot
- documentation that explains domain rules and tradeoffs clearly

That combination gives reviewers multiple credible signals at once: backend judgment, SQL fluency, frontend product sense, and the ability to present engineering work cleanly.

The goal is not just to display forms and tables. The project is intentionally shaped around real operational concerns:

- workspace isolation
- stock reservations
- overselling prevention
- low-stock alerting
- purchase order restocks
- audit logs
- analytics built from joins, aggregations, and CTEs

## Architecture Summary

### Frontend

- `frontend/app`: Next.js App Router pages
- `frontend/components`: shared UI primitives and layout
- `frontend/features`: screen-level feature modules
- `frontend/lib`: API client, formatting, auth/session helpers

The frontend uses a protected dashboard shell with a reusable navigation system, page headers, premium table layouts, drawers for operational actions, and chart components for analytics.

### Backend

- `backend/app/api`: FastAPI routes and dependencies
- `backend/app/core`: config, auth, pagination, exceptions, error handlers
- `backend/app/db`: connection pool utilities
- `backend/app/repositories`: raw SQL data access only
- `backend/app/services`: business logic and transaction orchestration
- `backend/app/schemas`: typed request/response models
- `backend/app/tests`: unit tests for key backend logic

### Database

- PostgreSQL only
- manual SQL migrations in `backend/sql`
- no ORM
- no Alembic
- parameterized queries only

## Tech Stack

### Frontend

- Next.js
- TypeScript
- Tailwind CSS
- Recharts
- Lucide icons

### Backend

- FastAPI
- Pydantic
- Psycopg 3
- JWT authentication
- Passlib

### Data and Infra

- PostgreSQL
- Docker
- Docker Compose

## Repository Structure

```text
stockpilot-oms/
  backend/
    app/
    sql/
    Dockerfile
    pyproject.toml
    .env.example
  frontend/
    app/
    components/
    features/
    lib/
    Dockerfile
    package.json
    .env.example
  docs/
    architecture.md
    api-plan.md
    database-design.md
    domain-flows.md
    frontend-pages.md
    sql-notes.md
    screenshots/
  docker-compose.yml
  .env.example
  README.md
```

## Setup Instructions

### Option 1: Docker Compose

1. Copy the root environment file:

```bash
cp .env.example .env
```

2. Start the stack:

```bash
docker compose up --build
```

3. Open:

- Frontend: `http://localhost:3000`
- Backend API docs: `http://localhost:8000/docs`
- PostgreSQL: `localhost:5432`

The PostgreSQL container automatically runs the SQL files in `backend/sql` on first startup through `docker-entrypoint-initdb.d`.

### Option 2: Local Development Without Docker

#### Backend

1. Create a PostgreSQL database manually.
2. Copy the backend env file:

```bash
cp backend/.env.example backend/.env
```

3. Install dependencies:

```bash
cd backend
python -m pip install -e .[dev]
```

4. Apply SQL migrations in order:

- `backend/sql/001_init_schema.sql`
- `backend/sql/002_indexes.sql`
- `backend/sql/003_seed_data.sql`
- `backend/sql/004_future_updates.sql`

5. Start the API:

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

#### Frontend

1. Copy the frontend env file:

```bash
cp frontend/.env.example frontend/.env.local
```

2. Install dependencies:

```bash
cd frontend
npm install
```

3. Start the app:

```bash
npm run dev
```

## Testing

Current automated coverage focuses on backend business logic:

- auth
- products
- warehouses
- inventory movement safety
- order confirmation and cancellation logic

Run backend tests:

```bash
cd backend
python -m pytest app/tests -q
```

At the time of writing, the backend suite passes with:

```text
16 passed
```

Frontend validation currently uses:

```bash
cd frontend
npm run build
```

## Production-Minded Refinements

The latest polish pass focused on the things that most often make portfolio repositories feel junior or unfinished:

- safer dynamic SQL updates through allowlisted query builders
- transaction-safe order number allocation using PostgreSQL advisory locks
- stronger search indexes for warehouse and order discovery
- mobile navigation so the dashboard shell works below desktop widths
- expired JWT cleanup on the client to reduce broken-session behavior
- route navigation cleaned up to use Next.js links instead of full page reloads
- repository hygiene via a root `.gitignore` and less generated noise in the codebase

None of those are flashy features, and that is the point. They make the existing product feel more trustworthy.

## Demo Workspace

The manual seed SQL includes a curated demo workspace so the app does not open into empty tables and blank charts.

Seeded sign-in credentials:

- owner: `owner@northstar.example` / `Demo@12345`
- operations: `ops@northstar.example` / `Ops@12345`

That seed data is intentionally small and believable: enough to show low-stock alerts, warehouse imbalances, purchase history, a processing sales order, recent movements, and a non-empty activity feed without turning the UI into noisy fake data.

## Deployment

Production deployment is set up for:

- backend: Render
- database: Render Postgres
- frontend: Vercel

### Backend

The repository includes [render.yaml](</C:/Users/Rubel/Ai/project/stockpilot-oms/render.yaml>) so Render can provision and redeploy the backend from git without hand-editing build commands every time.

Required backend environment values:

- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `JWT_ALGORITHM=HS256`
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES=480`
- `CORS_ALLOW_ORIGINS=https://your-production-frontend.vercel.app`

Optional but recommended:

- `CORS_ALLOW_ORIGIN_REGEX=^https://.*\.vercel\.app$`

That keeps Vercel preview deployments from breaking CORS every time the preview hostname changes.

### Frontend

Set the Vercel environment value:

```env
NEXT_PUBLIC_API_URL=https://your-render-backend.onrender.com/api/v1
```

Once those values are set, ordinary git pushes are enough for automatic redeploys on both Render and Vercel.
```

## API Summary

Base path:

```text
/api/v1
```

Main API groups:

- Auth
  - `POST /auth/register`
  - `POST /auth/login`
  - `GET /auth/me`
- Workspace
  - `GET /workspaces/current`
  - `PATCH /workspaces/current`
- Products
  - list, create, detail, update, archive
- Warehouses
  - list, create, detail, update
- Inventory
  - balances
  - movements
  - stock-in
  - stock-out
  - transfer
  - adjustment
- Suppliers
  - list, create, detail, update
  - supplier-product linking
- Orders
  - list, create, detail, update
  - confirm, process, ship, complete, cancel
- Alerts
  - list, summary, resolve, dismiss, recalculate
- Activity
  - searchable audit feed
- Analytics
  - overview
  - stock by warehouse
  - top moving products
  - monthly order trends
  - supplier restock summaries

See [docs/api-plan.md](</C:/Users/Rubel/Ai/project/stockpilot-oms/docs/api-plan.md>) for the endpoint plan and [backend/app/api/routes](</C:/Users/Rubel/Ai/project/stockpilot-oms/backend/app/api/routes>) for the current implementation.

## Domain Logic Summary

### Workspace Isolation

Every operational table includes `workspace_id`, and every important backend query is filtered by workspace context derived from the JWT.

### Inventory Safety

Current stock is stored in `inventory_balances`, while immutable stock history lives in `inventory_movements`.

The backend uses transaction-safe movement flows:

- lock affected balances
- validate available stock
- update balances
- write movement records
- write activity logs
- reconcile low-stock alerts

### Orders

Sales orders:

- `draft -> confirmed -> processing -> shipped -> completed`
- confirmation reserves stock
- shipping deducts stock
- cancellation releases reservations when needed

Purchase orders:

- `draft -> confirmed -> processing -> completed`
- completion records inbound stock receipts

### Alerts

The project currently supports:

- low stock alerts
- stuck processing alerts
- alert recalculation endpoint

### Activity Feed

Operational mutations write append-only activity records for auditability and future observability.

## Sample SQL Highlights

### Workspace-safe current stock

```sql
SELECT
    ib.product_id,
    ib.warehouse_id,
    ib.on_hand_quantity,
    ib.reserved_quantity,
    (ib.on_hand_quantity - ib.reserved_quantity) AS available_quantity
FROM inventory_balances ib
WHERE ib.workspace_id = $1;
```

### Stock by warehouse aggregation

```sql
SELECT
    w.id,
    w.name,
    COUNT(DISTINCT ib.product_id) AS sku_count,
    COALESCE(SUM(ib.on_hand_quantity), 0) AS total_on_hand,
    COALESCE(SUM(ib.on_hand_quantity - ib.reserved_quantity), 0) AS total_available
FROM warehouses w
LEFT JOIN inventory_balances ib
  ON ib.workspace_id = w.workspace_id
 AND ib.warehouse_id = w.id
WHERE w.workspace_id = $1
GROUP BY w.id;
```

### Low stock detection

```sql
SELECT
    p.name,
    p.sku,
    w.name AS warehouse_name,
    (ib.on_hand_quantity - ib.reserved_quantity) AS available_quantity,
    p.reorder_point
FROM inventory_balances ib
JOIN products p
  ON p.id = ib.product_id
 AND p.workspace_id = ib.workspace_id
JOIN warehouses w
  ON w.id = ib.warehouse_id
 AND w.workspace_id = ib.workspace_id
WHERE ib.workspace_id = $1
  AND (ib.on_hand_quantity - ib.reserved_quantity) <= p.reorder_point;
```

### Monthly order trends with a CTE

```sql
WITH monthly_orders AS (
    SELECT
        to_char(date_trunc('month', COALESCE(completed_at, created_at)), 'YYYY-MM') AS month_bucket,
        order_type,
        COUNT(*) AS order_count,
        SUM(subtotal_amount) AS gross_amount
    FROM orders
    WHERE workspace_id = $1
      AND status IN ('completed', 'shipped', 'processing', 'confirmed')
    GROUP BY 1, 2
)
SELECT *
FROM monthly_orders
ORDER BY month_bucket, order_type;
```

## Screenshots Placeholders

Add real screenshots later at these paths:

- `docs/screenshots/dashboard.png`
- `docs/screenshots/products.png`
- `docs/screenshots/inventory.png`
- `docs/screenshots/orders.png`
- `docs/screenshots/analytics.png`

Placeholder references:

![Dashboard Placeholder](docs/screenshots/dashboard.png)
![Products Placeholder](docs/screenshots/products.png)
![Inventory Placeholder](docs/screenshots/inventory.png)
![Orders Placeholder](docs/screenshots/orders.png)
![Analytics Placeholder](docs/screenshots/analytics.png)

## Why This Is Strong For A Junior Full-Stack Portfolio

This project is strong because it proves more than framework familiarity.

It shows:

- real backend complexity instead of simple CRUD-only endpoints
- thoughtful SQL and schema design without hiding behind an ORM
- business-rule enforcement around stock reservations and overselling prevention
- maintainable separation between routes, services, and repositories
- multi-page frontend product thinking rather than a single dashboard screenshot
- professional presentation through documentation, layout, and reusable UI primitives
- Dockerized setup for local development and review

For a junior engineer portfolio, that combination matters. It demonstrates:

- you can model domain rules
- you can organize a full-stack codebase cleanly
- you can work across frontend, backend, SQL, and deployment concerns
- you can present engineering decisions in a way hiring teams can trust

## Supporting Docs

- [Architecture](</C:/Users/Rubel/Ai/project/stockpilot-oms/docs/architecture.md>)
- [Database Design](</C:/Users/Rubel/Ai/project/stockpilot-oms/docs/database-design.md>)
- [Domain Flows](</C:/Users/Rubel/Ai/project/stockpilot-oms/docs/domain-flows.md>)
- [Frontend Page Plan](</C:/Users/Rubel/Ai/project/stockpilot-oms/docs/frontend-pages.md>)
- [SQL Notes](</C:/Users/Rubel/Ai/project/stockpilot-oms/docs/sql-notes.md>)

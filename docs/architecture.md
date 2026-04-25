# StockPilot OMS Architecture

StockPilot OMS is a production-style B2B SaaS platform for multi-warehouse inventory, order, supplier, alert, and analytics workflows. The project is designed to demonstrate a clean full-stack architecture with a Next.js TypeScript frontend, a FastAPI backend, PostgreSQL with raw SQL, Docker-based local development, and careful domain modeling.

## Goals

- Build a realistic inventory and order management system that feels useful for a small or mid-sized operations team.
- Keep the backend modular, testable, and explicit, with no ORM and no Alembic.
- Use PostgreSQL as a first-class part of the application design through constraints, indexes, joins, CTEs, transactions, and parameterized queries.
- Enforce workspace isolation across every domain query and mutation.
- Make inventory and order changes transaction-safe to prevent negative stock and overselling.
- Keep the frontend polished, responsive, and component-based, with reusable tables, forms, layout primitives, charts, badges, filters, modals, and empty/error/loading states.

## High-Level System

```text
Browser
  |
  | HTTPS / REST JSON
  v
Next.js frontend
  |
  | REST API calls with JWT access token
  v
FastAPI backend
  |
  | asyncpg / psycopg parameterized raw SQL
  v
PostgreSQL
```

Local development will run through Docker Compose with separate services for frontend, backend, and PostgreSQL. The backend owns database migrations through manually versioned SQL files under `backend/sql`.

## Repository Shape

Expected project structure after later phases:

```text
stockpilot-oms/
  backend/
    app/
      main.py
      api/
      core/
      db/
      repositories/
      schemas/
      services/
      tests/
    sql/
      001_init_schema.sql
      002_indexes.sql
      003_seed_data.sql
      004_future_updates.sql
    Dockerfile
    pyproject.toml
  frontend/
    app/
    components/
    features/
    lib/
    tests/
    Dockerfile
    package.json
  docs/
  docker-compose.yml
  README.md
  .env.example
```

## Backend Architecture

The backend will use layered modules:

- `api`: FastAPI routers, request dependencies, route-level validation, and response mapping.
- `schemas`: Pydantic request and response models.
- `services`: Business rules, transaction orchestration, authorization checks, and domain decisions.
- `repositories`: Raw SQL data access only. Repositories receive workspace/user context and never build SQL with untrusted string interpolation.
- `db`: connection pool management, transaction helpers, migration runner utilities for development, and database health checks.
- `core`: settings, security, JWT, password hashing, exceptions, pagination, and shared constants.
- `tests`: unit and integration tests using a test database.

### Backend Rules

- No ORM.
- No Alembic.
- All SQL must be parameterized.
- List endpoints must support pagination.
- Filtering/search must be implemented with safe query construction.
- Workspace isolation must be enforced in every repository query.
- Inventory and order stock changes must run inside database transactions.
- Database constraints should catch invalid states that application validation misses.

## Frontend Architecture

The frontend will use Next.js with TypeScript and Tailwind CSS. The UI should feel like a premium B2B admin product: dense enough for operations work, clean enough for a portfolio, and consistent across pages.

Suggested frontend structure:

```text
frontend/
  app/
    (auth)/
      login/
      register/
    (dashboard)/
      dashboard/
      products/
      warehouses/
      inventory/
      suppliers/
      orders/
      alerts/
      analytics/
      activity/
      settings/
  components/
    ui/
    layout/
    data-table/
    charts/
    forms/
  features/
    auth/
    products/
    warehouses/
    inventory/
    suppliers/
    orders/
    alerts/
    analytics/
    activity/
  lib/
    api-client.ts
    auth.ts
    formatters.ts
    validation.ts
```

### Frontend Rules

- Use real backend APIs.
- Keep route-level pages focused on composition.
- Put reusable domain UI in `features`.
- Put generic reusable components in `components`.
- Use typed API clients and typed response models.
- Include loading, empty, and error states on data-heavy pages.
- Use accessible forms with validation feedback.
- Use status badges for products, orders, alerts, and movements.

## Authentication And Authorization

Authentication will use JWT access tokens. The first version can use access tokens only, with a clean path to refresh tokens later.

User flow:

1. User registers with name, email, password, and workspace name.
2. Backend creates a workspace and the first user in one transaction.
3. User logs in and receives a JWT.
4. Frontend stores the token in a secure client strategy selected during implementation.
5. Authenticated requests include `Authorization: Bearer <token>`.
6. Backend extracts `user_id` and `workspace_id` from the token and enforces workspace isolation.

Roles can start simple:

- `owner`: initial workspace admin.
- `member`: normal operational user.

The schema should leave room for stronger role-based access control later.

## Workspace Isolation

Every business table belongs to a workspace either directly or through a parent record. Queries must include `workspace_id` filters and should not trust request body workspace IDs.

Examples:

- Product list: filter by `products.workspace_id = current_user.workspace_id`.
- Warehouse detail: fetch by `id` and `workspace_id`.
- Inventory movements: verify product and warehouse ownership inside the same workspace before writing.
- Orders: order header and order items must be scoped through `orders.workspace_id`.

## Inventory Consistency

Inventory is represented by two complementary concepts:

- `inventory_balances`: current stock per product and warehouse.
- `inventory_movements`: append-only movement history explaining changes.

Stock changes must update both in one database transaction. The backend should use row-level locks where appropriate, such as `SELECT ... FOR UPDATE` on the affected balance rows.

Negative available stock is not allowed. Reservation and deduction rules are defined in `domain-flows.md`.

## Order Consistency

Sales orders and purchase/restock orders share an `orders` table with an `order_type` value. Order lifecycle transitions must be explicit and validated by service logic.

Sales order confirmation reserves stock. Shipping/completion deducts stock from reserved quantity. Cancellation releases reservations if the order was not shipped.

Purchase order completion increases stock and records restock movements.

## Observability And Auditability

The first version will include activity logs as a user-facing audit feed. Later phases can add structured backend logs.

Important events:

- User registration and login.
- Product created, updated, archived.
- Warehouse created or updated.
- Inventory movement created.
- Order status changed.
- Supplier created or updated.
- Alert resolved or dismissed.

## Error Handling

Backend responses should be consistent:

```json
{
  "error": {
    "code": "INSUFFICIENT_STOCK",
    "message": "Not enough available stock to confirm this order.",
    "details": {}
  }
}
```

Common error classes:

- `VALIDATION_ERROR`
- `AUTHENTICATION_REQUIRED`
- `PERMISSION_DENIED`
- `NOT_FOUND`
- `CONFLICT`
- `INSUFFICIENT_STOCK`
- `INVALID_ORDER_TRANSITION`
- `DATABASE_ERROR`

## Testing Strategy

Backend tests should cover:

- Auth registration, login, and current user.
- Product creation, filtering, archiving, and SKU uniqueness.
- Warehouse creation and stock views.
- Inventory stock in, stock out, transfer, adjustment, and negative stock prevention.
- Sales order confirmation and overselling prevention.
- Purchase order completion and stock increase.
- Analytics aggregate endpoints.

Frontend tests should cover a few meaningful interaction paths:

- Login form validation.
- Product table search/filter behavior.
- Create product form validation.
- Order status badge rendering or order form item entry.

## Production-Friendly Decisions

- Use explicit SQL files so reviewers can inspect schema design.
- Use repository/service boundaries to make raw SQL manageable.
- Keep workspace isolation in repository methods, not only route handlers.
- Use transactions for every operation that changes stock or order state.
- Use typed schemas and consistent response models.
- Use focused documentation so the project reads like a real engineering artifact.


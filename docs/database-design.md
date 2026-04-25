# StockPilot OMS Database Design

The database is PostgreSQL with raw SQL migrations only. There will be no ORM and no Alembic. All schema changes will be captured in versioned SQL files under `backend/sql`.

Planned migration files:

- `001_init_schema.sql`: extensions, tables, primary keys, foreign keys, check constraints, timestamps, and core functions/triggers if needed.
- `002_indexes.sql`: performance indexes, partial indexes, search indexes, and composite indexes.
- `003_seed_data.sql`: demo workspace, users, categories, products, warehouses, suppliers, stock, movements, orders, alerts, and activity logs.
- `004_future_updates.sql`: intentionally reserved for documented future schema changes.

## Design Principles

- Every business record is scoped by `workspace_id`.
- Use UUID primary keys for public-safe identifiers.
- Use `created_at` and `updated_at` on mutable tables.
- Prefer explicit enums through check constraints for portability and easy review.
- Use foreign keys with intentional delete behavior.
- Keep `inventory_movements` append-only.
- Store money as `numeric(12, 2)`.
- Store quantities as integers for this version.
- Enforce non-negative current stock fields with check constraints.
- Use transaction-safe balance updates from the backend.

## Tables

### `workspaces`

Stores tenant organizations.

Important columns:

- `id uuid primary key`
- `name text not null`
- `slug text not null unique`
- `created_at timestamptz not null`
- `updated_at timestamptz not null`

### `users`

Stores workspace users.

Important columns:

- `id uuid primary key`
- `workspace_id uuid not null references workspaces(id)`
- `name text not null`
- `email citext not null`
- `password_hash text not null`
- `role text not null check (role in ('owner', 'member'))`
- `is_active boolean not null default true`
- `created_at timestamptz not null`
- `updated_at timestamptz not null`

Constraints:

- Unique email globally for simple login.
- Optional future unique `(workspace_id, email)` if multi-workspace login is added.

### `categories`

Product classification per workspace.

Important columns:

- `id uuid primary key`
- `workspace_id uuid not null references workspaces(id)`
- `name text not null`
- `description text`
- `created_at timestamptz not null`

Constraints:

- Unique `(workspace_id, lower(name))` through an expression index.

### `products`

Sellable or trackable inventory items.

Important columns:

- `id uuid primary key`
- `workspace_id uuid not null references workspaces(id)`
- `category_id uuid references categories(id)`
- `name text not null`
- `sku text not null`
- `description text`
- `unit text not null default 'each'`
- `reorder_point integer not null default 0`
- `reorder_quantity integer not null default 0`
- `status text not null check (status in ('active', 'archived'))`
- `created_by uuid references users(id)`
- `created_at timestamptz not null`
- `updated_at timestamptz not null`

Constraints:

- Unique `(workspace_id, sku)`.
- `reorder_point >= 0`.
- `reorder_quantity >= 0`.

### `warehouses`

Physical or logical stock locations.

Important columns:

- `id uuid primary key`
- `workspace_id uuid not null references workspaces(id)`
- `name text not null`
- `code text not null`
- `address_line1 text`
- `city text`
- `country text`
- `status text not null check (status in ('active', 'inactive'))`
- `created_at timestamptz not null`
- `updated_at timestamptz not null`

Constraints:

- Unique `(workspace_id, code)`.

### `inventory_balances`

Current stock by product and warehouse.

Important columns:

- `id uuid primary key`
- `workspace_id uuid not null references workspaces(id)`
- `product_id uuid not null references products(id)`
- `warehouse_id uuid not null references warehouses(id)`
- `on_hand_quantity integer not null default 0`
- `reserved_quantity integer not null default 0`
- `created_at timestamptz not null`
- `updated_at timestamptz not null`

Constraints:

- Unique `(workspace_id, product_id, warehouse_id)`.
- `on_hand_quantity >= 0`.
- `reserved_quantity >= 0`.
- `reserved_quantity <= on_hand_quantity`.

Available stock is calculated as:

```sql
on_hand_quantity - reserved_quantity
```

### `inventory_movements`

Append-only history of inventory changes.

Important columns:

- `id uuid primary key`
- `workspace_id uuid not null references workspaces(id)`
- `product_id uuid not null references products(id)`
- `warehouse_id uuid not null references warehouses(id)`
- `destination_warehouse_id uuid references warehouses(id)`
- `movement_type text not null`
- `quantity integer not null`
- `quantity_before integer not null`
- `quantity_after integer not null`
- `reason text`
- `reference_type text`
- `reference_id uuid`
- `notes text`
- `created_by uuid references users(id)`
- `created_at timestamptz not null`

Movement types:

- `stock_in`
- `stock_out`
- `transfer_out`
- `transfer_in`
- `adjustment`
- `reservation`
- `reservation_release`
- `order_deduction`

Constraints:

- `quantity > 0` for all movement records.
- `quantity_before >= 0`.
- `quantity_after >= 0`.

### `suppliers`

Vendor records.

Important columns:

- `id uuid primary key`
- `workspace_id uuid not null references workspaces(id)`
- `name text not null`
- `contact_name text`
- `email text`
- `phone text`
- `address text`
- `status text not null check (status in ('active', 'inactive'))`
- `notes text`
- `created_at timestamptz not null`
- `updated_at timestamptz not null`

### `supplier_products`

Many-to-many link between suppliers and products.

Important columns:

- `id uuid primary key`
- `workspace_id uuid not null references workspaces(id)`
- `supplier_id uuid not null references suppliers(id)`
- `product_id uuid not null references products(id)`
- `supplier_sku text`
- `lead_time_days integer`
- `minimum_order_quantity integer`
- `unit_cost numeric(12, 2)`
- `is_preferred boolean not null default false`
- `created_at timestamptz not null`
- `updated_at timestamptz not null`

Constraints:

- Unique `(workspace_id, supplier_id, product_id)`.
- `lead_time_days >= 0`.
- `minimum_order_quantity >= 0`.
- `unit_cost >= 0`.

### `orders`

Sales and purchase/restock order headers.

Important columns:

- `id uuid primary key`
- `workspace_id uuid not null references workspaces(id)`
- `order_number text not null`
- `order_type text not null check (order_type in ('sales', 'purchase'))`
- `status text not null`
- `warehouse_id uuid not null references warehouses(id)`
- `supplier_id uuid references suppliers(id)`
- `customer_name text`
- `notes text`
- `subtotal_amount numeric(12, 2) not null default 0`
- `created_by uuid references users(id)`
- `confirmed_at timestamptz`
- `processed_at timestamptz`
- `shipped_at timestamptz`
- `completed_at timestamptz`
- `cancelled_at timestamptz`
- `created_at timestamptz not null`
- `updated_at timestamptz not null`

Order statuses:

- `draft`
- `confirmed`
- `processing`
- `shipped`
- `completed`
- `cancelled`

Constraints:

- Unique `(workspace_id, order_number)`.
- Purchase orders require `supplier_id`.
- Sales orders require `customer_name`.

### `order_items`

Order line items.

Important columns:

- `id uuid primary key`
- `workspace_id uuid not null references workspaces(id)`
- `order_id uuid not null references orders(id) on delete cascade`
- `product_id uuid not null references products(id)`
- `quantity integer not null`
- `unit_price numeric(12, 2)`
- `unit_cost numeric(12, 2)`
- `line_total numeric(12, 2) not null`
- `created_at timestamptz not null`

Constraints:

- `quantity > 0`.
- Sales order items require `unit_price`.
- Purchase order items require `unit_cost`.

### `alerts`

Operational alerts.

Important columns:

- `id uuid primary key`
- `workspace_id uuid not null references workspaces(id)`
- `alert_type text not null`
- `severity text not null check (severity in ('info', 'warning', 'critical'))`
- `status text not null check (status in ('open', 'resolved', 'dismissed'))`
- `product_id uuid references products(id)`
- `warehouse_id uuid references warehouses(id)`
- `order_id uuid references orders(id)`
- `title text not null`
- `message text not null`
- `metadata jsonb not null default '{}'::jsonb`
- `resolved_by uuid references users(id)`
- `resolved_at timestamptz`
- `created_at timestamptz not null`
- `updated_at timestamptz not null`

Alert types:

- `low_stock`
- `reorder_suggestion`
- `stale_order`
- `stuck_processing`

### `activity_logs`

Searchable audit feed.

Important columns:

- `id uuid primary key`
- `workspace_id uuid not null references workspaces(id)`
- `actor_user_id uuid references users(id)`
- `action text not null`
- `entity_type text not null`
- `entity_id uuid`
- `summary text not null`
- `metadata jsonb not null default '{}'::jsonb`
- `created_at timestamptz not null`

Examples:

- `product.created`
- `product.archived`
- `inventory.stock_in`
- `inventory.transfer`
- `order.confirmed`
- `order.cancelled`
- `supplier.updated`
- `alert.resolved`

## Relationship Summary

- One workspace has many users, categories, products, warehouses, suppliers, orders, alerts, and activity logs.
- One product belongs to one workspace and optionally one category.
- One product has many inventory balances across warehouses.
- One product has many inventory movements.
- One warehouse has many inventory balances and movements.
- One supplier has many linked products through `supplier_products`.
- One order has many order items.
- Orders can reference a supplier for purchase orders.
- Alerts can reference products, warehouses, or orders.
- Activity logs can reference any entity by `entity_type` and `entity_id`.

## Index Plan

Core indexes for `002_indexes.sql`:

- `users(email)`
- `products(workspace_id, sku)`
- `products(workspace_id, status, created_at desc)`
- `products(workspace_id, category_id)`
- `products` trigram or full-text index for name/SKU search if enabled.
- `warehouses(workspace_id, code)`
- `inventory_balances(workspace_id, product_id, warehouse_id)`
- `inventory_balances(workspace_id, warehouse_id)`
- `inventory_movements(workspace_id, created_at desc)`
- `inventory_movements(workspace_id, product_id, created_at desc)`
- `inventory_movements(workspace_id, warehouse_id, created_at desc)`
- `suppliers(workspace_id, status, name)`
- `supplier_products(workspace_id, supplier_id, product_id)`
- `orders(workspace_id, status, created_at desc)`
- `orders(workspace_id, order_type, status)`
- `order_items(workspace_id, order_id)`
- `alerts(workspace_id, status, severity, created_at desc)`
- `activity_logs(workspace_id, created_at desc)`
- `activity_logs(workspace_id, entity_type, entity_id)`

## Transaction-Safe Stock Strategy

For any stock mutation:

1. Start a database transaction.
2. Fetch product and warehouse within the current workspace.
3. Lock the relevant `inventory_balances` row with `FOR UPDATE`.
4. Validate available quantity when reducing or reserving stock.
5. Update `inventory_balances`.
6. Insert one or more `inventory_movements`.
7. Insert an `activity_logs` row.
8. Recalculate or update alerts where needed.
9. Commit.

Transfers lock source and destination balances in deterministic order by ID to reduce deadlock risk.

## Analytics Query Expectations

Analytics should demonstrate strong SQL:

- CTE for monthly order/revenue summary.
- Joins between products, warehouses, balances, movements, suppliers, and orders.
- Aggregations with `count`, `sum`, `coalesce`, and `rank`.
- Date filtering.
- Pagination or limit for ranked reports.

Example future CTE shape:

```sql
with monthly_sales as (
  select
    date_trunc('month', completed_at) as month,
    count(*) as order_count,
    sum(subtotal_amount) as revenue
  from orders
  where workspace_id = $1
    and order_type = 'sales'
    and status = 'completed'
  group by 1
)
select month, order_count, revenue
from monthly_sales
order by month desc;
```


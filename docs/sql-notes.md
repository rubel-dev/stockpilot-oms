# StockPilot OMS SQL Notes

Phase 2 adds the manual PostgreSQL migration files under `backend/sql`:

- `001_init_schema.sql`
- `002_indexes.sql`
- `003_seed_data.sql`
- `004_future_updates.sql`

The schema is designed to support a production-style FastAPI backend that uses raw SQL repositories only.

## Important Schema Choices

### 1. Workspace isolation is built into every business table

All operational tables include `workspace_id`, including:

- `users`
- `categories`
- `products`
- `warehouses`
- `inventory_balances`
- `inventory_movements`
- `suppliers`
- `supplier_products`
- `orders`
- `order_items`
- `alerts`
- `activity_logs`

This makes later repository code straightforward and safer because almost every query can enforce:

```sql
... WHERE workspace_id = $1
```

It also lets us add composite foreign keys like `(product_id, workspace_id)` to ensure a record from one workspace cannot accidentally reference a parent from another workspace.

### 2. Composite workspace-aware foreign keys reduce tenant leakage risk

Several tables use foreign keys shaped like:

```sql
FOREIGN KEY (product_id, workspace_id)
REFERENCES products(id, workspace_id)
```

That pattern is stricter than a simple foreign key to `products(id)` because it ensures:

- the child row belongs to the same workspace as the parent row
- later backend bugs have less room to create cross-workspace references

### 3. Current stock and stock history are intentionally separated

Inventory uses two tables:

- `inventory_balances` for current state
- `inventory_movements` for append-only history

This gives later phases:

- fast reads for current stock
- a complete event log for auditing
- a clean basis for analytics and activity views

### 4. Reserved stock is modeled explicitly

`inventory_balances` stores:

- `on_hand_quantity`
- `reserved_quantity`

Available stock is derived as:

```sql
on_hand_quantity - reserved_quantity
```

This is important because sales orders need to reserve stock before shipment. The database constraint:

```sql
reserved_quantity <= on_hand_quantity
```

helps block impossible inventory states.

### 5. Orders and stock changes are designed for transaction-safe service logic

The schema does not try to implement full inventory mutation logic in triggers. That logic will live in FastAPI services later, but the schema supports safe behavior by providing:

- per-workspace uniqueness on order numbers and SKUs
- non-negative quantity checks
- strict order type and status checks
- workspace-aware foreign keys
- indexes that support `SELECT ... FOR UPDATE` access patterns on balances

Later stock-changing services should:

1. start a transaction
2. lock affected `inventory_balances` rows with `FOR UPDATE`
3. validate available stock
4. update balances
5. insert movement rows
6. insert activity rows
7. update alerts if needed
8. commit

### 6. Alerts are deduplicated at the database level

`002_indexes.sql` creates a partial unique index for open alerts by workspace, alert type, and related entity combination. That helps prevent duplicate open low-stock or stale-order alerts when recalculation runs more than once.

### 7. Search-heavy tables are prepared with trigram indexes

The schema enables `pg_trgm` and adds GIN trigram indexes for:

- product search
- supplier search
- activity feed search

That gives a realistic base for responsive B2B filtering later without introducing Elasticsearch or a similar external system.

## Seed Data Notes

The seed file creates a realistic demo workspace:

- one workspace
- two users
- three categories
- three warehouses
- three suppliers
- six products
- supplier-product links
- current inventory balances
- several orders in different lifecycle stages
- movement history
- active alerts
- activity feed entries

Seeded demo credentials are intentionally usable so a reviewer can sign in immediately after loading the SQL:

- owner account: `owner@northstar.example` / `Demo@12345`
- operations account: `ops@northstar.example` / `Ops@12345`

This data is shaped to support:

- dashboard cards
- product tables
- warehouse stock views
- movement history
- low-stock scenarios
- supplier restock summaries
- analytics pages

## Query Patterns That Will Power Later Features

Below are the main SQL shapes the backend will later use.

### Stock by warehouse

Purpose:

- show stock totals and SKU counts by warehouse
- support dashboard and warehouse analytics

Typical query shape:

```sql
SELECT
    w.id,
    w.name,
    w.code,
    COUNT(DISTINCT ib.product_id) AS sku_count,
    COALESCE(SUM(ib.on_hand_quantity), 0) AS total_on_hand,
    COALESCE(SUM(ib.reserved_quantity), 0) AS total_reserved,
    COALESCE(SUM(ib.on_hand_quantity - ib.reserved_quantity), 0) AS total_available
FROM warehouses w
LEFT JOIN inventory_balances ib
    ON ib.workspace_id = w.workspace_id
   AND ib.warehouse_id = w.id
WHERE w.workspace_id = $1
GROUP BY w.id, w.name, w.code
ORDER BY w.name;
```

### Low stock alerts

Purpose:

- identify products whose available quantity is at or below reorder point
- drive alert recalculation and alert summary cards

Typical query shape:

```sql
SELECT
    p.id AS product_id,
    w.id AS warehouse_id,
    p.name,
    p.sku,
    w.name AS warehouse_name,
    ib.on_hand_quantity,
    ib.reserved_quantity,
    (ib.on_hand_quantity - ib.reserved_quantity) AS available_quantity,
    p.reorder_point,
    p.reorder_quantity
FROM inventory_balances ib
JOIN products p
    ON p.id = ib.product_id
   AND p.workspace_id = ib.workspace_id
JOIN warehouses w
    ON w.id = ib.warehouse_id
   AND w.workspace_id = ib.workspace_id
WHERE ib.workspace_id = $1
  AND p.status = 'active'
  AND (ib.on_hand_quantity - ib.reserved_quantity) <= p.reorder_point
ORDER BY available_quantity ASC, p.name ASC;
```

### Top moving products

Purpose:

- rank products by movement volume in a date range
- support analytics and product-performance views

Typical query shape:

```sql
SELECT
    p.id,
    p.name,
    p.sku,
    SUM(im.quantity) AS total_moved,
    COUNT(*) AS movement_count
FROM inventory_movements im
JOIN products p
    ON p.id = im.product_id
   AND p.workspace_id = im.workspace_id
WHERE im.workspace_id = $1
  AND im.created_at >= $2
  AND im.created_at < $3
GROUP BY p.id, p.name, p.sku
ORDER BY total_moved DESC, movement_count DESC
LIMIT $4;
```

For a more domain-specific ranking, later code can restrict movement types to outward operational movements such as `order_deduction`, `stock_out`, and `transfer_out`.

### Monthly order trends

Purpose:

- show monthly sales and purchase volume
- power dashboard trend charts and analytics views

Typical query shape with a CTE:

```sql
WITH monthly_orders AS (
    SELECT
        date_trunc('month', COALESCE(completed_at, created_at)) AS month_bucket,
        order_type,
        COUNT(*) AS order_count,
        SUM(subtotal_amount) AS gross_amount
    FROM orders
    WHERE workspace_id = $1
      AND status IN ('completed', 'shipped', 'processing', 'confirmed')
      AND COALESCE(completed_at, created_at) >= $2
      AND COALESCE(completed_at, created_at) < $3
    GROUP BY 1, 2
)
SELECT
    month_bucket,
    order_type,
    order_count,
    gross_amount
FROM monthly_orders
ORDER BY month_bucket ASC, order_type ASC;
```

Later, the backend can choose whether revenue charts should use only completed sales orders.

### Supplier restock summaries

Purpose:

- show which suppliers drive incoming stock
- power supplier analytics and supplier detail summaries

Typical query shape:

```sql
SELECT
    s.id AS supplier_id,
    s.name AS supplier_name,
    COUNT(DISTINCT o.id) AS purchase_order_count,
    COUNT(DISTINCT oi.product_id) AS unique_products,
    COALESCE(SUM(oi.quantity), 0) AS total_units_ordered,
    COALESCE(SUM(oi.line_total), 0) AS total_spend
FROM orders o
JOIN suppliers s
    ON s.id = o.supplier_id
   AND s.workspace_id = o.workspace_id
JOIN order_items oi
    ON oi.order_id = o.id
   AND oi.workspace_id = o.workspace_id
WHERE o.workspace_id = $1
  AND o.order_type = 'purchase'
  AND o.status IN ('confirmed', 'processing', 'completed')
  AND o.created_at >= $2
  AND o.created_at < $3
GROUP BY s.id, s.name
ORDER BY total_spend DESC, total_units_ordered DESC;
```

### Activity feed

Purpose:

- power the searchable audit timeline
- support filters by actor, entity, action, and date

Typical query shape:

```sql
SELECT
    al.id,
    al.action,
    al.entity_type,
    al.entity_id,
    al.summary,
    al.metadata,
    al.created_at,
    u.id AS actor_user_id,
    u.name AS actor_name
FROM activity_logs al
LEFT JOIN users u
    ON u.id = al.actor_user_id
   AND u.workspace_id = al.workspace_id
WHERE al.workspace_id = $1
  AND ($2::uuid IS NULL OR al.actor_user_id = $2)
  AND ($3::text IS NULL OR al.entity_type = $3)
  AND ($4::text IS NULL OR al.action = $4)
  AND ($5::timestamptz IS NULL OR al.created_at >= $5)
  AND ($6::timestamptz IS NULL OR al.created_at < $6)
  AND (
      $7::text IS NULL
      OR al.summary ILIKE '%' || $7 || '%'
      OR al.action ILIKE '%' || $7 || '%'
      OR al.entity_type ILIKE '%' || $7 || '%'
  )
ORDER BY al.created_at DESC
LIMIT $8 OFFSET $9;
```

## Files Created In Phase 2

- `backend/sql/001_init_schema.sql`
- `backend/sql/002_indexes.sql`
- `backend/sql/003_seed_data.sql`
- `backend/sql/004_future_updates.sql`
- `docs/sql-notes.md`

## Implementation Notes For Phase 3

When the FastAPI backend is implemented, repository methods should:

- always filter by `workspace_id`
- use parameterized queries only
- allowlist sortable fields
- use transactions for stock and order mutations
- lock `inventory_balances` rows before any reservation or deduction
- treat `inventory_movements` and `activity_logs` as append-only records

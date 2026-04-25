# StockPilot OMS Frontend Pages

The frontend should feel like a polished B2B SaaS admin product for operations teams. It should avoid a student-demo feel by using realistic page density, consistent layout, strong table interactions, clear hierarchy, and domain-specific UI states.

## App Shell

Authenticated pages share a dashboard shell:

- Left sidebar navigation.
- Top navbar with workspace name, global search placeholder, alert indicator, and user menu.
- Main content area with page title, short operational subtitle, primary action, and optional filters.
- Responsive behavior that collapses navigation on smaller screens.

Primary navigation:

- Dashboard
- Products
- Warehouses
- Inventory
- Suppliers
- Orders
- Alerts
- Analytics
- Activity
- Settings

## Design Direction

Visual style:

- Clean SaaS admin interface.
- Neutral background, crisp cards, restrained borders, and strong spacing.
- Status colors used intentionally, not as decoration.
- Tables optimized for scanning.
- Form layouts that feel practical for business workflows.

Reusable components:

- `AppShell`
- `SidebarNav`
- `TopNav`
- `PageHeader`
- `MetricCard`
- `DataTable`
- `TableToolbar`
- `StatusBadge`
- `FilterBar`
- `SearchInput`
- `ConfirmDialog`
- `Drawer`
- `Modal`
- `EmptyState`
- `ErrorState`
- `LoadingSkeleton`
- `FormField`
- `SelectField`
- `DateRangePicker`
- `PaginationControls`
- `ChartCard`

## Public Auth Routes

### `/login`

Purpose:

- Authenticate existing users.

UI:

- Focused login panel.
- Email and password fields.
- Validation messages.
- Submit loading state.
- Link to register.

Behavior:

- Calls `POST /api/v1/auth/login`.
- Stores JWT using the selected auth strategy.
- Redirects to `/dashboard`.

### `/register`

Purpose:

- Create a new workspace and owner user.

UI:

- Workspace name, full name, email, password fields.
- Password requirements feedback.
- Submit loading state.

Behavior:

- Calls `POST /api/v1/auth/register`.
- Redirects to `/dashboard`.

## Authenticated Routes

### `/dashboard`

Purpose:

- Give operations users a daily command center.

Sections:

- KPI cards: total products, total stock units, low-stock alerts, open sales orders, open purchase orders, monthly revenue.
- Alerts summary.
- Stock by warehouse chart.
- Recent inventory movements.
- Recent order activity.
- Top moving products.

States:

- Loading skeleton cards.
- Empty onboarding state when seed data is absent.
- Error state with retry.

### `/products`

Purpose:

- Manage product catalog and stock visibility.

UI:

- Searchable/filterable product table.
- Filters for category, status, low stock, warehouse.
- Primary action: New product.
- Columns: SKU, product name, category, total stock, reserved, available, suppliers, status, updated date.
- Row actions: view, edit, archive.

Behavior:

- Calls `GET /api/v1/products`.
- Supports pagination and filters.
- Archive action uses confirm dialog.

### `/products/new`

Purpose:

- Create a product.

UI:

- Product identity section.
- SKU field with generate option.
- Category select with create-category flow.
- Reorder settings.
- Optional initial stock helper can be deferred to inventory page for strict domain clarity.

Behavior:

- Calls `POST /api/v1/products`.
- Redirects to product detail.

### `/products/[id]`

Purpose:

- Show product operational detail.

Sections:

- Product summary and status.
- Stock by warehouse table.
- Supplier links.
- Recent movements.
- Open alerts.
- Related orders.

Actions:

- Edit product.
- Archive product.
- Create stock movement.
- Link supplier.

### `/warehouses`

Purpose:

- Manage warehouse locations.

UI:

- Warehouse table with search and status filter.
- Columns: code, name, city/country, total SKUs, total units, low-stock items, status.
- Primary action: New warehouse.

### `/warehouses/[id]`

Purpose:

- Show warehouse-level stock and operational activity.

Sections:

- Warehouse profile.
- Stock table by product.
- Low-stock products.
- Recent movements.
- Open orders linked to the warehouse.

Actions:

- Edit warehouse.
- Start transfer.
- Stock adjustment.

### `/inventory`

Purpose:

- Show current inventory balances.

UI:

- Balance table by product and warehouse.
- Filters for warehouse, product, category, low stock.
- Columns: SKU, product, warehouse, on hand, reserved, available, reorder point.
- Quick actions: stock in, stock out, transfer, adjustment.

Movement actions should open drawers or modals with focused forms.

### `/inventory/movements`

Purpose:

- Searchable inventory movement history.

UI:

- Movement timeline or data table.
- Filters for product, warehouse, movement type, date range.
- Columns: date, product, warehouse, type, quantity, before, after, reference, user.

### `/suppliers`

Purpose:

- Manage supplier relationships.

UI:

- Supplier table.
- Search and status filter.
- Columns: supplier, contact, email, phone, linked products, last restock, status.
- Primary action: New supplier.

### `/suppliers/[id]`

Purpose:

- Show supplier details and restock history.

Sections:

- Supplier profile.
- Linked products table.
- Purchase order history.
- Restock analytics summary.
- Activity feed for supplier changes.

Actions:

- Edit supplier.
- Link product.
- Create purchase order.

### `/orders`

Purpose:

- Manage sales and purchase orders.

UI:

- Tab or segmented control for sales and purchase orders.
- Filters for status, supplier, warehouse, date range.
- Columns: order number, type, status, warehouse, customer/supplier, item count, subtotal, created date.
- Primary action: New order.

Status badges:

- Draft
- Confirmed
- Processing
- Shipped
- Completed
- Cancelled

### `/orders/new`

Purpose:

- Create a draft sales or purchase order.

UI:

- Order type selector.
- Warehouse selector.
- Supplier selector for purchase orders.
- Customer field for sales orders.
- Dynamic item entry table.
- Product picker, quantity, unit price/cost, line totals.
- Validation for missing items and invalid quantities.

Behavior:

- Calls `POST /api/v1/orders`.
- Redirects to order detail.

### `/orders/[id]`

Purpose:

- Show order detail and lifecycle actions.

Sections:

- Header with order number, type, status, total.
- Order items.
- Status timeline.
- Inventory impact.
- Activity log.

Actions depend on status:

- Edit draft.
- Confirm.
- Process.
- Ship sales order.
- Complete purchase order.
- Cancel.

Destructive or stock-impacting actions require confirmation.

### `/alerts`

Purpose:

- Manage operational alerts.

UI:

- Alert summary cards by severity.
- Alert table with filters for type, severity, status, warehouse, product.
- Row actions: resolve, dismiss, view related entity.

Alert types:

- Low stock.
- Reorder suggestion.
- Stale order.
- Stuck processing.

### `/analytics`

Purpose:

- Show operational performance and inventory insights.

Sections:

- Stock by warehouse chart.
- Low-stock product table.
- Top moving products.
- Monthly order and revenue chart.
- Supplier restock summary.
- Inventory movement trends.
- Product performance ranking.

Controls:

- Date range.
- Warehouse filter.
- Product/category filter where useful.

### `/activity`

Purpose:

- Searchable audit feed.

UI:

- Timeline or table.
- Search by summary, entity, actor.
- Filters for action, entity type, actor, date range.

Rows include:

- Actor.
- Action.
- Entity.
- Summary.
- Timestamp.

### `/settings`

Purpose:

- Manage workspace settings.

Sections:

- Workspace profile.
- User profile.
- Default reorder preferences.
- API/environment info can be added later.

## Frontend State Strategy

Initial implementation can use:

- Server components for static shells where appropriate.
- Client components for forms, tables, filters, and charts.
- A small typed API client around `fetch`.
- React Hook Form and Zod if selected during frontend implementation.
- TanStack Query can be considered for client-side data fetching, caching, and mutations.

## Polish Checklist

Every major page should include:

- Page title and primary action.
- Loading state.
- Empty state.
- Error state.
- Pagination where lists can grow.
- Search and filters where useful.
- Consistent status badges.
- Clear destructive-action confirmation.
- Responsive layout for tablet and mobile.


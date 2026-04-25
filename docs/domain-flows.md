# StockPilot OMS Domain Flows

This document defines the core business workflows for StockPilot OMS. Later implementation phases should follow these rules closely, especially where inventory and orders affect stock.

## Workspace Registration

Flow:

1. User submits workspace name, name, email, and password.
2. Backend validates unique email and valid password.
3. Backend starts a transaction.
4. Create workspace.
5. Create owner user in that workspace.
6. Insert `activity_logs` entry for workspace/user creation.
7. Commit.
8. Return JWT and current user payload.

Rules:

- Registration creates exactly one owner user.
- Workspace ID is assigned server-side.
- Passwords are hashed before storage.

## Product Creation

Flow:

1. User submits product name, optional SKU, category, unit, reorder point, reorder quantity, and description.
2. Backend validates category belongs to current workspace.
3. If SKU is omitted, backend generates one from product name plus a short suffix.
4. Backend inserts product with `status = 'active'`.
5. Backend inserts activity log.
6. Product detail page is returned or fetched.

Rules:

- SKU must be unique per workspace.
- Archived products stay visible in history but are hidden from active selectors by default.
- Reorder point and reorder quantity cannot be negative.

## Warehouse Creation

Flow:

1. User submits warehouse name, code, address, city, country.
2. Backend validates code uniqueness inside workspace.
3. Backend inserts warehouse with `status = 'active'`.
4. Backend inserts activity log.

Rules:

- Warehouse code is unique per workspace.
- Inactive warehouses should not be selectable for new stock movements.

## Stock In

Use case:

- Initial inventory count.
- Manual restock.
- Purchase order completion.

Flow:

1. User submits product, warehouse, quantity, reason, and notes.
2. Backend verifies product and warehouse belong to workspace and are active.
3. Backend starts a transaction.
4. Lock or create the relevant `inventory_balances` row.
5. Increase `on_hand_quantity`.
6. Insert `inventory_movements` with `movement_type = 'stock_in'`.
7. Insert activity log.
8. Recalculate low-stock alert for that product and warehouse.
9. Commit.

Rules:

- Quantity must be positive.
- Stock in increases on-hand stock.
- Reserved quantity does not change.

## Stock Out

Use case:

- Manual removal.
- Damaged goods.
- Non-order correction.

Flow:

1. User submits product, warehouse, quantity, reason, and notes.
2. Backend starts a transaction.
3. Lock the balance row.
4. Calculate available quantity as `on_hand_quantity - reserved_quantity`.
5. Reject if quantity is greater than available quantity.
6. Decrease `on_hand_quantity`.
7. Insert `inventory_movements` with `movement_type = 'stock_out'`.
8. Insert activity log.
9. Recalculate alerts.
10. Commit.

Rules:

- Manual stock out cannot consume reserved stock.
- Available stock must never become negative.

## Stock Transfer

Use case:

- Move inventory from one warehouse to another.

Flow:

1. User submits product, source warehouse, destination warehouse, quantity, and notes.
2. Backend validates source and destination differ.
3. Backend starts a transaction.
4. Lock source and destination balance rows in deterministic order.
5. Validate source available quantity.
6. Decrease source `on_hand_quantity`.
7. Increase destination `on_hand_quantity`.
8. Insert `transfer_out` movement for source.
9. Insert `transfer_in` movement for destination.
10. Insert one activity log summarizing the transfer.
11. Recalculate alerts for both warehouses.
12. Commit.

Rules:

- Transfers cannot move reserved stock.
- Transfers are atomic: both sides succeed or both fail.

## Stock Adjustment

Use case:

- Physical count correction.

Flow:

1. User submits product, warehouse, counted quantity, reason, and notes.
2. Backend starts a transaction.
3. Lock balance row.
4. Validate counted quantity is not below reserved quantity.
5. Compute delta between counted and current on-hand.
6. Set `on_hand_quantity` to counted quantity.
7. Insert `adjustment` movement with absolute delta and before/after values.
8. Insert activity log.
9. Recalculate alerts.
10. Commit.

Rules:

- Physical count cannot invalidate existing reservations.
- Adjustment must include a reason.

## Sales Order Lifecycle

Statuses:

```text
draft -> confirmed -> processing -> shipped -> completed
draft -> cancelled
confirmed -> cancelled
processing -> cancelled
```

### Create Draft Sales Order

Flow:

1. User selects order type `sales`.
2. User selects warehouse and customer name.
3. User adds product items with quantities and unit prices.
4. Backend validates warehouse and products belong to workspace.
5. Backend creates order and items with status `draft`.
6. Backend inserts activity log.

Rules:

- Draft orders do not reserve stock.
- Draft orders can be edited.

### Confirm Sales Order

Flow:

1. User confirms a draft sales order.
2. Backend starts a transaction.
3. Lock all relevant inventory balance rows for the order warehouse.
4. Validate each item has enough available stock.
5. Increase `reserved_quantity` for each item.
6. Insert `reservation` inventory movements.
7. Set order status to `confirmed`.
8. Insert order status activity log.
9. Commit.

Rules:

- Confirmation prevents overselling by reserving stock.
- If any item lacks stock, no reservations are made.

### Process Sales Order

Flow:

1. User moves confirmed order to processing.
2. Backend validates status transition.
3. Backend updates order status and timestamp.
4. Backend inserts activity log.

Rules:

- Processing does not change stock quantities.

### Ship Sales Order

Flow:

1. User ships a processing sales order.
2. Backend starts a transaction.
3. Lock relevant inventory balances.
4. For each item, decrease `on_hand_quantity` and `reserved_quantity`.
5. Insert `order_deduction` inventory movements.
6. Set order status to `shipped`.
7. Insert activity log.
8. Recalculate alerts.
9. Commit.

Rules:

- Shipping consumes previously reserved stock.
- Reserved quantity must not become negative.

### Complete Sales Order

Flow:

1. User completes a shipped order.
2. Backend updates order status to `completed`.
3. Backend inserts activity log.

Rules:

- Completion does not change stock because stock was deducted at shipment.

### Cancel Sales Order

Flow:

1. User cancels a draft, confirmed, or processing order.
2. If order is draft, backend only changes status.
3. If order has reservations, backend starts a transaction.
4. Lock relevant balances.
5. Decrease `reserved_quantity` for each item.
6. Insert `reservation_release` movements.
7. Update order status to `cancelled`.
8. Insert activity log.
9. Commit.

Rules:

- Shipped and completed sales orders cannot be cancelled in version 1.
- Cancellation releases reservations when needed.

## Purchase Order Lifecycle

Statuses:

```text
draft -> confirmed -> processing -> completed
draft -> cancelled
confirmed -> cancelled
processing -> cancelled
```

### Create Draft Purchase Order

Flow:

1. User selects order type `purchase`.
2. User selects supplier and destination warehouse.
3. User adds product items with quantities and unit costs.
4. Backend validates supplier, warehouse, and products belong to workspace.
5. Backend creates order and items with status `draft`.
6. Backend inserts activity log.

Rules:

- Draft purchase orders do not change stock.
- Products should usually be linked to the supplier, but version 1 can warn before strictly enforcing if seed data needs flexibility.

### Confirm Purchase Order

Flow:

1. User confirms draft purchase order.
2. Backend validates supplier-product relationships.
3. Backend updates status to `confirmed`.
4. Backend inserts activity log.

Rules:

- Confirmation does not change stock.

### Complete Purchase Order

Flow:

1. User marks a processing or confirmed purchase order complete.
2. Backend starts a transaction.
3. Lock or create inventory balance rows for destination warehouse.
4. Increase `on_hand_quantity` for every item.
5. Insert `stock_in` inventory movements with order reference.
6. Update order status to `completed`.
7. Insert activity log.
8. Recalculate alerts.
9. Commit.

Rules:

- Purchase order completion is the stock-in event.
- Completion is atomic across all items.

## Low Stock Alerts

Trigger:

- Product available stock in a warehouse is less than or equal to product `reorder_point`.

Flow:

1. Stock mutation completes.
2. Backend computes available stock for affected product and warehouse.
3. If below threshold and no open matching alert exists, create `low_stock` alert.
4. If stock rises above threshold, resolve open matching low-stock alert automatically or mark as resolved by system.

Rules:

- Alerts are workspace-scoped.
- Duplicate open low-stock alerts for the same product and warehouse should be avoided.

## Reorder Suggestions

Trigger:

- Low stock exists and product has supplier relationship or reorder quantity.

Suggestion data:

- Product.
- Warehouse.
- Current available stock.
- Reorder point.
- Suggested reorder quantity.
- Preferred supplier if available.

Rules:

- Reorder suggestions are advisory in version 1.
- Later versions can generate purchase orders from suggestions.

## Stale Order Alerts

Trigger examples:

- Draft order older than a configured threshold.
- Processing order with no status change after a configured threshold.

Flow:

1. Alert recalculation endpoint or background-like manual action runs.
2. Backend finds stale orders with SQL date filtering.
3. Backend creates open alerts when missing.

Rules:

- No background worker is required in version 1.
- Manual recalculation endpoint keeps scope realistic for a portfolio project.

## Activity Logging

Every important mutation should write one activity log row inside the same transaction when possible.

Activity metadata should include useful context:

```json
{
  "product_id": "uuid",
  "warehouse_id": "uuid",
  "quantity": 25,
  "before": 10,
  "after": 35
}
```

Rules:

- Activity logs are append-only.
- Activity feed search should inspect summary, action, and related entity type.


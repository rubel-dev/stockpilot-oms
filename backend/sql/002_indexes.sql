BEGIN;

CREATE UNIQUE INDEX categories_workspace_name_unique_idx
    ON categories (workspace_id, lower(name));

CREATE INDEX products_workspace_status_created_idx
    ON products (workspace_id, status, created_at DESC);

CREATE INDEX products_workspace_category_idx
    ON products (workspace_id, category_id);

CREATE INDEX products_workspace_name_search_idx
    ON products
    USING gin ((coalesce(name, '') || ' ' || coalesce(sku, '') || ' ' || coalesce(description, '')) gin_trgm_ops);

CREATE INDEX warehouses_workspace_status_name_idx
    ON warehouses (workspace_id, status, name);

CREATE INDEX warehouses_workspace_search_idx
    ON warehouses
    USING gin ((coalesce(name, '') || ' ' || coalesce(code, '') || ' ' || coalesce(city, '') || ' ' || coalesce(country, '')) gin_trgm_ops);

CREATE INDEX suppliers_workspace_status_name_idx
    ON suppliers (workspace_id, status, name);

CREATE INDEX suppliers_workspace_search_idx
    ON suppliers
    USING gin ((coalesce(name, '') || ' ' || coalesce(contact_name, '') || ' ' || coalesce(email, '') || ' ' || coalesce(phone, '')) gin_trgm_ops);

CREATE INDEX supplier_products_workspace_supplier_idx
    ON supplier_products (workspace_id, supplier_id, product_id);

CREATE INDEX supplier_products_workspace_product_idx
    ON supplier_products (workspace_id, product_id, supplier_id);

CREATE INDEX inventory_balances_workspace_warehouse_idx
    ON inventory_balances (workspace_id, warehouse_id, product_id);

CREATE INDEX inventory_balances_workspace_product_idx
    ON inventory_balances (workspace_id, product_id, warehouse_id);

CREATE INDEX inventory_balances_workspace_low_stock_idx
    ON inventory_balances (workspace_id, warehouse_id, product_id, on_hand_quantity, reserved_quantity);

CREATE INDEX inventory_movements_workspace_created_idx
    ON inventory_movements (workspace_id, created_at DESC);

CREATE INDEX inventory_movements_workspace_product_created_idx
    ON inventory_movements (workspace_id, product_id, created_at DESC);

CREATE INDEX inventory_movements_workspace_warehouse_created_idx
    ON inventory_movements (workspace_id, warehouse_id, created_at DESC);

CREATE INDEX inventory_movements_workspace_type_created_idx
    ON inventory_movements (workspace_id, movement_type, created_at DESC);

CREATE INDEX orders_workspace_status_created_idx
    ON orders (workspace_id, status, created_at DESC);

CREATE INDEX orders_workspace_type_status_idx
    ON orders (workspace_id, order_type, status);

CREATE INDEX orders_workspace_warehouse_idx
    ON orders (workspace_id, warehouse_id, created_at DESC);

CREATE INDEX orders_workspace_supplier_idx
    ON orders (workspace_id, supplier_id, created_at DESC)
    WHERE supplier_id IS NOT NULL;

CREATE INDEX orders_workspace_search_idx
    ON orders
    USING gin ((coalesce(order_number, '') || ' ' || coalesce(customer_name, '')) gin_trgm_ops);

CREATE INDEX orders_workspace_completed_idx
    ON orders (workspace_id, completed_at DESC)
    WHERE status = 'completed';

CREATE INDEX order_items_workspace_order_idx
    ON order_items (workspace_id, order_id);

CREATE INDEX order_items_workspace_product_idx
    ON order_items (workspace_id, product_id);

CREATE INDEX alerts_workspace_status_severity_created_idx
    ON alerts (workspace_id, status, severity, created_at DESC);

CREATE INDEX alerts_workspace_type_status_idx
    ON alerts (workspace_id, alert_type, status);

CREATE UNIQUE INDEX alerts_open_unique_entity_idx
    ON alerts (workspace_id, alert_type, coalesce(product_id, '00000000-0000-0000-0000-000000000000'::uuid), coalesce(warehouse_id, '00000000-0000-0000-0000-000000000000'::uuid), coalesce(order_id, '00000000-0000-0000-0000-000000000000'::uuid))
    WHERE status = 'open';

CREATE INDEX activity_logs_workspace_created_idx
    ON activity_logs (workspace_id, created_at DESC);

CREATE INDEX activity_logs_workspace_entity_idx
    ON activity_logs (workspace_id, entity_type, entity_id, created_at DESC);

CREATE INDEX activity_logs_workspace_actor_idx
    ON activity_logs (workspace_id, actor_user_id, created_at DESC);

CREATE INDEX activity_logs_workspace_search_idx
    ON activity_logs
    USING gin ((coalesce(action, '') || ' ' || coalesce(entity_type, '') || ' ' || coalesce(summary, '')) gin_trgm_ops);

COMMIT;

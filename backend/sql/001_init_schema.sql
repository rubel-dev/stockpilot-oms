BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS citext;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE workspaces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT workspaces_name_not_blank CHECK (btrim(name) <> ''),
    CONSTRAINT workspaces_slug_not_blank CHECK (btrim(slug) <> '')
);

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    email CITEXT NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT users_name_not_blank CHECK (btrim(name) <> ''),
    CONSTRAINT users_role_valid CHECK (role IN ('owner', 'member')),
    CONSTRAINT users_password_hash_not_blank CHECK (btrim(password_hash) <> ''),
    CONSTRAINT users_email_unique UNIQUE (email),
    CONSTRAINT users_id_workspace_unique UNIQUE (id, workspace_id)
);

CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT categories_name_not_blank CHECK (btrim(name) <> ''),
    CONSTRAINT categories_id_workspace_unique UNIQUE (id, workspace_id)
);

CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    category_id UUID NULL,
    name TEXT NOT NULL,
    sku TEXT NOT NULL,
    description TEXT,
    unit TEXT NOT NULL DEFAULT 'each',
    reorder_point INTEGER NOT NULL DEFAULT 0,
    reorder_quantity INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'active',
    created_by UUID NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT products_name_not_blank CHECK (btrim(name) <> ''),
    CONSTRAINT products_sku_not_blank CHECK (btrim(sku) <> ''),
    CONSTRAINT products_unit_not_blank CHECK (btrim(unit) <> ''),
    CONSTRAINT products_status_valid CHECK (status IN ('active', 'archived')),
    CONSTRAINT products_reorder_point_non_negative CHECK (reorder_point >= 0),
    CONSTRAINT products_reorder_quantity_non_negative CHECK (reorder_quantity >= 0),
    CONSTRAINT products_workspace_sku_unique UNIQUE (workspace_id, sku),
    CONSTRAINT products_id_workspace_unique UNIQUE (id, workspace_id),
    CONSTRAINT products_category_fk
        FOREIGN KEY (category_id, workspace_id)
        REFERENCES categories(id, workspace_id)
        ON DELETE SET NULL,
    CONSTRAINT products_created_by_fk
        FOREIGN KEY (created_by, workspace_id)
        REFERENCES users(id, workspace_id)
        ON DELETE SET NULL
);

CREATE TABLE warehouses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    code TEXT NOT NULL,
    address_line1 TEXT,
    address_line2 TEXT,
    city TEXT,
    state_region TEXT,
    postal_code TEXT,
    country TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT warehouses_name_not_blank CHECK (btrim(name) <> ''),
    CONSTRAINT warehouses_code_not_blank CHECK (btrim(code) <> ''),
    CONSTRAINT warehouses_status_valid CHECK (status IN ('active', 'inactive')),
    CONSTRAINT warehouses_workspace_code_unique UNIQUE (workspace_id, code),
    CONSTRAINT warehouses_id_workspace_unique UNIQUE (id, workspace_id)
);

CREATE TABLE suppliers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    contact_name TEXT,
    email TEXT,
    phone TEXT,
    address TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT suppliers_name_not_blank CHECK (btrim(name) <> ''),
    CONSTRAINT suppliers_status_valid CHECK (status IN ('active', 'inactive')),
    CONSTRAINT suppliers_id_workspace_unique UNIQUE (id, workspace_id)
);

CREATE TABLE supplier_products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    supplier_id UUID NOT NULL,
    product_id UUID NOT NULL,
    supplier_sku TEXT,
    lead_time_days INTEGER,
    minimum_order_quantity INTEGER NOT NULL DEFAULT 0,
    unit_cost NUMERIC(12, 2),
    is_preferred BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT supplier_products_moq_non_negative CHECK (minimum_order_quantity >= 0),
    CONSTRAINT supplier_products_lead_time_non_negative CHECK (lead_time_days IS NULL OR lead_time_days >= 0),
    CONSTRAINT supplier_products_unit_cost_non_negative CHECK (unit_cost IS NULL OR unit_cost >= 0),
    CONSTRAINT supplier_products_unique UNIQUE (workspace_id, supplier_id, product_id),
    CONSTRAINT supplier_products_supplier_fk
        FOREIGN KEY (supplier_id, workspace_id)
        REFERENCES suppliers(id, workspace_id)
        ON DELETE CASCADE,
    CONSTRAINT supplier_products_product_fk
        FOREIGN KEY (product_id, workspace_id)
        REFERENCES products(id, workspace_id)
        ON DELETE CASCADE
);

CREATE TABLE inventory_balances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    product_id UUID NOT NULL,
    warehouse_id UUID NOT NULL,
    on_hand_quantity INTEGER NOT NULL DEFAULT 0,
    reserved_quantity INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT inventory_balances_on_hand_non_negative CHECK (on_hand_quantity >= 0),
    CONSTRAINT inventory_balances_reserved_non_negative CHECK (reserved_quantity >= 0),
    CONSTRAINT inventory_balances_reserved_lte_on_hand CHECK (reserved_quantity <= on_hand_quantity),
    CONSTRAINT inventory_balances_unique UNIQUE (workspace_id, product_id, warehouse_id),
    CONSTRAINT inventory_balances_product_fk
        FOREIGN KEY (product_id, workspace_id)
        REFERENCES products(id, workspace_id)
        ON DELETE CASCADE,
    CONSTRAINT inventory_balances_warehouse_fk
        FOREIGN KEY (warehouse_id, workspace_id)
        REFERENCES warehouses(id, workspace_id)
        ON DELETE CASCADE
);

CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    order_number TEXT NOT NULL,
    order_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    warehouse_id UUID NOT NULL,
    supplier_id UUID NULL,
    customer_name TEXT NULL,
    notes TEXT,
    subtotal_amount NUMERIC(12, 2) NOT NULL DEFAULT 0,
    created_by UUID NULL,
    confirmed_at TIMESTAMPTZ NULL,
    processed_at TIMESTAMPTZ NULL,
    shipped_at TIMESTAMPTZ NULL,
    completed_at TIMESTAMPTZ NULL,
    cancelled_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT orders_order_number_not_blank CHECK (btrim(order_number) <> ''),
    CONSTRAINT orders_order_type_valid CHECK (order_type IN ('sales', 'purchase')),
    CONSTRAINT orders_status_valid CHECK (status IN ('draft', 'confirmed', 'processing', 'shipped', 'completed', 'cancelled')),
    CONSTRAINT orders_subtotal_non_negative CHECK (subtotal_amount >= 0),
    CONSTRAINT orders_unique_number UNIQUE (workspace_id, order_number),
    CONSTRAINT orders_id_workspace_unique UNIQUE (id, workspace_id),
    CONSTRAINT orders_warehouse_fk
        FOREIGN KEY (warehouse_id, workspace_id)
        REFERENCES warehouses(id, workspace_id)
        ON DELETE RESTRICT,
    CONSTRAINT orders_supplier_fk
        FOREIGN KEY (supplier_id, workspace_id)
        REFERENCES suppliers(id, workspace_id)
        ON DELETE RESTRICT,
    CONSTRAINT orders_created_by_fk
        FOREIGN KEY (created_by, workspace_id)
        REFERENCES users(id, workspace_id)
        ON DELETE SET NULL,
    CONSTRAINT orders_purchase_requires_supplier CHECK (
        (order_type = 'purchase' AND supplier_id IS NOT NULL)
        OR (order_type = 'sales' AND supplier_id IS NULL)
    ),
    CONSTRAINT orders_sales_requires_customer CHECK (
        (order_type = 'sales' AND customer_name IS NOT NULL AND btrim(customer_name) <> '')
        OR (order_type = 'purchase' AND customer_name IS NULL)
    ),
    CONSTRAINT orders_status_timestamps_consistent CHECK (
        (confirmed_at IS NULL OR confirmed_at >= created_at)
        AND (processed_at IS NULL OR confirmed_at IS NOT NULL)
        AND (shipped_at IS NULL OR processed_at IS NOT NULL)
        AND (completed_at IS NULL OR (
            (order_type = 'sales' AND shipped_at IS NOT NULL)
            OR (order_type = 'purchase' AND confirmed_at IS NOT NULL)
        ))
        AND (cancelled_at IS NULL OR status = 'cancelled')
    )
);

CREATE TABLE order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    order_id UUID NOT NULL,
    product_id UUID NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(12, 2),
    unit_cost NUMERIC(12, 2),
    line_total NUMERIC(12, 2) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT order_items_quantity_positive CHECK (quantity > 0),
    CONSTRAINT order_items_unit_price_non_negative CHECK (unit_price IS NULL OR unit_price >= 0),
    CONSTRAINT order_items_unit_cost_non_negative CHECK (unit_cost IS NULL OR unit_cost >= 0),
    CONSTRAINT order_items_line_total_non_negative CHECK (line_total >= 0),
    CONSTRAINT order_items_order_fk
        FOREIGN KEY (order_id, workspace_id)
        REFERENCES orders(id, workspace_id)
        ON DELETE CASCADE,
    CONSTRAINT order_items_product_fk
        FOREIGN KEY (product_id, workspace_id)
        REFERENCES products(id, workspace_id)
        ON DELETE RESTRICT
);

CREATE TABLE inventory_movements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    product_id UUID NOT NULL,
    warehouse_id UUID NOT NULL,
    destination_warehouse_id UUID NULL,
    movement_type TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    quantity_before INTEGER NOT NULL,
    quantity_after INTEGER NOT NULL,
    reason TEXT,
    reference_type TEXT,
    reference_id UUID,
    notes TEXT,
    created_by UUID NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT inventory_movements_type_valid CHECK (
        movement_type IN (
            'stock_in',
            'stock_out',
            'transfer_out',
            'transfer_in',
            'adjustment',
            'reservation',
            'reservation_release',
            'order_deduction'
        )
    ),
    CONSTRAINT inventory_movements_quantity_positive CHECK (quantity > 0),
    CONSTRAINT inventory_movements_before_non_negative CHECK (quantity_before >= 0),
    CONSTRAINT inventory_movements_after_non_negative CHECK (quantity_after >= 0),
    CONSTRAINT inventory_movements_transfer_destination_valid CHECK (
        (movement_type IN ('transfer_out', 'transfer_in') AND destination_warehouse_id IS NOT NULL AND destination_warehouse_id <> warehouse_id)
        OR (movement_type NOT IN ('transfer_out', 'transfer_in') AND destination_warehouse_id IS NULL)
    ),
    CONSTRAINT inventory_movements_product_fk
        FOREIGN KEY (product_id, workspace_id)
        REFERENCES products(id, workspace_id)
        ON DELETE RESTRICT,
    CONSTRAINT inventory_movements_warehouse_fk
        FOREIGN KEY (warehouse_id, workspace_id)
        REFERENCES warehouses(id, workspace_id)
        ON DELETE RESTRICT,
    CONSTRAINT inventory_movements_destination_warehouse_fk
        FOREIGN KEY (destination_warehouse_id, workspace_id)
        REFERENCES warehouses(id, workspace_id)
        ON DELETE RESTRICT,
    CONSTRAINT inventory_movements_created_by_fk
        FOREIGN KEY (created_by, workspace_id)
        REFERENCES users(id, workspace_id)
        ON DELETE SET NULL
);

CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    alert_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    product_id UUID NULL,
    warehouse_id UUID NULL,
    order_id UUID NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    resolved_by UUID NULL,
    resolved_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT alerts_type_valid CHECK (alert_type IN ('low_stock', 'reorder_suggestion', 'stale_order', 'stuck_processing')),
    CONSTRAINT alerts_severity_valid CHECK (severity IN ('info', 'warning', 'critical')),
    CONSTRAINT alerts_status_valid CHECK (status IN ('open', 'resolved', 'dismissed')),
    CONSTRAINT alerts_title_not_blank CHECK (btrim(title) <> ''),
    CONSTRAINT alerts_message_not_blank CHECK (btrim(message) <> ''),
    CONSTRAINT alerts_resolved_consistency CHECK (
        (status = 'open' AND resolved_at IS NULL AND resolved_by IS NULL)
        OR (status IN ('resolved', 'dismissed'))
    ),
    CONSTRAINT alerts_product_fk
        FOREIGN KEY (product_id, workspace_id)
        REFERENCES products(id, workspace_id)
        ON DELETE CASCADE,
    CONSTRAINT alerts_warehouse_fk
        FOREIGN KEY (warehouse_id, workspace_id)
        REFERENCES warehouses(id, workspace_id)
        ON DELETE CASCADE,
    CONSTRAINT alerts_order_fk
        FOREIGN KEY (order_id, workspace_id)
        REFERENCES orders(id, workspace_id)
        ON DELETE CASCADE,
    CONSTRAINT alerts_resolved_by_fk
        FOREIGN KEY (resolved_by, workspace_id)
        REFERENCES users(id, workspace_id)
        ON DELETE SET NULL
);

CREATE TABLE activity_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    actor_user_id UUID NULL,
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id UUID NULL,
    summary TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT activity_logs_action_not_blank CHECK (btrim(action) <> ''),
    CONSTRAINT activity_logs_entity_type_not_blank CHECK (btrim(entity_type) <> ''),
    CONSTRAINT activity_logs_summary_not_blank CHECK (btrim(summary) <> ''),
    CONSTRAINT activity_logs_actor_user_fk
        FOREIGN KEY (actor_user_id, workspace_id)
        REFERENCES users(id, workspace_id)
        ON DELETE SET NULL
);

COMMIT;

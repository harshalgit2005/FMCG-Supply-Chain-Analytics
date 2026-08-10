USE fmcg_supply_chain;


-- =========================================================
-- SALES INDEXES
-- =========================================================

CREATE INDEX idx_sales_date
ON fact_sales(date_id);

CREATE INDEX idx_sales_product
ON fact_sales(product_id);

CREATE INDEX idx_sales_store
ON fact_sales(store_id);


-- =========================================================
-- INVENTORY INDEXES
-- =========================================================

CREATE INDEX idx_inventory_date
ON fact_inventory(date_id);

CREATE INDEX idx_inventory_product
ON fact_inventory(product_id);

CREATE INDEX idx_inventory_warehouse
ON fact_inventory(warehouse_id);


-- =========================================================
-- PURCHASE ORDER INDEXES
-- =========================================================

CREATE INDEX idx_po_supplier
ON fact_purchase_orders(supplier_id);

CREATE INDEX idx_po_product
ON fact_purchase_orders(product_id);

CREATE INDEX idx_po_warehouse
ON fact_purchase_orders(warehouse_id);

CREATE INDEX idx_po_date
ON fact_purchase_orders(date_id);


-- =========================================================
-- SHIPMENT INDEXES
-- =========================================================

CREATE INDEX idx_shipments_po
ON fact_shipments(po_id);

CREATE INDEX idx_shipments_warehouse
ON fact_shipments(warehouse_id);

CREATE INDEX idx_shipments_store
ON fact_shipments(store_id);

CREATE INDEX idx_shipments_delivery
ON fact_shipments(actual_delivery_date);


-- =========================================================
-- AGING INDEXES
-- =========================================================

CREATE INDEX idx_aging_product
ON fact_inventory_aging(product_id);

CREATE INDEX idx_aging_warehouse
ON fact_inventory_aging(warehouse_id);

CREATE INDEX idx_aging_risk
ON fact_inventory_aging(expiry_risk);

CREATE INDEX idx_aging_expiry
ON fact_inventory_aging(expiry_date);
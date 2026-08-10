-- =========================================================
-- FMCG SUPPLY CHAIN ANALYTICS
-- DATABASE SCHEMA
-- =========================================================

DROP DATABASE IF EXISTS fmcg_supply_chain;

CREATE DATABASE fmcg_supply_chain;

USE fmcg_supply_chain;


-- =========================================================
-- DIMENSION: PRODUCT
-- =========================================================

CREATE TABLE dim_product (

    product_id VARCHAR(30) NOT NULL,

    product_name VARCHAR(255),

    brand VARCHAR(150),

    category VARCHAR(100),

    subcategory VARCHAR(100),

    unit_size DECIMAL(12,2),

    unit_of_measure VARCHAR(30),

    shelf_life_days INT,

    unit_cost DECIMAL(12,2),

    selling_price DECIMAL(12,2),

    PRIMARY KEY (product_id)

);


-- =========================================================
-- DIMENSION: SUPPLIER
-- =========================================================

CREATE TABLE dim_supplier (

    supplier_id VARCHAR(30) NOT NULL,

    supplier_name VARCHAR(255),

    supplier_region VARCHAR(100),

    supplier_type VARCHAR(100),

    supplier_rating DECIMAL(5,2),

    contract_type VARCHAR(100),

    PRIMARY KEY (supplier_id)

);


-- =========================================================
-- DIMENSION: WAREHOUSE
-- =========================================================

CREATE TABLE dim_warehouse (

    warehouse_id VARCHAR(30) NOT NULL,

    warehouse_name VARCHAR(255),

    city VARCHAR(100),

    state VARCHAR(100),

    warehouse_type VARCHAR(100),

    capacity_units BIGINT,

    PRIMARY KEY (warehouse_id)

);


-- =========================================================
-- DIMENSION: STORE
-- =========================================================

CREATE TABLE dim_store (

    store_id VARCHAR(30) NOT NULL,

    store_name VARCHAR(255),

    city VARCHAR(100),

    state VARCHAR(100),

    store_type VARCHAR(100),

    region VARCHAR(100),

    PRIMARY KEY (store_id)

);


-- =========================================================
-- DIMENSION: DATE
-- =========================================================

CREATE TABLE dim_date (

    date_id INT NOT NULL,

    date DATE NOT NULL,

    day INT,

    month INT,

    month_name VARCHAR(20),

    quarter INT,

    year INT,

    week INT,

    day_of_week INT,

    day_name VARCHAR(20),

    PRIMARY KEY (date_id),

    UNIQUE KEY uq_dim_date_date (date)

);


-- =========================================================
-- FACT: SALES
-- =========================================================

CREATE TABLE fact_sales (

    sale_id VARCHAR(40) NOT NULL,

    date_id INT NOT NULL,

    product_id VARCHAR(30) NOT NULL,

    store_id VARCHAR(30) NOT NULL,

    quantity_sold INT,

    unit_price DECIMAL(12,2),

    discount DECIMAL(12,4),

    sales_amount DECIMAL(15,2),

    revenue DECIMAL(15,2),

    gross_sales DECIMAL(15,2),

    PRIMARY KEY (sale_id),

    FOREIGN KEY (date_id)
        REFERENCES dim_date(date_id),

    FOREIGN KEY (product_id)
        REFERENCES dim_product(product_id),

    FOREIGN KEY (store_id)
        REFERENCES dim_store(store_id)

);


-- =========================================================
-- FACT: INVENTORY
-- =========================================================

CREATE TABLE fact_inventory (

    inventory_id VARCHAR(50) NOT NULL,

    date_id INT NOT NULL,

    product_id VARCHAR(30) NOT NULL,

    warehouse_id VARCHAR(30) NOT NULL,

    opening_stock BIGINT,

    demand_units BIGINT,

    received_units BIGINT,

    sold_units BIGINT,

    closing_stock BIGINT,

    damaged_units BIGINT,

    expired_units BIGINT,

    stockout_units BIGINT,

    inventory_value DECIMAL(18,2),

    stockout_rate DECIMAL(12,6),

    PRIMARY KEY (inventory_id),

    FOREIGN KEY (date_id)
        REFERENCES dim_date(date_id),

    FOREIGN KEY (product_id)
        REFERENCES dim_product(product_id),

    FOREIGN KEY (warehouse_id)
        REFERENCES dim_warehouse(warehouse_id)

);


-- =========================================================
-- FACT: PURCHASE ORDERS
-- =========================================================

CREATE TABLE fact_purchase_orders (

    po_id VARCHAR(40) NOT NULL,

    date_id INT,

    supplier_id VARCHAR(30) NOT NULL,

    product_id VARCHAR(30) NOT NULL,

    warehouse_id VARCHAR(30) NOT NULL,

    ordered_quantity BIGINT,

    received_quantity BIGINT,

    unit_cost DECIMAL(12,2),

    order_status VARCHAR(50),

    PRIMARY KEY (po_id),

    FOREIGN KEY (date_id)
        REFERENCES dim_date(date_id),

    FOREIGN KEY (supplier_id)
        REFERENCES dim_supplier(supplier_id),

    FOREIGN KEY (product_id)
        REFERENCES dim_product(product_id),

    FOREIGN KEY (warehouse_id)
        REFERENCES dim_warehouse(warehouse_id)

);


-- =========================================================
-- FACT: SHIPMENTS
-- =========================================================

CREATE TABLE fact_shipments (

    shipment_id VARCHAR(40) NOT NULL,

    po_id VARCHAR(40),

    warehouse_id VARCHAR(30) NOT NULL,

    store_id VARCHAR(30) NOT NULL,

    shipment_date DATE,

    expected_delivery_date DATE,

    actual_delivery_date DATE,

    ordered_quantity BIGINT,

    quantity_shipped BIGINT,

    quantity_delivered BIGINT,

    damage_units BIGINT,

    delivery_delay_days INT,

    fill_rate DECIMAL(12,6),

    on_time_flag TINYINT,

    shipping_cost DECIMAL(15,2),

    damage_rate DECIMAL(12,6),

    late_shipment_flag TINYINT,

    PRIMARY KEY (shipment_id),

    FOREIGN KEY (po_id)
        REFERENCES fact_purchase_orders(po_id),

    FOREIGN KEY (warehouse_id)
        REFERENCES dim_warehouse(warehouse_id),

    FOREIGN KEY (store_id)
        REFERENCES dim_store(store_id)

);


-- =========================================================
-- FACT: INVENTORY AGING
-- =========================================================

CREATE TABLE fact_inventory_aging (

    lot_id VARCHAR(50) NOT NULL,

    shipment_id VARCHAR(40),

    po_id VARCHAR(40),

    product_id VARCHAR(30) NOT NULL,

    warehouse_id VARCHAR(30) NOT NULL,

    receipt_date DATE,

    expiry_date DATE,

    received_units BIGINT,

    remaining_units BIGINT,

    unit_cost DECIMAL(12,2),

    shelf_life_days INT,

    analysis_date DATE,

    age_days INT,

    remaining_shelf_life_days INT,

    age_bucket VARCHAR(30),

    expiry_risk VARCHAR(30),

    inventory_value DECIMAL(18,2),

    expiry_risk_value DECIMAL(18,2),

    expiry_risk_flag TINYINT,

    PRIMARY KEY (lot_id),

    FOREIGN KEY (product_id)
        REFERENCES dim_product(product_id),

    FOREIGN KEY (warehouse_id)
        REFERENCES dim_warehouse(warehouse_id)

);
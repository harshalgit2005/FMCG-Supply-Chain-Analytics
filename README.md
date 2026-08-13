# 📦 FMCG Supply Chain Performance & Inventory Analytics

### Are we keeping the right inventory at the right location at the right time while minimizing stockouts, expiry losses, and logistics costs?

**Answer:** Built an end-to-end FMCG Supply Chain Analytics platform using live product data, synthetic operational data, Python, MySQL, SQL, and Power BI to monitor inventory performance, supplier efficiency, logistics operations, and sales across the supply chain.

---

# Project Overview

Modern FMCG companies process millions of inventory transactions every year. Poor inventory planning leads to stockouts, excess inventory, expiry losses, delayed deliveries, and increased logistics costs.

In this project, I worked as a **Data Analyst** supporting the Supply Chain & Operations team. The objective was to build a complete analytics pipeline that combines live product master data with simulated operational data to monitor inventory, sales, supplier performance, warehouse operations, and logistics through interactive Power BI dashboards.

The project demonstrates a complete Business Intelligence workflow from API data collection to executive dashboards.

---

# Business Problem

An FMCG company's operations leadership wants answers to questions such as:

- Which products generate the highest revenue?
- Which warehouses frequently experience stockouts?
- Which suppliers consistently deliver on time?
- How much inventory is at risk of expiry?
- Which regions contribute the most sales?
- Where can logistics costs be reduced?
- How efficiently is inventory being converted into sales?

Instead of relying on disconnected reports, this project creates a centralized analytics platform for end-to-end supply chain monitoring.

---

# Project Architecture

```text
Open Food Facts API
        │
        ▼
Python API Extraction
        │
        ▼
Raw Product Data
        │
        ▼
Synthetic Operational Data Generation
        │
        ▼
Pandas Data Cleaning & Validation
        │
        ▼
MySQL Database
        │
        ▼
SQL Analytics
        │
        ▼
Feature Engineering
        │
        ▼
Power BI Dashboard
        │
        ▼
Business Recommendations
```

---

# Dashboard Preview

## Dashboard 1 — Executive Overview

<p align="center">
<img src="images/executive overview.jpeg" width="100%">
</p>

Provides an executive snapshot of sales performance, inventory value, OTIF, stockouts, inventory turnover, and overall supply chain health.

---

## Dashboard 2 — Sales & Demand Analysis

<p align="center">
<img src="images/sales and demand analysis.png" width="100%">
</p>

Analyzes revenue trends, category performance, regional sales, monthly demand, and top-performing brands.

---

## Dashboard 3 — Inventory Analytics

<p align="center">
<img src="images/inventory analytics.png" width="100%">
</p>

Monitors warehouse inventory, stock availability, inventory turnover, stockouts, inventory aging, and expiry risks.

---

## Dashboard 4 — Supplier & Logistics Performance

<p align="center">
<img src="images/supplier and logistics performance.png" width="100%">
</p>

Measures supplier reliability using fill rate, OTIF, delivery delays, shipping costs, and logistics efficiency.

---

## Dashboard 5 — Operational KPIs

<p align="center">
<img src="images/operational kpis.png" width="100%">
</p>

Tracks operational performance using supply chain KPIs, warehouse utilization, logistics costs, damaged inventory, and inventory movement.

---

# Tech Stack

| Category | Technologies |
|----------|--------------|
| Programming | Python |
| Data Collection | Open Food Facts API |
| Data Processing | Pandas, NumPy |
| Database | MySQL |
| SQL | MySQL Queries, Joins, Window Functions, CTEs |
| Visualization | Power BI |
| Version Control | Git & GitHub |

---

# Data Source

## Live Data

**Open Food Facts API**

Provides:

- Product Name
- Brand
- Category
- Packaging
- Ingredients
- Country
- Product Labels

---

## Generated Operational Data

Python-generated datasets simulate realistic FMCG operations including:

- Sales
- Inventory
- Purchase Orders
- Shipments
- Inventory Aging
- Warehouses
- Suppliers
- Retail Stores

---

# Dataset Information

| Attribute | Value |
|------------|-------|
| Product Source | Open Food Facts API |
| Operational Data | Python Generated |
| Time Period | 2 Years |
| Products | 97 |
| Suppliers | 20 |
| Warehouses | 8 |
| Stores | 100 |
| Sales Records | 73,000 |
| Inventory Records | 5,840 |
| Purchase Orders | 839 |
| Shipments | 839 |
| Dashboard | Power BI |

---

# Database Schema

## Dimension Tables

- Product
- Supplier
- Warehouse
- Store
- Date

---

## Fact Tables

- Sales
- Inventory
- Purchase Orders
- Shipments
- Inventory Aging

---

# Methodology

## 1. Data Collection

- Extracted live FMCG product information using the Open Food Facts API.
- Stored raw datasets for traceability.

---

## 2. Data Generation

Developed Python generators to create realistic operational datasets including:

- Sales Transactions
- Inventory
- Purchase Orders
- Shipments
- Inventory Aging

---

## 3. Data Cleaning

Using Pandas:

- Removed duplicate records
- Corrected data types
- Standardized fields
- Validated foreign keys
- Cleaned missing values

---

## 4. Database Design

Designed a Star Schema consisting of:

- 5 Dimension Tables
- 5 Fact Tables

Implemented:

- Primary Keys
- Foreign Keys
- Relational Integrity

---

## 5. SQL Analytics

Performed analytical SQL using:

- INNER JOIN
- LEFT JOIN
- GROUP BY
- Aggregate Functions
- Window Functions
- CTEs
- CASE Statements

---

## 6. Feature Engineering

Created KPIs including:

- Revenue
- Units Sold
- Inventory Turnover
- Stockout Rate
- Inventory Value
- Fill Rate
- OTIF
- Shipping Cost
- Damage Rate
- Expiry Risk

---

## 7. Dashboard Development

Connected Power BI directly to MySQL and built five interactive dashboards for supply chain decision-making.

---

# Key Findings

- Generated over **₹1.07 Billion** in simulated sales across **73,000** transactions.
- Managed inventory across **8 warehouses** supplying **100 retail stores**.
- Average shipment fill rate reached **90.8%**.
- Approximately **11.6%** of shipments experienced delivery delays.
- Inventory aging highlighted products nearing expiry, enabling proactive stock management.

---

# Business Recommendations

| Recommendation | Owner | Expected Outcome |
|---------------|-------|------------------|
| Increase safety stock for high-demand products | Inventory Team | Reduce stockouts |
| Prioritize reliable suppliers | Procurement | Improve OTIF |
| Rebalance warehouse inventory | Supply Chain | Lower holding costs |
| Monitor aging inventory weekly | Category Managers | Reduce expiry losses |
| Optimize logistics routes | Logistics Team | Reduce transportation costs |

---

# Limitations & Assumptions

- Product master data comes from a public API.
- Operational datasets are synthetically generated.
- Customer-level behavior is outside the scope.
- External market conditions are not modeled.
- Forecasting models are reserved for future versions.

---

# Repository Structure

```text
fmcg-supply-chain-analytics/
│
├── data/
│   ├── raw/
│   └── processed/
│
├── dashboard/
│   └── fmcg_supply_chain.pbix
│
├── images/
│   ├── executive overview.png
│   ├── sales and demand analysis.png
│   ├── inventory analytics.png
│   ├── supplier and logistics performance.png
│   └── operational kpis.png
│
├── notebooks/
├── sql/
├── src/
│   ├── api/
│   ├── data_generation/
│   ├── database/
│   ├── etl/
│   ├── features/
│   └── validation/
│
├── README.md
├── requirements.txt
└── main.py
```

---

# How to Reproduce

### Clone the repository

```bash
git clone https://github.com/yourusername/fmcg-supply-chain-analytics.git
```

### Create a virtual environment

```bash
python -m venv .venv
```

### Activate the environment

```bash
.venv\Scripts\activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Configure MySQL

Create a `.env` file:

```text
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=fmcg_supply_chain
```

### Generate Data

```bash
python src/api/fetch_products.py

python src/data_generation/generate_sales.py
python src/data_generation/generate_inventory.py
python src/data_generation/generate_purchase_orders.py
python src/data_generation/generate_shipments.py
python src/data_generation/generate_inventory_aging.py
```

### Load into MySQL

```bash
python src/database/load_mysql.py
```

### Open Power BI

Open:

```text
dashboard/fmcg_supply_chain.pbix
```

Refresh the report.

---

# Future Improvements

- Live ERP integration
- Demand Forecasting
- ML-based Stockout Prediction
- Power BI Service Deployment
- Streamlit Dashboard
- Automated ETL Scheduling

---

# Author

**Harshal Saudagar**

Aspiring Data Analyst | Python | SQL | MySQL | Power BI | ETL | Supply Chain Analytics | Business Intelligence

If you found this project useful, consider giving the repository a ⭐.

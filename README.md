# FMCG Supply Chain Performance & Inventory Analytics

### Are we keeping the right inventory at the right location at the right time while minimizing stockouts, overstocking, expiry, and logistics costs?

**Answer:** Built an end-to-end FMCG supply chain analytics platform using live product data, economic indicators, synthetic operational datasets, Python ETL, MySQL, SQL analytics, and Power BI to identify inventory inefficiencies, supplier performance issues, and opportunities to improve supply chain operations.

---

# Project Overview

Modern FMCG companies manage thousands of products across suppliers, warehouses, distributors, and retail stores. Poor inventory planning can lead to stockouts, excess inventory, product expiry, delayed deliveries, and increased logistics costs.

In this project, I worked as a **Data Analyst** supporting the Supply Chain and Operations team of a large FMCG company. The objective was to design and build a complete analytics platform that integrates live master data with realistic operational data, transforms it into business-ready datasets, stores it in a relational database, and delivers interactive dashboards for executive decision-making.

The project demonstrates a complete data analytics workflow—from API integration and ETL to SQL validation and Power BI reporting.

---

# Business Problem

The Supply Chain Director wants to answer questions such as:

- Are we keeping the right inventory levels across warehouses?
- Which products generate the highest revenue?
- Which suppliers consistently deliver on time?
- Where are stockouts occurring most frequently?
- Which warehouses carry excessive inventory?
- How much inventory is at risk of expiry?
- What factors contribute most to supply chain costs?

Instead of relying on static spreadsheets, this project builds a centralized analytics platform to support inventory optimization and operational decision-making.

---

# Project Architecture

```text
Open Food Facts API            FRED API
        │                         │
        └──────────────┬──────────┘
                       ▼
              Python API Extraction
                       │
                       ▼
               Raw Data Collection
                       │
                       ▼
          Pandas Cleaning & Transformation
                       │
                       ▼
     Synthetic Operational Data Generation
                       │
                       ▼
                 Processed CSV Files
                       │
                       ▼
                 MySQL Database
                       │
                       ▼
                 SQL Analytics
                       │
                       ▼
              Power BI Dashboards
                       │
                       ▼
          Business Insights & Decisions
```

---

# Tech Stack

| Category | Technologies |
|-----------|--------------|
| Programming | Python |
| APIs | Open Food Facts API, FRED API |
| Data Processing | Pandas, NumPy |
| Database | MySQL |
| SQL | Joins, CTEs, Window Functions, Aggregations |
| Visualization | Power BI |
| Version Control | Git & GitHub |

---

# Data Sources

## Open Food Facts API

Provides live FMCG product master data including:

- Product Name
- Brand
- Category
- Packaging
- Product Codes

---

## FRED API

Provides macroeconomic indicators used for realistic demand simulation.

Examples include:

- Consumer Price Index
- Retail Sales Indicators
- Inflation Trends

---

## Synthetic Operational Data

Business-rule driven datasets generated using Python:

- Sales
- Inventory
- Purchase Orders
- Shipments
- Inventory Aging

---

# Dataset Information

| Attribute | Value |
|------------|-------|
| Product Source | Open Food Facts API |
| Economic Source | FRED API |
| Operational Data | Synthetic |
| Storage | MySQL |
| Format | CSV |
| Time Span | 2 Years |
| Products | 97 |
| Suppliers | 20 |
| Warehouses | 8 |
| Stores | 100 |
| Sales Records | 73,000 |
| Inventory Records | 5,840 |
| Purchase Orders | 839 |
| Shipments | 839 |

---

# Database Schema

## Dimension Tables

| Table | Description |
|--------|-------------|
| dim_product | Product master |
| dim_supplier | Supplier information |
| dim_store | Retail stores |
| dim_warehouse | Warehouse master |
| dim_date | Calendar dimension |

---

## Fact Tables

| Table | Description |
|--------|-------------|
| fact_sales | Daily sales transactions |
| fact_inventory | Daily warehouse inventory |
| fact_purchase_orders | Procurement orders |
| fact_shipments | Shipment performance |
| fact_inventory_aging | Expiry risk inventory |

---

# Methodology

## 1. Live Data Collection

- Extracted product master data from Open Food Facts API.
- Retrieved macroeconomic indicators from the FRED API.
- Stored raw API responses for reproducibility.

---

## 2. Data Cleaning

Using Pandas:

- Removed duplicate records
- Standardized categories
- Cleaned missing values
- Converted data types
- Validated product attributes

---

## 3. Operational Data Generation

Generated realistic operational datasets using business rules:

- Sales simulation
- Inventory movement
- Purchase order generation
- Shipment simulation
- Inventory aging
- Supplier lead times

---

## 4. Data Storage

Loaded processed datasets into MySQL with:

- Primary Keys
- Foreign Keys
- Referential Integrity
- Data Validation

---

## 5. SQL Analytics

Performed analytical SQL using:

- INNER JOIN
- LEFT JOIN
- GROUP BY
- HAVING
- Window Functions
- Common Table Expressions (CTEs)
- Aggregate Functions

---

## 6. Dashboard Development

Connected Power BI directly to MySQL and developed five interactive dashboards for executive reporting.

---

# Dashboard 1 — Executive Overview

<p align="center">
<img src="images/executive overview.jpeg" width="100%">
</p>

Provides an executive summary of supply chain performance, including sales, inventory, logistics, supplier performance, and key operational KPIs.

---

# Dashboard 2 — Sales & Demand Analytics

<p align="center">
<img src="images/sales and demand analytics.jpeg" width="100%">
</p>

Analyzes revenue, units sold, demand trends, product performance, regional sales, and customer demand patterns.

---

# Dashboard 3 — Inventory Analytics

<p align="center">
<img src="images/inventory analytics.jpeg" width="100%">
</p>

Evaluates inventory value, stock availability, warehouse utilization, inventory turnover, stockouts, damaged inventory, and inventory health.

---

# Dashboard 4 — Supplier Performance

<p align="center">
<img src="images/supplier performance.jpeg" width="100%">
</p>

Measures supplier reliability using purchase orders, lead times, fill rates, shipping costs, damage rates, and on-time delivery metrics.


---

# Key Findings

Analysis of over **73,000 sales transactions** and **839 purchase orders** identified several operational insights:

- Generated over **₹1.07 Billion** in simulated sales revenue across 97 FMCG products.
- Inventory was distributed across **8 warehouses** supporting **100 retail stores**.
- Average shipment fill rate exceeded **90%**, indicating generally strong supplier fulfillment.
- Approximately **1.7% of shipped units** were damaged during transportation, increasing logistics costs.
- Late deliveries represented an operational risk affecting warehouse replenishment and inventory availability.
- Inventory aging highlighted products approaching expiry, creating opportunities to reduce wastage through better inventory rotation.

---

# Business Recommendations

| Recommendation | Owner | Expected Outcome |
|---------------|-------|------------------|
| Improve replenishment planning for warehouses with frequent stockouts | Inventory Planning Team | Reduce stockout rate |
| Negotiate performance improvements with suppliers having high lead times | Procurement Team | Faster replenishment |
| Monitor damaged shipments and optimize logistics partners | Logistics Team | Lower transportation losses |
| Prioritize FEFO (First Expiry First Out) inventory rotation | Warehouse Operations | Reduce expiry costs |
| Continuously monitor inventory turnover and stock levels | Supply Chain Management | Improve working capital efficiency |

---

# Limitations & Assumptions

- Product master data is obtained from the Open Food Facts API.
- Operational datasets are synthetically generated using business rules.
- Demand patterns are simulated and may not fully represent real-world purchasing behavior.
- Transportation routes, weather, promotions, and competitor activities are not modeled.
- Economic indicators are used only to improve demand realism.

---

# Repository Structure

```text
FMCG-Supply-Chain-Analytics/
│
├── config/
│   └── config.example.env
│
├── dashboard/
│   ├── Executive Overview.pbix
│   ├── Sales & Demand Analysis.pbix
│   ├── Inventory Analytics.pbix
│   └── Supplier Performance.pbix
│
├── data/
│   ├── raw/
│   │   ├── fred/
│   │   └── operational/
│   │
│   └── processed/
│
├── images/
│   ├── executive overview.jpeg
│   ├── sales and demand analytics.jpeg
│   ├── inventory analytics.jpeg
│   └── supplier performance.jpeg
│
├── sql/
│   ├── schema.sql
│   ├── views.sql
│   ├── kpi_queries.sql
│   └── advanced_analysis.sql
│
├── src/
│   ├── analysis/
│   │   ├── inventory.py
│   │   ├── logistics.py
│   │   ├── sales.py
│   │   └── supplier.py
│   │
│   ├── cleaning/
│   │   └── clean_data.py
│   │
│   ├── data_generation/
│   │   ├── generate_inventory.py
│   │   ├── generate_orders.py
│   │   ├── generate_products.py
│   │   ├── generate_sales.py
│   │   └── generate_shipments.py
│   │
│   ├── database/
│   │   └── load_mysql.py
│   │
│   ├── ingestion/
│   │   └── fred_api.py
│   │
│   ├── transformation/
│   │   └── transform_data.py
│   │
│   └── utils/
│       ├── helpers.py
│       ├── logger.py
│       └── validators.py
│
├── .gitignore
├── README.md
└── requirements.txt
```

---

# How to Reproduce

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/fmcg-supply-chain-analytics.git
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the environment

```bash
.venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Create a `.env` file

```env
OPENFOODFACTS_API_URL=https://world.openfoodfacts.org
FRED_API_KEY=YOUR_FRED_API_KEY

DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=fmcg_supply_chain
```

### 6. Run the ETL pipeline

Generate master data, synthetic operational datasets, and load them into MySQL.

### 7. Execute SQL validation scripts

Validate referential integrity and KPI calculations.

### 8. Open the Power BI dashboard

Open `dashboard/fmcg_supply_chain.pbix` and refresh the data model.

---

# Future Improvements

- Integrate real ERP or SAP transactional data.
- Add demand forecasting using Prophet or XGBoost.
- Implement inventory optimization models.
- Automate daily ETL with Apache Airflow.
- Deploy an interactive Streamlit dashboard.
- Containerize the project using Docker.
- Deploy the analytics pipeline on Microsoft Azure or AWS.

---

# Author

**Harshal Saudagar**

Aspiring Data Analyst | Python | SQL | MySQL | Power BI | ETL | Business Intelligence | Supply Chain Analytics

If you found this project useful, consider giving the repository a star ⭐.

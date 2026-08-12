USE fmcg_supply_chain;

-- ===========================================================
-- SALES ANALYSIS
-- ===========================================================

---------------------------------------------------------------
-- 1. Monthly Revenue
---------------------------------------------------------------

SELECT
    d.year,
    d.month_name,
    SUM(f.revenue) AS revenue
FROM fact_sales f
JOIN dim_date d
ON f.date_id = d.date_id
GROUP BY
    d.year,
    d.month,
    d.month_name
ORDER BY
    d.year,
    d.month;

---------------------------------------------------------------
-- 2. Revenue by Category
---------------------------------------------------------------

SELECT
    p.category,
    ROUND(SUM(f.revenue),2) AS revenue,
    SUM(f.quantity_sold) AS units_sold
FROM fact_sales f
JOIN dim_product p
ON f.product_id = p.product_id
GROUP BY
    p.category
ORDER BY revenue DESC;

---------------------------------------------------------------
-- 3. Revenue by Brand
---------------------------------------------------------------

SELECT
    p.brand,
    ROUND(SUM(f.revenue),2) revenue
FROM fact_sales f
JOIN dim_product p
ON f.product_id=p.product_id
GROUP BY p.brand
ORDER BY revenue DESC;

---------------------------------------------------------------
-- 4. Top 10 Products
---------------------------------------------------------------

SELECT

    p.product_name,

    SUM(f.quantity_sold) units,

    ROUND(SUM(f.revenue),2) revenue

FROM fact_sales f

JOIN dim_product p
ON f.product_id=p.product_id

GROUP BY p.product_name

ORDER BY revenue DESC

LIMIT 10;

---------------------------------------------------------------
-- 5. Bottom 10 Products
---------------------------------------------------------------

SELECT

    p.product_name,

    SUM(f.quantity_sold) units,

    ROUND(SUM(f.revenue),2) revenue

FROM fact_sales f

JOIN dim_product p
ON f.product_id=p.product_id

GROUP BY p.product_name

ORDER BY revenue ASC

LIMIT 10;

---------------------------------------------------------------
-- 6. Average Selling Price
---------------------------------------------------------------

SELECT

    ROUND(
        AVG(unit_price),
        2
    ) average_price

FROM fact_sales;

---------------------------------------------------------------
-- 7. Discount Impact
---------------------------------------------------------------

SELECT

    promotion_flag,

    COUNT(*) transactions,

    ROUND(
        SUM(revenue),
        2
    ) revenue

FROM fact_sales

GROUP BY promotion_flag;

---------------------------------------------------------------
-- 8. Daily Revenue Trend
---------------------------------------------------------------

SELECT

    d.full_date,

    SUM(f.revenue) revenue

FROM fact_sales f

JOIN dim_date d
ON f.date_id=d.date_id

GROUP BY d.full_date

ORDER BY d.full_date;
USE fmcg_supply_chain;


INSERT INTO dim_date
(
    date_id,
    date,
    day,
    month,
    month_name,
    quarter,
    year,
    week,
    day_of_week,
    day_name
)

SELECT
    DATE_FORMAT(d, '%Y%m%d') + 0 AS date_id,

    d AS date,

    DAY(d) AS day,

    MONTH(d) AS month,

    MONTHNAME(d) AS month_name,

    QUARTER(d) AS quarter,

    YEAR(d) AS year,

    WEEK(d, 1) AS week,

    DAYOFWEEK(d) AS day_of_week,

    DAYNAME(d) AS day_name

FROM
(
    SELECT
        DATE_ADD(
            '2024-01-01',
            INTERVAL seq DAY
        ) AS d

    FROM
    (
        SELECT
            a.n
            + b.n * 10
            + c.n * 100
            + d.n * 1000 AS seq

        FROM
        (
            SELECT 0 n UNION SELECT 1 UNION
            SELECT 2 UNION SELECT 3 UNION
            SELECT 4 UNION SELECT 5 UNION
            SELECT 6 UNION SELECT 7 UNION
            SELECT 8 UNION SELECT 9
        ) a

        CROSS JOIN
        (
            SELECT 0 n UNION SELECT 1 UNION
            SELECT 2 UNION SELECT 3 UNION
            SELECT 4 UNION SELECT 5 UNION
            SELECT 6 UNION SELECT 7 UNION
            SELECT 8 UNION SELECT 9
        ) b

        CROSS JOIN
        (
            SELECT 0 n UNION SELECT 1 UNION
            SELECT 2 UNION SELECT 3 UNION
            SELECT 4 UNION SELECT 5 UNION
            SELECT 6 UNION SELECT 7 UNION
            SELECT 8 UNION SELECT 9
        ) c

        CROSS JOIN
        (
            SELECT 0 n UNION SELECT 1 UNION
            SELECT 2 UNION SELECT 3 UNION
            SELECT 4 UNION SELECT 5 UNION
            SELECT 6 UNION SELECT 7 UNION
            SELECT 8 UNION SELECT 9
        ) d

    ) numbers

) dates

WHERE d <= '2027-12-31';
CREATE OR REPLACE TABLE marts.revenue_daily AS
WITH orders AS (
    SELECT order_id, customer_id, order_date
    FROM raw.orders
),
enriched AS (
    SELECT o.*, oi.product_id, oi.quantity, oi.unit_price
    FROM orders o
    JOIN raw.order_items oi ON o.order_id = oi.order_id
)
SELECT
    customer_id,
    order_date,
    SUM(quantity * unit_price) AS net_revenue
FROM enriched
GROUP BY customer_id, order_date;

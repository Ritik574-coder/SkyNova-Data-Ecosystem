# Recommended Analytical Questions

Once `dim_*`/`fct_*` marts exist, these should all be answerable. Grouped roughly by
which marts they exercise.

## Revenue & growth (fct_sales, dim_date, dim_geography)
1. Monthly revenue by country.
2. Revenue by product department/category/subcategory.
3. Year-over-year and month-over-month revenue growth.
4. Sales by channel (in-store vs. online) over time.
5. Average order value, by channel and by country.

## Customers (dim_customer SCD2, fct_sales, fct_returns)
6. Customer lifetime value.
7. Repeat customer rate.
8. Customer retention / churn by cohort.
9. Customer segmentation (RFM or segment field) and revenue contribution by segment.
10. Customer migration between segments over time (requires SCD2 history).
11. Historical customer attributes at time of purchase (SCD2 point-in-time join).

## Returns (fct_returns, fct_sales)
12. Overall return rate (units and revenue).
13. Product-level return rate — which SKUs/categories return most.
14. Return behavior by customer segment.
15. Refund-amount variance from expected (data-quality-adjacent but business-relevant).

## Inventory (fct_inventory_snapshot)
16. Inventory turnover by product/category.
17. Stock-out frequency (closing_stock = 0 events) by location.
18. Slow-moving inventory (low sold_qty relative to average on-hand).
19. Inventory valuation over time, by location and company-wide.

## Margin & pricing (fct_sales, dim_product)
20. Gross margin by product/category/department.
21. Discount impact on margin and volume.
22. Product profitability ranked, with cost/price history from SCD2.

## Store & employee performance (fct_sales, dim_store SCD2, dim_employee SCD2)
23. Store performance (revenue, AOV, return rate) by region and store format.
24. Employee (cashier) sales performance.

## Supplier (bridge_product_supplier, fct_sales, fct_returns)
25. Supplier performance — on-time-ish proxy via lead time, return rate of their products.

## Reviews (fct_reviews, fct_sales)
26. Review sentiment vs. actual sales trend for a product.
27. Verified-purchase review rating vs. non-verified rating, by product.

## Promotions (dim_channel, fct_sales, promotions)
28. Promotion effectiveness (incremental volume/revenue during promo windows vs. baseline).

## Top-line / mix
29. Top products by revenue and by units, with time-window comparisons (e.g. trailing
    90 days vs. prior 90 days).
30. High-return products cross-referenced with review sentiment and discount depth.

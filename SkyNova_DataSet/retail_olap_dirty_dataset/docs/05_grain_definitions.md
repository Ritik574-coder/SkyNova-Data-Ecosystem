# Expected Grain, Table By Table

"Grain" = what one row represents. Get this wrong and every downstream aggregate is
wrong. A few of these are deliberately easy to misjudge at a glance.

| Table | Grain (1 row =) | Common mistake |
|---|---|---|
| `store_master.csv` | 1 store (as currently known) — **not deduplicated**, ~2% re-extract dupes | assuming 1 row = 1 unique store |
| `store_change_events.csv` | 1 historical change event for a store | treating this as a dimension rather than an audit log |
| `promotions.csv` | 1 promotion definition | — |
| `pos_loyalty_customers.csv` | 1 loyalty enrollment | assuming 1 row = 1 unique person (some people enroll more than once / appear via more than one channel) |
| `pos_sales_YYYY.csv` | **1 order LINE** (already flat) | grouping by `pos_transaction_id` alone silently drops line detail; conversely, summing without grouping double-counts order-level attributes like `store_region` |
| `ecommerce_customers.jsonl` | 1 web account signup | same caution as loyalty customers |
| `ecommerce_orders_YYYY.jsonl` | **1 ORDER**, with a nested `items[]` array at LINE grain inside it | the single biggest grain trap in this dataset — you must `LATERAL FLATTEN` `items[]` to get to line grain, and order-level fields (payment, shipping, customer) must not be duplicated incorrectly when you do |
| `crm_customers.csv` | 1 customer registration — **not deduplicated**, includes true re-registrations | assuming 1 row = 1 unique person |
| `crm_customer_change_events.csv` | 1 audit event | — |
| `warehouse_master.csv` | 1 warehouse | — |
| `inventory_snapshots_YYYY.csv` | 1 (product × location × snapshot_date) observation | assuming daily coverage, or coverage for every product at every location — neither holds; this is a **sparse periodic snapshot**, not a complete cube |
| `employee_master.csv` | 1 employment record — **not deduplicated**; rehires appear as a second row | assuming 1 row = 1 unique employee |
| `employee_change_events.csv` | 1 audit event | — |
| `suppliers_master.csv` | 1 supplier (as currently known) — ~2% re-extract dupes | — |
| `reviews_YYYY.csv` | 1 review submission | duplicate/bot-pattern rows exist on purpose — decide your own dedup rule |
| `returns_YYYY.csv` | 1 return event — **not 1 per order**; an order/line can have more than one partial return | joining returns to orders 1:1 |
| `payments_YYYY.csv` | **1 payment ATTEMPT**, not 1 per order | summing `amount` per order without filtering `payment_status` will overcount for orders with a failed-then-retried or split payment |
| `shipments_YYYY.csv` | **1 shipment**, not 1 per order | an order with 3+ items can ship in 2 shipments; `skus_shipped` must be split before you can join back to order lines at SKU level |
| `product_master.csv` | 1 SKU extract — **not deduplicated**; includes reintroduced-product rows (new SKU, same lineage) and ~1.2% re-extract dupes | assuming 1 row = 1 unique product forever |
| `product_alias_crosswalk.csv` | 1 alias relationship | — |
| `product_name_change_history.csv` / `product_category_change_history.csv` | 1 change event | — |
| `bridge_product_supplier.csv` | 1 product↔supplier relationship (many-to-many) | assuming a product has exactly one supplier |

## Target mart grains (what you're building toward)

- `fct_sales`: 1 row per sales order **line**, unioned across POS and e-commerce, channel-tagged.
- `fct_returns`: 1 row per return event.
- `fct_inventory_snapshot`: 1 row per (product, location, snapshot_date) as captured — a
  periodic snapshot fact, not filled-in/interpolated unless you choose to build that as a
  separate derived mart.
- `fct_payments`: 1 row per payment attempt (or collapse to 1 row per order if your
  design calls for it — either is defensible, document the choice).
- `fct_reviews`: 1 row per review.
- `fct_shipments`: 1 row per shipment, with a bridge or exploded relationship back to
  the SKUs it carried.

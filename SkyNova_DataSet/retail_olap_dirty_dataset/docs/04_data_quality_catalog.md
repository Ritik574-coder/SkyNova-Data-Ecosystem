# Data Quality Issue Catalog

Rates below are **approximate design-time injection rates** (a few are directly measured
against the generated files, noted as "measured"). Treat them as a guide for what to
expect, not a row-level answer key — your dbt tests should discover the actual counts.

## 1. Missing values / null representations (mixed on purpose)
Present across most string columns at low-to-moderate rates (roughly 2–10% depending on
field and source): `NULL` (true blank), empty string, whitespace-only string, and the
literal strings `"N/A"`, `"NA"`, `"null"`, `"unknown"`/`"Unknown"`, `"?"`, `"-"` — all
used interchangeably *within the same column* in the same file. A `COALESCE`/`NULLIF`
strategy needs to catch all of these, not just true NULL.

## 2. Duplicates
- **Exact row duplicates**: ~1.5–2% of rows in suppliers, stores, CRM customers, and a
  duplicate-JSON-resend pattern in e-commerce orders (~1.4% of orders, measured: 1,691
  of 121,000) — same content, different `ingestion_timestamp`/`batch_id`.
- **Business-key duplicates**: ~4% of CRM customers are a second registration of the
  same underlying person under a new `cust_id`, with slightly different name
  casing/spacing.
- **Near-duplicates**: casing/whitespace variants of names and geography strings
  throughout (`"Ritik Kumar"` / `"ritik kumar"` / `" Ritik Kumar "` / `"Ritik  Kumar"`),
  ~3–8% of name/geography fields depending on source.
- **Typographical duplicates**: light character insert/delete typos in ~2% of CRM names.
- **Duplicate transactions with different ingestion timestamps**: ~1.8% of POS
  transactions are fully re-sent; ~2.5% of returns and ~1.5–2% of reviews likewise.
- **Product SKU duplicates**: ~1.2% of `product_master.csv` rows are a later re-extract
  of an existing SKU with slightly drifted price/brand casing (measured: 240 of 20,377
  rows share a SKU with another row).

## 3. Invalid / impossible values
- Negative or zero **quantity**: ~0.3% / ~0.2% of sales lines (measured on POS: 708 and
  496 of 233,150 rows respectively). Returns can also exceed the purchased quantity on
  the same order/line (~1.2% of returns, measured: 575 of 47,315).
- Negative or absurd **unit price**: ~0.2–0.4% injected directly, but this *cascades* —
  roughly 0.8% of products in `product_master.csv` carry a negative or zero
  `list_price_usd`, and every sales line referencing one of those SKUs inherits the bad
  price. Measured downstream effect on POS: 2,134 of 233,150 lines have a negative
  `unit_price` — most of that is the cascade, not independent per-line injection. This
  is intentional: the fix belongs in the product dimension, not in a per-row patch on
  the fact table.
- **Discount > 100%**: ~0.3% of sales lines (measured: 691 of 233,150 POS lines).
- **Invalid/negative tax**: ~0.3% of sales lines.
- **Invalid currency code**: ~0.5–1% of sales lines/orders carry a currency that doesn't
  match the store's/shipping country's expected currency.
- **Negative closing inventory**: ~1% directly injected plus organic edge cases from
  damage/return arithmetic at low stock levels (measured: 18,968 of 576,935 snapshot
  rows, ≈3.3%).
- **Rating out of 1–5 range**: ~1.5% of reviews (0, 6, 7, -1 used as invalid values),
  separate from the ~3% of reviews with a missing rating.
- **Negative salary / negative helpful_votes / negative payment amount**: rare
  (<0.5%), simulating raw source bugs rather than business rule violations.
- **Invalid dates**: a small fraction (<0.2%) of transaction/order dates are future-dated
  beyond `DATA_END_DATE` (2026-09-15) or predate business launch (2019-01-01) — genuine
  source errors, not seasonality.
- **Invalid DOB / impossible age**: ~1.5% combined across customers — a `1900-01-01`
  sentinel default (~0.7%), a future date of birth (~0.5%), and an absurd 140–160 year
  implied age (~0.3%).

## 4. Ambiguous / conflicting records
- ~840 customers (≈420 pairs) share **identical full name AND identical city** with a
  different underlying person — a genuinely ambiguous entity-resolution case. For these
  specific individuals, phone/email are also more likely to be missing across sources,
  removing the attributes that would normally disambiguate them. These are meant to be
  flagged `UNRESOLVED`, not guessed.
- ~7% of e-commerce orders with a known customer carry a **stale name snapshot**
  (upper-cased or truncated to first name) that differs from the current
  `ecommerce_customers.jsonl` record for the same `customer_id` — a realistic "order
  captured the name as it was at checkout time" scenario.
- ~3% of e-commerce orders have an `order_total_reported` that does not reconcile with
  the sum of its line items.
- ~2% of returns have a `refund_amount` that doesn't match
  `expected_refund_amount_ref` (measured: 6,397 of 47,315 — note this reference field is
  provided as a QA convenience and is itself derived, not an authoritative source value).

## 5. Referential integrity problems
- A small fraction (<1%) of `product_code`/`sku` references in sales lines and review
  rows point to a SKU that does not exist in `product_master.csv` at all (not even
  retired) — true orphan foreign keys.
- A small fraction (<0.5%) of `store_code` references in POS sales point to a
  non-existent store.
- A larger, *intentional and structural* class of "missing" FK: ~58% of POS sales lines
  have a null `customer_id` (guest checkout) — this is normal business behavior, not a
  data quality defect, and should not be flagged the same way as an orphaned FK.

## 6. Late-arriving / lineage-timing issues
- ~2–3% of records across sales, returns, inventory, and reviews have an
  `ingestion_timestamp` that lags the business date by 3–21 days.
- ~0.4–1% of records have an implausible `ingestion_timestamp` *before* the business
  date (simulated clock-skew bug in a source system) — a smaller, separate class of
  timing defect from ordinary late arrival.

## 7. Structural / formatting inconsistencies
- 1NF violations: `skus_shipped` in `shipments.csv` is pipe-delimited; several
  geography and free-text fields mix delimiters informally.
- 2NF violations: `pos_sales_YYYY.csv` carries `product_name`, `category_name`, and
  `supplier_name` inline, functionally dependent only on `product_code`, not on the
  (order, line) composite key.
- Unit inconsistency: `weight_raw` mixes g/kg/lb as free text; `dimensions_raw` mixes
  cm/mm/in as free text "LxWxH unit" strings — both require regex parsing and
  standardization.
- Geography inconsistency: casing (`Bihar`/`BIHAR`), trailing whitespace/commas,
  ISO-code-vs-full-name (`IN` vs `India`), and **deliberate city-name collisions across
  different states/countries** (e.g. "Victoria" exists in both Gujarat, India and
  British Columbia, Canada and Texas, USA in this dataset; "Alexandria" exists in both
  Karnataka, India and Georgia, USA) — never assume city uniquely determines state.

## 8. Malformed semi-structured data
- ~0.12% of lines in the e-commerce order JSONL files are truncated/invalid JSON
  (measured: 169 of 122,860 total lines) and must fail parsing, not be salvaged.
- Nested blocks (`product`, `order.customer`, `order.customer.address`) are
  intermittently null even when the parent record is otherwise well-formed.
- Array length varies freely (`items[]` 1–6 elements, `tracking.events[]` 0–3 elements).

## Approximate overall distribution (matches the brief's target bands)
Missing values ≈ 5–12% (field-dependent) · duplicates ≈ 2–6% (table-dependent) ·
formatting inconsistencies ≈ 3–8% · invalid values ≈ 1–4% · ambiguous records ≈ 1–3% ·
referential integrity problems ≈ 1–3% · late-arriving records ≈ 2–3% · conflicting
source records ≈ 1–3%. Some tables (supplier master, warehouse master) are much
cleaner than others (inventory snapshots, e-commerce orders) — severity is
intentionally uneven across the dataset, as in a real warehouse.

# Data Dictionary

Column types below are the *intended* logical type. Every source file lands as text/CSV
or JSON — do not assume the raw column is already clean enough to cast directly; several
columns deliberately mix representations (see `04_data_quality_catalog.md`).

---
## SOURCE A — POS

### `store_master.csv` (grain: 1 row per store, plus ~2% re-extract duplicates)
| column | type | notes |
|---|---|---|
| store_id | string | `ST-#####` |
| store_name | string | |
| store_type | string | FLAGSHIP / STANDARD / OUTLET / EXPRESS |
| country | string | mixed casing, sometimes ISO code, sometimes missing |
| state_province | string | mixed casing, occasional trailing space |
| city | string | mixed casing/whitespace |
| address_line | string | |
| postal_code | string | occasionally missing/invalid; legitimately blank for AE (no postal system) |
| region | string | company region code, e.g. `IN-North`, `US-West` |
| opening_date | date | |
| closing_date | date, nullable | null unless permanently closed |
| store_status | string | OPEN / TEMPORARILY_CLOSED / PERMANENTLY_CLOSED |
| manager_employee_id | string, nullable | FK → employee_master.employee_id (current manager only — see `store_change_events.csv` for history) |
| square_footage | int | |
| source_system / source_file / ingestion_timestamp / batch_id | lineage | |

### `store_change_events.csv` (grain: 1 row per change event)
`store_id, event_type {MANAGER_CHANGE, REGION_REASSIGNMENT, FORMAT_CHANGE, TEMP_CLOSURE}, changed_field, old_value, new_value, event_date, source_system`

### `promotions.csv` (grain: 1 row per promotion)
`promo_code, promo_name, discount_type {PERCENTAGE, FIXED_AMOUNT}, discount_value, start_date, end_date, channel_applicability {ALL, ONLINE, IN_STORE}, min_purchase_amount_usd`

### `pos_loyalty_customers.csv` (grain: 1 row per loyalty signup — NOT deduplicated to one row/person)
`loyalty_id` (numeric string; may or may not equal the CRM customer's numeric core — see `07_identifier_mapping_guidance.md`), `customer_name`, `phone`, `city`, `enrollment_date`, lineage columns.

### `pos_sales_YYYY.csv` (grain: **1 row per order LINE** — already denormalized/flat)
| column | type | notes |
|---|---|---|
| source_record_id | string | |
| pos_transaction_id | string | order-level id, repeats across lines |
| line_number | int | 1..n within the transaction |
| transaction_date | timestamp | local time, no explicit offset |
| store_code | string | FK → store_master.store_id (occasionally invalid on purpose) |
| store_region | string | denormalized copy of store's region at sale time |
| product_code | string | FK → product_master.sku; **~8% of rows use the bare numeric code with the `SKU-` prefix stripped** (POS-native convention) |
| product_name | string | **2NF violation** — depends only on product_code, not (order,line) |
| category_name | string | **2NF violation** |
| supplier_name | string, nullable | **2NF violation** — primary supplier at time of extract |
| customer_id | string, nullable | FK → pos_loyalty_customers.loyalty_id; null = guest checkout (~58% of lines — this is normal, not a defect) |
| employee_id | string | FK → employee_master.employee_id (cashier) |
| quantity | int | includes some negative/zero dirty values |
| unit_price | decimal | local currency; includes some negative/absurd values |
| discount_pct | decimal | 0–100 normally; some >100 dirty values |
| tax_amount | decimal | |
| gross_amount | decimal | qty × unit_price before discount/tax |
| net_amount | decimal | final charged amount |
| currency | string | ISO code; occasionally wrong for the store's country |
| payment_method | string | CARD / UPI / CASH / NETBANKING / WALLET / COD / GIFT_CARD |
| promo_code | string, nullable | FK → promotions.promo_code |
| channel | string | always `IN_STORE` in this source |
| order_status | string | COMPLETED / VOIDED |
| source_system / source_file / ingestion_timestamp / batch_id | lineage | |

---
## SOURCE B — E-COMMERCE

### `ecommerce_customers.jsonl` (grain: 1 JSON doc per line = 1 signup; camelCase, nested)
`customerId, fullName, emailAddress, contact.phone, address.{country,state,city,postalCode}, accountCreatedAt, marketingOptIn, loyaltyTier, sourceSystem`

### `ecommerce_orders_YYYY.jsonl` (grain: 1 JSON doc = 1 ORDER, with a nested `items[]` array at LINE grain)
Top-level object is `{"order": {...}}`. Key paths:
- `order.order_id`, `order.order_date`, `order.order_status`, `order.channel`
- `order.customer.{customer_id, name, contact.{email,phone}, address.{...}}` — nullable (guest checkout ≈15%); when present, occasionally carries a **stale name snapshot** that differs from the current `ecommerce_customers.jsonl` record for the same `customer_id`
- `order.items[]` — array of `{sku, product.{name, category.{department,category}}, quantity, pricing.{unit_price, discount, tax}}`; `product` block is itself sometimes null; `quantity`/`pricing` contain the same dirty-value classes as POS
- `order.order_total_reported` — a header-level total that occasionally **does not reconcile** with the sum of item lines (source-side calculation bug, not a transcription error you can "fix" by re-summing blindly — profile both)
- `order.payment.{method, processor.name, currency}` — currency occasionally wrong for the shipping country
- `order.promo_code`
- `order.shipping.address.{...}`, `order.shipping.tracking.{carrier, events[]}` (`events[]` is an array of `{status, event_time}`, variable length, sometimes empty)
- `order.source_system`, `order.ingestion_timestamp`, `order.batch_id`

A small fraction (~0.12% of lines) are **truncated/invalid JSON** — these must fail
`PARSE_JSON`/`json.loads` and be quarantined, not patched.

---
## SOURCE C — CRM

### `crm_customers.csv` (grain: 1 row per customer registration — includes duplicate re-registrations)
`cust_id (CUST-######), customer_number, full_name, gender, date_of_birth, email_address, phone_number, country, state_province, city, postal_code, registration_date, customer_segment {Regular,Premium,VIP}, customer_status {ACTIVE,INACTIVE,CHURNED}` + lineage.

### `crm_customer_change_events.csv` (grain: 1 row per audit event — SCD2 fuel)
`cust_id, event_type {ADDRESS_CHANGE,PHONE_CHANGE,EMAIL_CHANGE,SEGMENT_CHANGE,STATUS_CHANGE}, changed_field, old_value, new_value, event_date, source_system, ingestion_timestamp`

---
## SOURCE D — INVENTORY MANAGEMENT

### `warehouse_master.csv` (grain: 1 row per warehouse)
`warehouse_id, warehouse_name, country, state_province, city, capacity_units, warehouse_type {REGIONAL_DC,FULFILLMENT_CENTER,RETURNS_CENTER}, opened_date`

### `inventory_snapshots_YYYY.csv` (grain: 1 row per product × location × snapshot_date — periodic, NOT daily-complete)
`sku, location_type {STORE,WAREHOUSE}, location_id, snapshot_date, opening_stock, received_qty, sold_qty, returned_qty, damaged_qty, closing_stock, unit_cost_usd, inventory_value_usd` + lineage.
Recent history (last ~18 months) is tracked weekly for a subset of product/location pairs;
older history is tracked monthly for a broader subset. **Coverage is intentionally sparse
and non-uniform** — do not assume every product/location/date combination exists.

---
## SOURCE E — HR

### `employee_master.csv` (grain: 1 row per employment record — includes rehire duplicates)
`employee_id (EMP-######), employee_name, department, role, store_id (nullable), manager_id (nullable), hire_date, termination_date (nullable — sometimes missing even when status=TERMINATED), employment_status {ACTIVE,TERMINATED}, annual_salary_usd` + lineage.

### `employee_change_events.csv` (grain: 1 row per audit event — SCD2 fuel)
`employee_id, event_type {PROMOTION,STORE_TRANSFER,DEPARTMENT_CHANGE,SALARY_ADJUSTMENT,MANAGER_CHANGE,REHIRE}, changed_field, old_value, new_value, event_date, source_system, ingestion_timestamp`

---
## SOURCE F — SUPPLIER MANAGEMENT

### `suppliers_master.csv` (grain: 1 row per supplier, plus ~2% re-extract duplicates)
`supplier_id (SUP-######), supplier_name, country, state_province, city, contact_name, contact_email, contact_phone, contract_start_date, contract_end_date (nullable), supplier_status {ACTIVE,INACTIVE,TERMINATED}, payment_terms_days, lead_time_days` + lineage.

---
## SOURCE G — REVIEWS

### `reviews_YYYY.csv` (grain: 1 row per review — includes duplicate/bot-pattern rows)
`review_id, sku, user_id (nullable → anonymous), display_name, rating (1–5 normally; some out-of-range/missing), review_text (multi-language, emoji, HTML fragments, whitespace noise), review_date, verified_purchase (bool), sentiment_label {POSITIVE,NEUTRAL,NEGATIVE}, helpful_votes` + lineage.

---
## SOURCE H — RETURNS MANAGEMENT

### `returns_YYYY.csv` (grain: 1 row per return event)
`return_id, order_id, order_line_id, customer_id (nullable), sku, return_date, quantity_purchased_ref (convenience field, mirrors the source order), quantity_returned (sometimes exceeds quantity_purchased_ref), return_reason, refund_amount, expected_refund_amount_ref (convenience field — sometimes doesn't match refund_amount), refund_method, return_status {APPROVED,COMPLETED,REJECTED,PENDING}, channel` + lineage.

---
## SOURCE — PAYMENT GATEWAY

### `payments_YYYY.csv` (grain: 1 row per payment ATTEMPT — an order can have 0, 1, or 2+ rows)
`payment_id, order_id, payment_date, amount, currency (usually null — inherit from order; rarely populated and wrong), payment_method, payment_status {SUCCESS,FAILED,PENDING,REFUNDED}, processor_reference, channel` + lineage.

---
## SOURCE — LOGISTICS / 3PL

### `shipments_YYYY.csv` (grain: 1 row per SHIPMENT — an order can split into 2 shipments)
`shipment_id, order_id, warehouse_id, ship_date, carrier, skus_shipped (pipe-delimited — 1NF violation, split before use), delivery_status, delivered_date (nullable), ` + lineage.

---
## SOURCE — PIM (PRODUCT INFORMATION MANAGEMENT)

### `product_master.csv` (grain: 1 row per SKU extract — includes ~1.2% duplicate re-extracts and reintroduced-product rows)
`sku, product_name, brand, department, category, subcategory, unit_cost_usd, list_price_usd, weight_raw (free-text, mixed units g/kg/lb), dimensions_raw (free-text "LxWxH unit", mixed units cm/mm/in), color, size, product_status {ACTIVE,RETIRED,DISCONTINUED}, launch_date, retired_date (nullable)` + lineage.

### `product_alias_crosswalk.csv` (grain: 1 row per alias)
`alias_sku, current_sku, alias_type {REINTRODUCED_REPLACEMENT, LEGACY_CODE_MIGRATION}, effective_date`

### `product_name_change_history.csv` / `product_category_change_history.csv` (grain: 1 row per change event)
Name history: `sku, old_product_name, new_product_name, change_date`.
Category history: `sku, old_category, old_subcategory, new_category, new_subcategory, change_date`.

### `bridge_product_supplier.csv` (grain: 1 row per product↔supplier relationship, many-to-many)
`sku, supplier_id, is_primary_supplier (bool), unit_supply_cost_usd (nullable)`

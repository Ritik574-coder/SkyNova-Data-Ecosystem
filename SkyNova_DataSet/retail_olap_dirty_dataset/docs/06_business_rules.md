# Business Rules

These are the rules the "business" actually operates under. Some are directly testable
with dbt generic tests; some need a custom singular/generic test; a few are judgment
calls the dataset deliberately leaves to you.

## Rules with a clear, testable invariant
1. `quantity_returned` should not exceed the originally purchased quantity for that
   order/line — violations exist and are findable by joining `returns` back to the
   sales line via `order_id` (+ `sku`).
2. `closing_stock` should never be negative in a healthy system — violations exist and
   are intentional; decide whether to hard-fail or soft-flag them in a test severity.
3. `discount_pct` (or discount fraction) must be between 0 and 100 — violations exist.
4. For any SCD2 dimension you build (`dim_customer`, `dim_product`, `dim_store`,
   `dim_employee`), `effective_from < effective_to` for every row, and there must be
   **exactly one current row per business key** (`is_current = TRUE`).
5. Every foreign key in a fact table must resolve to a row in its dimension —
   except where the FK is legitimately nullable (guest checkout customer_id, nullable
   store_id for warehouse/corporate employees, nullable termination_date). Don't test
   nullable-by-design fields as if they were orphaned keys.
6. `unit_price`, `net_amount`, `refund_amount`, `annual_salary_usd`, `inventory_value_usd`
   should not be negative under normal operation — violations are intentional data
   quality defects to catch, not business rules that are sometimes legitimately violated.
7. A payment's `payment_status = 'SUCCESS'` should be the one counted toward revenue
   recognition; `FAILED`/`PENDING` attempts should not be double-counted against the
   order total.

## Rules requiring business judgment (documented, not enforced by the data)
- **Guest checkout is normal**, not a data quality defect. ~58% of POS sales lines and
  ~15% of e-commerce orders have no customer reference by design.
- **A product that goes through `REINTRODUCED_REPLACEMENT`** (see
  `product_alias_crosswalk.csv`) gets a *new* SKU. Whether your `dim_product` treats
  the relaunch as "the same product, new version" (chain the SCD2 history through the
  alias) or "a new product" (start fresh) is a modeling decision — either is defensible,
  but be consistent and document it.
- **Currency handling**: amounts in sales/payment/return tables are in the transaction's
  local currency, not a single base currency. Pick a base currency (e.g. USD) and an
  FX approach for cross-country aggregation (a fixed rate is fine for this exercise;
  document that it's a simplification).
- **Late-arriving facts and dimensions**: decide and document how your incremental
  models handle a fact whose `ingestion_timestamp` is materially after its business
  date — e.g. does it still land in the correct historical period, or in the period it
  arrived?
- **Ambiguous customer matches** (~420 pairs sharing identical name+city with no other
  matching attributes) should be surfaced as `UNRESOLVED` in your entity-resolution
  output, not force-merged into either candidate. A false merge here is worse than an
  unresolved record.
- **Discount stacking**: a promo-code discount and a line-level discount are not
  designed to compound multiplicatively in this dataset's source logic — when both
  appear to apply, treat `discount_pct` on the line as already reflecting whichever
  discount won, not something to add to the promo separately.

## Tax and currency reference (for validating extracted amounts)
| Country | Currency | Approx. tax rate used |
|---|---|---|
| India | INR | 18% |
| United States | USD | 8% |
| United Kingdom | GBP | 20% |
| Canada | CAD | 13% |
| United Arab Emirates | AED | 5% |

These are simplifications for the exercise, not a claim about real-world tax law.

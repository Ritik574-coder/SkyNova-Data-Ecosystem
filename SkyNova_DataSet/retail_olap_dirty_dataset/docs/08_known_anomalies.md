# Known Intentional Anomalies

A categorized list of "yes, that's supposed to be there" items, so you can distinguish
intentional teaching artifacts from an actual bug in the dataset itself (if you find
something not described anywhere in `docs/`, treat it as worth double-checking — but
everything catalogued here and in `04_data_quality_catalog.md` is by design).

## Category A — Directly solvable via deterministic rules
- Null representation zoo (`NULL`/empty/whitespace/`N/A`/`NA`/`null`/`unknown`/`?`/`-`) →
  a `NULLIF`/`COALESCE` normalization list solves it.
- `SKU-` prefix stripped in some POS `product_code` values → regex/string normalization.
- Mixed weight/dimension units in free text → regex extraction + unit conversion.
- Discount > 100%, negative quantity/price/tax → range-check tests, clearly invalid
  regardless of context.
- Casing/whitespace variants of names and geography strings → normalize (trim, collapse
  whitespace, standardize case) before comparing.

## Category B — Solvable using another source
- POS/e-commerce customer identity → cross-referenced against CRM (with the caveats in
  `07_identifier_mapping_guidance.md`).
- Product cascade-negative-price sales lines → the *cause* is in `product_master.csv`,
  not fixable by patching the fact table alone.
- `skus_shipped` in shipments → resolves to real SKUs in `product_master.csv` once split.

## Category C — Solvable using historical records
- Current store manager conflicting with an older reference elsewhere → resolve via
  `store_change_events.csv` (event-time ordering).
- Employee currently shown in a department that doesn't match an older reference →
  resolve via `employee_change_events.csv`.
- A customer's "current" address differing from an address embedded in an old
  e-commerce order → resolve via `crm_customer_change_events.csv` and the order's own
  timestamp (the order's stale snapshot is *supposed* to look old — don't overwrite
  history, model it).
- Retired SKU referenced in an old sales line that predates the SKU's retirement date →
  not an error; check `launch_date`/`retired_date` against the transaction date.

## Category D — Solvable using business rules
- Guest checkout nulls (not a defect — see `06_business_rules.md`).
- AE (UAE) blank postal codes (structural — UAE largely has no postal code system in
  this dataset's design, distinct from a *missing* postal code elsewhere).
- Warehouse-department employees with null `store_id` (structural, not missing data).
- Payment `FAILED` attempts preceding a `SUCCESS` retry on the same order (expected
  gateway behavior, not a duplicate to be deduplicated away).

## Category E — Detectable but intentionally unresolved
- The ~420 ambiguous name+city customer collision pairs (see `07_identifier_mapping_guidance.md`)
  — correct handling is to flag, not merge.
- ~0.12% of e-commerce JSONL lines are truncated/invalid JSON and will fail to parse —
  correct handling is to quarantine them (e.g., a dbt source freshness/format test or a
  dead-letter pattern), not to attempt a byte-level repair.
- Orphaned FK references (SKU/store codes that don't exist anywhere) — a genuine small
  slice with no recoverable "correct" value; flag via referential integrity tests.
- `order.order_total_reported` vs. summed line items in e-commerce orders occasionally
  disagree with no recoverable single truth — pick and document a policy (trust the
  header, trust the sum, or carry both and flag the delta).

## What is NOT in this dataset
No pure random-noise corruption exists that has no traceable cause — if a value looks
inexplicable, look for it in another table, another point in time, or a stated business
rule before assuming it's unsolvable.

# Source System Descriptions

| Code | System | Owns | Format(s) | Update cadence (simulated) |
|---|---|---|---|---|
| A | POS (point of sale) | stores, promotions, POS loyalty customer refs, in-store sales lines | CSV, one file per year for sales | daily batch |
| B | E-commerce platform | web customer accounts, online orders (nested) | JSON Lines, one file per year for orders | near-real-time, with some late-arriving batches |
| C | CRM | authoritative-ish customer master + change audit log | CSV | daily batch |
| D | Inventory Management | warehouses, periodic inventory snapshots | CSV, one file per year | weekly (recent) / monthly (historical) |
| E | HR | employee master + change audit log | CSV | daily batch |
| F | Supplier Management | supplier master | CSV | ad hoc / infrequent |
| G | Reviews platform | product reviews | CSV, one file per year | daily batch |
| H | Returns Management | returns | CSV, one file per year | daily batch |
| — | Payment Gateway | payment attempts | CSV, one file per year | near-real-time |
| — | Logistics / 3PL | shipments | CSV, one file per year | daily batch |
| — | PIM (Product Info Mgmt) | product master, aliases, category/name history, product↔supplier bridge | CSV | ad hoc |

## Why the conventions differ between systems

Each source was built by a different team at a different time, which is why the same
concept is named differently depending on where you're looking:

- **Customer identifier**: `cust_id`/`customer_number` (CRM) vs. `loyalty_id` (POS) vs.
  `customerId` (E-commerce, camelCase) vs. `user_id` (Reviews).
- **Product identifier**: `sku` (PIM/E-commerce) vs. `product_code` (POS — sometimes the
  same value, sometimes the same value with the `SKU-` prefix stripped).
- **Date fields**: `transaction_date` (POS) vs. `order_date` (E-commerce) vs.
  `snapshot_date` (Inventory) vs. `event_date` (audit logs) — none of these are named
  consistently, none are guaranteed to be in the same timezone convention, and none
  should be assumed to mean "ingestion time" (see `ingestion_timestamp` on every table).
- **Casing**: E-commerce is the only camelCase JSON source; everything else is
  snake_case-ish CSV headers, though even that isn't perfectly consistent
  (`store_code` in POS sales vs. `store_id` in the store master, for the same concept).

## Lineage columns present on (almost) every table

`source_system, source_file, ingestion_timestamp, batch_id` — use these to resolve
conflicts by recency, to detect duplicate batches, and to identify late-arriving records
(`business_date` vs. `ingestion_timestamp` can differ by anywhere from under a day to
several weeks — a small fraction of records are late by design, and a smaller fraction
have implausible/future `ingestion_timestamp` values simulating clock-skew bugs in a
source system).

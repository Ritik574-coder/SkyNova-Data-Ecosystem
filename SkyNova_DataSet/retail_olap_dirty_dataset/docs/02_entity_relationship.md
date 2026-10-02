# Entity Relationship Description

This is a description of relationships, not a literal ERD diagram file. Cardinalities
are given at the *conformed/target* level (after integration) — raw source files often
look messier than this because the same relationship is expressed with different keys
in different systems (see `07_identifier_mapping_guidance.md`).

## Core entities and relationships

```
Customer (1) ───< (many) Sales Order Line   [POS: pos_sales.csv | Ecommerce: order.items[]]
Customer (1) ───< (many) Return
Customer (1) ───< (many) Review               (nullable — anonymous reviews exist)
Customer (1) ───< (many) Payment              (via order_id, indirect)
Customer (1) ───< (many) crm_customer_change_events   [SCD2 source]

Product/SKU (1) ───< (many) Sales Order Line
Product/SKU (1) ───< (many) Return
Product/SKU (1) ───< (many) Review
Product/SKU (1) ───< (many) Inventory Snapshot
Product/SKU (many) ──< bridge_product_supplier >── (many) Supplier
Product/SKU (1) ───< (many) product_name_change_history
Product/SKU (1) ───< (many) product_category_change_history
Product/SKU (0/1) ──── product_alias_crosswalk ──── (0/1) Product/SKU   [self-referencing: alias_sku → current_sku]

Store (1) ───< (many) Sales Order Line (POS only)
Store (1) ───< (many) Employee                (an employee's "home" store; nullable for corporate/warehouse staff)
Store (1) ───< (many) store_change_events      [SCD2 source]
Store (1) ──── Employee                         (manager_employee_id — current manager, 1:1 at any instant)

Warehouse (1) ───< (many) Inventory Snapshot
Warehouse (1) ───< (many) Shipment

Employee (1) ───< (many) employee_change_events  [SCD2 source]
Employee (0/1) ──── Employee                      (manager_id — self-referencing hierarchy)

Order (1) ───< (many) Order Line                (order_id is the natural grain-join key)
Order (1) ───< (many) Payment                    (0, 1, or 2+ payment attempts per order)
Order (1) ───< (many) Shipment                   (1 or 2 shipments per order)
Order (1) ───< (many) Return                     (0, 1, or more partial returns per order)

Promotion (1) ───< (many) Order Line             (promo_code applied at line/item level)
```

## Notes on cardinality that are *deliberately* not clean 1:1

- **Customer identity is not a single key across sources.** The same real person may
  have 1 CRM row, 0–1 POS loyalty rows, 0–1 e-commerce rows, and 0–1 reviewer identity —
  and a small number of CRM rows are themselves duplicate registrations of the same
  person. Treat "customer" as something you build (`dim_customer`), not something you're
  handed.
- **Product identity has the same issue on a smaller scale**: `product_alias_crosswalk`
  exists specifically because some SKUs were retired and relaunched under a new SKU, and
  some SKUs were migrated from a legacy code. A `dim_product` SCD2 build needs to decide
  whether an alias represents "the same product" (arguably yes for `LEGACY_CODE_MIGRATION`)
  or "a new product generation" (arguably yes for `REINTRODUCED_REPLACEMENT`) — this is a
  business-rule judgment call, not something the data forces on you.
- **Store manager is a point-in-time fact, not a permanent attribute** — `store_master.csv`
  only shows the *current* manager; history lives in `store_change_events.csv`.
- **Order vs. Line vs. Payment vs. Shipment are four different grains** that all key off
  `order_id` but do not have the same row count. See `05_grain_definitions.md`.

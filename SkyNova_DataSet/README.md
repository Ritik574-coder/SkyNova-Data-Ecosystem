# Retail OLAP Dirty Dataset — Omnichannel Retail Co.

A multi-year, multi-source, intentionally messy dataset for practicing the full data
engineering → dimensional modeling → dbt/Snowflake pipeline. Built to be **difficult but
solvable**: every quality problem is either resolvable with evidence somewhere in the
data, or is a genuinely ambiguous case that should be *detected and flagged*, not guessed at.

## What this is

A fictional omnichannel retailer ("the Company") operating physical stores and
e-commerce across India, the United States, the United Kingdom, Canada, and the UAE,
2019‑01‑01 through 2026‑09‑15 (~7.7 years). Data is exported the way a real enterprise's
disconnected systems actually would: eight source systems, four file conventions (CSV,
JSON Lines, deeply nested JSON, pipe-delimited fields inside CSV columns), inconsistent
naming, inconsistent identifiers, and realistic operational noise.

**~1.9 million source rows** (≈2.1M once nested e-commerce order items are flattened),
485 MB uncompressed, spread across 9 source systems.

## Folder structure

```
data/
  source_a_pos/                 POS terminals + store master + promotions   (CSV)
  source_b_ecommerce/           Online orders (nested JSON) + web customers (JSONL)
  source_c_crm/                 Customer master + change-event audit log    (CSV)
  source_d_inventory_mgmt/      Warehouse master + inventory snapshots      (CSV)
  source_e_hr/                  Employee master + change-event audit log    (CSV)
  source_f_supplier_management/ Supplier master                             (CSV)
  source_g_reviews/             Product reviews                             (CSV)
  source_h_returns_mgmt/        Returns                                     (CSV)
  source_logistics_3pl/         Shipments (1 row = 1 shipment)               (CSV)
  source_payment_gateway/       Payment attempts (1 row = 1 payment)         (CSV)
  source_pim_product_master/    Product master, aliases, category/name history, 
                                 product↔supplier bridge                    (CSV)
docs/
  01_data_dictionary.md
  02_entity_relationship.md
  03_source_systems.md
  04_data_quality_catalog.md
  05_grain_definitions.md
  06_business_rules.md
  07_identifier_mapping_guidance.md
  08_known_anomalies.md
  09_analytical_questions.md
```

## How to use it

1. **Load raw, don't clean on the way in.** Every file is meant to land in a
   `RAW`/staging schema as-is — VARCHAR/VARIANT, no casting, no filtering.
2. **Profile before you model.** Row counts, null rates, distinct-value counts,
   min/max dates per source — this dataset rewards profiling; it punishes assuming.
3. **Read `docs/05_grain_definitions.md` before writing any dbt model.** Several
   sources look like they're at one grain and are actually at another.
4. **Use `docs/04_data_quality_catalog.md` and `docs/08_known_anomalies.md`** as your
   test backlog — they describe *categories* of issues and roughly how common they
   are, not row-level answers.
5. Build staging → intermediate → marts. Marts should land on a conformed Kimball star:
   `dim_date`, `dim_customer` (SCD2), `dim_product` (SCD2), `dim_store` (SCD2),
   `dim_employee` (SCD2), `dim_supplier`, `dim_geography`, `dim_channel`,
   `dim_payment_method`, `fct_sales`, `fct_returns`, `fct_inventory_snapshot`,
   `fct_reviews`, `fct_payments`, `fct_shipments`.

## What you will NOT find in this package

A cleaned/solved version of the data, an entity-resolution answer key, or a literal
crosswalk of every source ID back to a single master ID. Those defeat the point.
An internal ground truth was used during generation to keep the mess *logically
consistent* (so your joins, dedup logic, and SCD2 reconstruction can actually work),
but it isn't shipped. A number of records are genuinely ambiguous by design — the
right outcome for those is to flag them `UNRESOLVED`, not to force a match.

## Scale notes / deviations from a literal spec reading

- **Stores: ~530**, not "20,000+". A 20,000-store chain isn't a coherent business;
  530 stores is "large enterprise" scale and is what makes 20,000+ employees realistic
  (~35 staff/store average + corporate + warehouse staff).
- Total volume targets several hundred thousand to a couple million rows per the
  brief's own range ("several hundred thousand, preferably several million"), rather
  than every table individually reaching into the millions — full-scale generation
  across every single table would produce tens of GB, impractical to hand over as a
  learning dataset.

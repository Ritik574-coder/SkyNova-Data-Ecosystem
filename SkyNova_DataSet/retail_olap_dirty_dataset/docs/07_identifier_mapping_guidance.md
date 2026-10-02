# Identifier Mapping Guidance

This is **guidance on how to approach entity resolution**, not a crosswalk table. No
answer key is shipped — building the resolution logic is the exercise.

## Customer identifiers — three overlapping strategies exist in the data

The dataset uses three *different* identifier relationships simultaneously, mixed
together, so no single strategy will resolve every customer:

1. **Shared numeric core (pattern match).** For a majority-but-not-all of customers who
   appear in more than one source, the source-specific ID literally embeds the same
   underlying numeric key with a different prefix/format convention — e.g. CRM's
   `CUST-001245` and something like a bare `1245` in POS or `customer_1245` in
   e-commerce. Stripping known prefixes and comparing the numeric remainder will
   resolve a real share of cross-source matches, but **not all of them** — treat a
   successful pattern match as a strong candidate, not a guarantee.
2. **Independent identifier sequences.** A meaningful share of POS loyalty IDs and
   e-commerce customer IDs are assigned independently of the CRM numbering and will
   **not** pattern-match at all. These require attribute-based matching: name
   (normalized for case/whitespace/typos), phone number, email, and city/geography as
   joint evidence. No single attribute is reliable alone — phone numbers change,
   emails change, names have variants, and city alone is not unique (see the
   deliberate city-name collisions noted in `04_data_quality_catalog.md`).
3. **Genuinely ambiguous cases.** A small, specific cohort of customers shares an
   identical name AND identical city with a different real person, and — for that
   cohort specifically — the disambiguating attributes (phone/email) are more likely to
   be missing across sources. No amount of clever matching logic should force a
   confident merge here. Design your entity resolution pipeline to output a
   `match_confidence` (or equivalent) and route low-confidence matches to `UNRESOLVED`
   rather than silently picking one.

**Recommended approach**: build a layered matching pipeline — (a) exact/normalized key
match, (b) deterministic pattern match on ID numbering, (c) probabilistic/fuzzy match on
name + phone/email + geography with a minimum evidence threshold, (d) anything left
unmatched with sufficient evidence stays `UNRESOLVED` rather than guessed.

## Product identifiers
- `sku` in PIM/e-commerce vs. `product_code` in POS: usually identical, but POS
  sometimes strips the `SKU-` prefix — normalize both to compare.
- `product_alias_crosswalk.csv` gives you real (not hidden) `alias_sku → current_sku`
  links for legacy code migrations and product relaunches — this one **is** shipped in
  full, because it represents a legitimate, always-available master-data crosswalk a
  real PIM team would maintain, not something you're expected to reverse-engineer.

## Store / employee identifiers
Both are consistent within their own source system (POS uses `store_id` as its own
key; HR uses `employee_id` as its own key) — the challenge with these two entities is
**temporal** (reconstructing SCD2 history from the change-event logs), not cross-system
identity resolution.

## A general note
Where you cannot resolve something with reasonable confidence, **say so** in your
output rather than picking an answer. An `UNRESOLVED`/`low_confidence` flag is a
correct, gradeable outcome in this exercise — a confident wrong merge is not.

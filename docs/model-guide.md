# Model guide

[Back to the project overview](../README.md)

## Source contract

The `de_project` source declares four existing Snowflake tables: `user_journey`, `user_data`, `product_data`, and `inventory_data`. See [the source declarations](../models/raw_data/de_project_ddl.yml) for column names and declared types. YAML declarations describe the sources; they do not provision tables, enforce column types, or load data.

## Models, keys, and grain

The grains below describe intended use and configured keys. A dbt `unique_key` is not a uniqueness assertion or automatic source deduplication.

| Model | Materialization | Intended grain / configured key | Detail |
| --- | --- | --- | --- |
| `stg_user_journey_SX` | Incremental | Search event × product × user | Projects source events and derives `event_hour` / `event_date`. |
| `dim_user_env_SX` | Incremental | User × session | Projects session/device/geography fields directly from journey rows; repeated events can duplicate this grain. |
| `dim_product_SX` | Table | Product | Rebuilt from source; configured key `product_id` does not enforce uniqueness. |
| `dim_user_data_SX` | Table | User | Rebuilt customer attributes, including opt-in status. |
| `dim_inventory_SX` | Table | Inventory record | Key is `inventory_id`; retains product and warehouse identifiers. |
| `fact_search_metric_SX` | Incremental | Product × user × search event | Search context plus cart and purchase flags. |
| `fact_product_performance_SX` | Incremental | Product × user × search event | Event timestamp and engagement flags. |
| `fact_campaign_effect_SX` | Incremental | Configured key: product × user × session | Selects search-event rows; multiple searches within one session can conflict with this key. |
| `fact_product_aggregate_SX` | Table | Product × event date | Explicit `GROUP BY` produces daily product summaries. |

The product, user, and inventory tables reflect current source values after rebuilds. They do not implement SCD Type 2 history. Inventory contains measures as well as descriptive attributes; its existing `dim_` name should not imply a purely descriptive dimension.

## Metric definitions

These definitions follow [the aggregate SQL](../models/data_mart/fact_product_aggregate_SX.sql).

| Field | Calculation per product/day | Caveat |
| --- | --- | --- |
| `search_count` | Count of non-null `search_event_id` values | Not a distinct-search count; source duplicates affect it. |
| `atc_count` | Count of rows where `has_atc` is true | Flagged records, not cart quantities. |
| `amount_sold` | Count of rows where `has_purchase` is true | Purchase-flagged records, not units, orders, or revenue. |
| `pdp_view_count` | Count of rows where `has_pdp` is true | Product-detail-page flag count. |
| `qv_view_count` | Count of rows where `has_qv` is true | Quick-view flag count. |
| `no_engagement_count` | Count where both `has_pdp` and `has_atc` are false | Does not exclude quick views or purchase flags; nulls do not satisfy the predicate. |
| `purchase_from_pdp_count` | Count where both purchase and PDP flags are true | Co-occurrence, not proof that a PDP view preceded or caused a purchase. |

Summing product-level counts across products does not produce distinct sessions, customers, searches, or orders. Revenue and campaign ROI require transaction values and campaign costs that these models do not calculate.

## Incremental behavior

Five models combine `materialized='incremental'`, a composite `unique_key`, and `WHERE NOT EXISTS` against the existing target.

- **Initial build:** the incremental predicate is absent, so all selected source rows are processed.
- **Later builds:** rows whose keys already exist in the target are excluded before the adapter writes results.
- **Late new keys:** an older event can still enter if its key is unseen; there is no event-date watermark.
- **Changes to existing keys:** corrected attributes or a purchase flag that later changes will be skipped.
- **Duplicates in the incoming batch:** the anti-join does not deduplicate rows within that batch. Null key components also need explicit handling.

The adapter may use a merge to write incremental results, but the selection predicate prevents existing-key updates from reaching it. This is not an implemented lookback-window or change-data-capture strategy.

## Campaign filtering

The campaign fact joins the staged journey to raw `user_data`, keeping records where `LOWER(CAST(marketing_opt_in AS STRING)) = 'true'`. Unmatched users and other opt-in values are excluded.

The resulting population is opted-in users with matching source records, not all customers. Current opt-in status is used; consent as of the historical event time is not reconstructed. Because existing keys are skipped during incremental builds, a later opt-out does not automatically remove a previously loaded row.

## Tests and their boundaries

| Test type | Existing coverage | Boundary |
| --- | --- | --- |
| Column tests | Selected `not_null` checks | Composite uniqueness and all relationships are not comprehensively tested. |
| User-reference SQL | Users in three event facts must exist in the customer dimension | Does not validate every dimension relationship. |
| Marketing SQL | Flags customer opt-in values whose string cast equals lowercase `'false'` | Not the full inverse of the model filter; nulls and alternative spellings need attention. |
| Email SQL | Simple `LIKE` pattern | Not complete email validation. |
| Unit fixtures | Timestamp truncation, opt-in join/filter, daily counts | Staging and campaign fixtures disable the incremental branch. |

## Design trade-offs and next steps

1. **Make grain explicit.** Add composite uniqueness checks and decide whether campaign facts represent search events or sessions. Deduplicate session-environment records with a documented selection rule before relying on session-level joins.
2. **Handle updates deliberately.** Replace the new-key-only selection where mutable events require updates. Choose a lookback window or change timestamp based on measured source behavior, then test reruns and late arrivals.
3. **Clarify reporting semantics.** Consider renaming `amount_sold` to `purchase_event_count` in a coordinated model/report change. Preserve the current name until consumers are updated.
4. **Strengthen input checks.** Add relationship, null-key, boolean normalization, and uniqueness coverage based on actual source guarantees.
5. **Simplify inherited configuration.** Align project configuration names, document dependencies, and introduce project-owned CI checks if needed. The inherited cloud workflows are archived; the Airflow DAG documents the separate scheduled model-run path.
6. **Add reproducible evidence.** Include sanitized build results, sample outputs, and reporting screenshots when available. Do not infer successful execution or business impact from the presence of code.

These are future improvements, not features claimed by the current implementation.

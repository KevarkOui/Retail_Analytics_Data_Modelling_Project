# Local setup

[Back to the project overview](../README.md)

## Prerequisites

- Python and a virtual environment compatible with your chosen dbt/Snowflake adapter versions.
- dbt Core **1.8 or later** for the native `unit_tests` definitions. The existing project constraint says `>=1.5.0`, which is not sufficient for all repository features.
- A Snowflake account and development role with read access to the four source tables and permission to create models in an isolated target schema.

A fresh Snowflake build was not executed as part of the documentation refresh. Validate package and adapter compatibility in your environment before scheduling jobs.

## 1. Install the transformation tools

From the repository root, on macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install 'dbt-core>=1.8,<2' 'dbt-snowflake>=1.8,<2'
dbt --version
```

These are version ranges, not a tested lockfile. After a successful build, pin a compatible set for your environment.

`requirements.txt` is an inherited helper-tool lockfile and does not install dbt Core or the Snowflake adapter. `Taskfile.yml` defaults to BigQuery and generates Jaffle Shop data; use the explicit Snowflake commands in this guide for the active retail models.

## 2. Configure local credentials

```bash
cp profiles.example.yml profiles.yml
```

Set these environment variables through your local environment or secret manager:

| Variable | Purpose |
| --- | --- |
| `SNOWFLAKE_ACCOUNT` | Your Snowflake account identifier. |
| `SNOWFLAKE_USER` | Your development user. |
| `SNOWFLAKE_PASSWORD` | Local credential for the example's password-based connection. |
| `SNOWFLAKE_ROLE` | Role permitted to read sources and build development models. |
| `SNOWFLAKE_WAREHOUSE` | Compute warehouse available to that role. |
| `SNOWFLAKE_DATABASE` | Target database for generated models. |
| `SNOWFLAKE_SCHEMA` | Isolated target schema for generated models. |

The profile name must remain `shengjie_de_project` to match `dbt_project.yml`. If your account requires a different authentication method, configure it in your local profile. dbt does not automatically load a `.env` file; variables must be available to its process.

`profiles.yml` and local environment files are ignored by Git. The tracked example contains variable references only. Removing a credential file from the current tree does not remove it from previous commits.

## 3. Make the expected sources available

[models/raw_data/de_project_ddl.yml](../models/raw_data/de_project_ddl.yml) currently declares database `brave_database` and source name `de_project`. With no explicit source schema, dbt resolves the schema from that source name. Confirm that these relations exist and are accessible:

| Source relation |
| --- |
| `BRAVE_DATABASE.DE_PROJECT.USER_JOURNEY` |
| `BRAVE_DATABASE.DE_PROJECT.USER_DATA` |
| `BRAVE_DATABASE.DE_PROJECT.PRODUCT_DATA` |
| `BRAVE_DATABASE.DE_PROJECT.INVENTORY_DATA` |

Adapt the source declaration's database/schema to your own source location if necessary. Changing the target profile database does not change the hard-coded source database.

The repository does not include ingestion code or the matching raw extracts. `brave_data/raw_orders.csv`, `raw_items.csv`, and the other starter CSVs use a different data model. They are not inputs to these four sources, and `dbt seed` will not make this project runnable from those files: the configured seed directory is `seeds/`.

## 4. Understand target configuration

The root project is named `brave_de_project`, but the nested `models` and `seeds` configuration blocks use `shengjie_de_project`. Those blocks do not match the project name and may produce unused-configuration warnings. Each SQL model supplies its own materialization; do not assume the unmatched database/schema settings take effect.

The custom [generate_schema_name macro](../macros/generate_schema_name.sql) always returns `target.schema`, including when a custom schema is requested. Choose a distinct target schema for each development environment.

These behaviors are documented as existing configuration limitations; the presentation refresh does not change model routing.

## 5. Build and inspect

```bash
dbt deps
dbt debug --profiles-dir .
dbt parse --profiles-dir .
dbt build --profiles-dir .
```

`dbt debug` checks the connection; `dbt parse` checks project parsing, not warehouse execution. `dbt build` runs models and tests against Snowflake and may reveal source-quality, grain, or dependency issues described in the [model guide](model-guide.md).

To generate and view local dbt documentation after a successful build:

```bash
dbt docs generate --profiles-dir .
dbt docs serve --profiles-dir .
```

Generated `target/`, `logs/`, and installed `dbt_packages/` are local artifacts and should remain untracked. A full refresh rebuilds incremental tables; use it deliberately in a development schema when changed source records must be reprocessed.

## Existing automation

The GitHub workflows are inherited dbt Cloud scaffolding with Snowflake, BigQuery, and PostgreSQL jobs and hard-coded account/project/job identifiers. They depend on `DBT_CLOUD_API_KEY` and separately configured dbt Cloud jobs. Their presence does not establish a working deployment for this repository.

Review or replace those jobs before relying on automated runs. No Airflow DAG is included in the current repository.

## dbt references

- [Source schema defaults](https://docs.getdbt.com/docs/build/sources)
- [Native unit tests and version requirements](https://docs.getdbt.com/docs/build/unit-tests)

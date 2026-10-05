# Archived dbt Cloud workflows

These files came with the original repository and are retained unchanged for reference. They are outside `.github/workflows/`, so GitHub Actions does not discover them as active workflows on this branch.

| File | Former trigger |
| --- | --- |
| `ci.yml` | Pull requests targeting `main` or `staging` |
| `cd_prod.yml` | Pushes to `main` |
| `cd_staging.yml` | Pushes to `staging` |
| `scripts/dbt_cloud_run_job.py` | API helper invoked by all three workflows |

Each workflow defines Snowflake, BigQuery, and PostgreSQL jobs with inherited dbt Cloud identifiers. The observed PR checks failed while trying to trigger external jobs with an empty API key; they did not run the model tests.

The project's SQL data tests, column tests, and unit-test definitions remain in their original locations. See [Airflow orchestration](../../docs/orchestration.md) for the project's supplied scheduled execution path.

To restore cloud automation, review the account/project/job identifiers, provide the appropriate credentials, validate the external jobs, and update the helper path or restore it to `.github/workflows/scripts/`. Restore only workflows for environments actually used by the project. Archived workflow commands still reference the original helper path.

Archiving does not erase historical failed runs. Other branches retain their own workflow definitions until this change is merged or applied there.

# Airflow orchestration

[Back to the project overview](../README.md)

## Implemented flow

The [Airflow DAG](../dags/dbt_dag.py) schedules dbt Core on an Airflow worker. The worker invokes `dbt run`; dbt resolves model dependencies and submits transformation SQL to Snowflake. Snowflake executes the SQL and stores the resulting models. This path does not use dbt Cloud or its API key.

| Setting | Behavior |
| --- | --- |
| DAG and task ID | `Shengjie_pipeline_dag`, preserved from the original script |
| Schedule | One-day interval, not a claim of a specific local clock time |
| Tasks | One BashOperator invoking `dbt run` for the project |
| Retry | One retry after a 30-second delay |
| Catchup | Disabled explicitly in this version |
| Concurrent DAG runs | Limited to one |
| Target | Supplied by the local dbt profile |

Airflow manages the schedule, task state, retry, and task logs. dbt manages dependencies between the SQL models inside this single task; the Airflow UI does not expose each model as a separate task.

## What the uploaded script established

The original script invoked a dbt executable in a local Python virtual environment and pointed both project and profile arguments to a local project folder. It already contained the daily interval and retry settings.

For portability, this repository version replaces the absolute laptop paths with environment variables and uses the Airflow 2.x BashOperator import. It also makes the start date explicitly UTC, disables automatic historical catchup, limits overlapping runs, and treats every nonzero command exit as a failure. DAG and task identifiers and the `dbt run` command are retained.

The original task supplied an `env` dictionary containing only `DBT_PROFILES_DIR`. This version inherits the worker environment so the environment-based Snowflake profile can receive its credentials. These are publication-time changes, not claims about the original runtime configuration.

## Deployment requirements

This is an **Airflow 2.x-style DAG**, using the documented 2.10.x interfaces; it is not an Airflow 3 migration or an installation lockfile. Python syntax and command wiring have been checked, but the DAG has not been executed in a live Airflow/Snowflake environment during this update.

1. Use a compatible Airflow environment and place `dbt_dag.py` in its configured DAG folder.
2. Deploy a checkout of this repository to the machine/container that executes the task. GitHub changes are not automatically pulled by this DAG.
3. Install dbt Core and the Snowflake adapter in a worker-accessible environment, and run `dbt deps` for the project. See [local setup](setup.md).
4. Configure the following variables in the **worker's environment**, using absolute paths that exist inside that worker or container:

| Variable | Example |
| --- | --- |
| `DBT_EXECUTABLE` | `/opt/dbt-venv/bin/dbt` |
| `DBT_PROJECT_DIR` | `/opt/retail-analytics` |
| `DBT_PROFILES_DIR` | `/opt/dbt-config` |

5. Copy `profiles.example.yml` to `profiles.yml` inside that profile directory and securely supply its required `SNOWFLAKE_*` variables to the worker. Never commit the real profile or credentials.
6. Ensure the warehouse and four raw source tables are accessible. Inspect DAG import errors and validate a manual run in a development schema before enabling the schedule.

The worker needs permission to write dbt logs and generated artifacts. A distributed Airflow executor requires the executable, project, packages, profile, and environment to be present on each worker that can receive this task. Exporting variables in an unrelated terminal does not configure an already-running worker.

## Model builds versus tests

The supplied automation runs **`dbt run`, not `dbt build` or `dbt test`**. Its green status means the model-run command succeeded; it does not certify that the repository's data tests or unit tests passed.

All existing dbt tests remain in the repository. A future change could use `dbt build` to combine model execution with tests, after validating the tests and source data. That behavior has not been added here.

The DAG does not ingest source data, wait for an upstream ingestion task, refresh Power BI, or use Airflow's data interval to filter model inputs. Its daily schedule controls when the existing SQL runs. It does not establish an end-to-end ingestion pipeline or a currently active deployment.

## Archived dbt Cloud automation

The inherited GitHub workflows and their API helper now live under [archive/dbt-cloud/](../archive/dbt-cloud/README.md). They are separate from this Airflow execution path and no longer define active GitHub Actions workflows on branches containing this change.

## References

- [Airflow 2.10.5 DAG runs and catchup](https://airflow.apache.org/docs/apache-airflow/2.10.5/core-concepts/dag-run.html)
- [Airflow 2.10.4 BashOperator environment and exit behavior](https://airflow.apache.org/docs/apache-airflow/2.10.4/_api/airflow/operators/bash/index.html)

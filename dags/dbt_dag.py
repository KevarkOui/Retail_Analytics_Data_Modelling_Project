"""Schedule the retail dbt models with Airflow 2.x.

Configure DBT_EXECUTABLE, DBT_PROJECT_DIR, and DBT_PROFILES_DIR on the worker.
See docs/orchestration.md for setup and differences from the original DAG.
"""

from datetime import datetime, timedelta, timezone

from airflow import DAG
from airflow.operators.bash import BashOperator


default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2025, 11, 9, tzinfo=timezone.utc),
    "retries": 1,
    "retry_delay": timedelta(seconds=30),
}

with DAG(
    "Shengjie_pipeline_dag",
    default_args=default_args,
    description="Run retail analytics dbt models daily in Snowflake",
    schedule_interval=timedelta(days=1),
    catchup=False,
    max_active_runs=1,
    tags=["dbt", "snowflake", "retail"],
) as dag:
    dbt_run = BashOperator(
        task_id="Shengjie_pipeline_dag",
        bash_command='''
set -euo pipefail
: "${DBT_EXECUTABLE:?Set DBT_EXECUTABLE to the dbt executable path}"
: "${DBT_PROJECT_DIR:?Set DBT_PROJECT_DIR to the dbt project directory}"
: "${DBT_PROFILES_DIR:?Set DBT_PROFILES_DIR to the directory containing profiles.yml}"
"$DBT_EXECUTABLE" run \\
  --project-dir "$DBT_PROJECT_DIR" \\
  --profiles-dir "$DBT_PROFILES_DIR"
''',
        # Inherit worker environment, including credentials used by profiles.yml.
        skip_on_exit_code=None,
    )

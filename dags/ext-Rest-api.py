from airflow.decorators import dag, task
from datetime import datetime

@dag(
    dag_id="local_etl_demo",
    start_date=datetime(2025, 1, 1),
    schedule="@daily",
    catchup=False,
)
def local_etl_demo():

    @task
    def extract():
        return [
            {"id": 1, "name": "A"},
            {"id": 2, "name": "B"}
        ]

    @task
    def transform(rows):
        return [
            {**row, "source_system": "demo"}
            for row in rows
        ]

    @task
    def load(rows):
        print(rows)

    load(transform(extract()))

local_etl_demo()
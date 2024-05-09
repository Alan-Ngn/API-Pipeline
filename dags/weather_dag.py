from airflow.decorators import dag, task
from airflow.models import Variable
from airflow.providers.http.operators.http import HttpOperator
from datetime import datetime, timedelta
from airflow.providers.sqlite.hooks.sqlite import SqliteHook
import json

default_args = {
    'owner':'snowglobe',
    'start_date': datetime(2023, 2, 14, 7, 0, 0),  # datetime(year, month, day, hour, minute, second)
    'retries': 1,
    'retries_delay': timedelta(minutes=15)
}

@dag(
    dag_id='openweathermap',
    default_args=default_args,
    schedule_interval=timedelta(days=1),
    catchup=False
)

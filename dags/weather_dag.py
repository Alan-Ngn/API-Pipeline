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
def weather_etl():
    ski_resorts=[
                    {
                        'lat': 46.92930718381659,
                        'lon':-121.50084437354852,
                        'mountain': 'Crystal Mountain'
                    },
                    {
                        'lat': 47.408923006793,
                        'lon':-121.4130210782378,
                        'mountain': 'Summit at Snoqualmie'
                    },
                    {
                        'lat': 47.74457508492699,
                        'lon':-121.08910872510756,
                        'mountain': 'Stevens Pass'
                    },
                    {
                        'lat': 39.63392622173591,
                        'lon':-105.87151011534075,
                        'mountain': 'Araphaoe Basin'
                    },
                    {
                        'lat': 39.478058458168334,
                        'lon':-106.16144782958219,
                        'mountain': 'Copper Mountain'
                    },
                ]

    OPENWEATHERMAP_API_KEY = Variable.get("OPENWEATHERMAP_API_KEY")

    @task
    def extract(api_results, mountain):
        return [mountain]+json.loads(api_results)['list']

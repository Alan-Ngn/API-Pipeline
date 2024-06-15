
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

    #transforming data
    @task
    def transform(extracted_ski_resorts):
        result = [
            {
                'name': mountain,
                'date': datetime.utcfromtimestamp(entry['dt']).strftime('%Y-%m-%d %H:%M:%S'),
                'temp': entry['main']['temp'],
                'weather': entry['weather'][0]['description'],
                'wind': entry['wind']['speed'] if 'wind' in entry else None,
                'snow': entry['snow']['3h'] if 'snow' in entry else None,
                'rain': entry['rain']['3h'] if 'rain' in entry else None,

            }
            for mountain, *entries in extracted_ski_resorts
            for entry in entries
        ]
        return result

    @task
    def load(data):
        sqlite_hook=SqliteHook(sqlite_conn_id='sqlite_dev_db')
        target_fields = ['name', 'date', 'temp', 'weather', 'wind', 'snow','rain']
        rows = [(entry['name'], entry['date'], entry['temp'], entry['weather'], entry['wind'], entry['snow'], entry['rain']) for entry in data]
        sqlite_hook.insert_rows(table='weather',rows=rows, target_fields=target_fields)



    # extracting data with task
    extracted_resorts=[]
    for resort in ski_resorts:
        resort_task_id = resort['mountain'].replace(' ', '_').lower()
        get_weather_results_task = HttpOperator(
            task_id =f'weather_fetch_{resort_task_id}',
            method = 'GET',
            http_conn_id='openweathermap_api',
            endpoint=f'/data/2.5/forecast',
            headers={"Content-Type": "application/json"},
            data={
                'lat':resort['lat'],
                'lon':resort['lon'],
                'appid':OPENWEATHERMAP_API_KEY,
                'units':'metric'
            },
            do_xcom_push=True,
        )
        extracted_resorts.append(extract(api_results=get_weather_results_task.output, mountain=resort['mountain']))

    transformed_data = transform(extracted_resorts)
    load_data = load(transformed_data)

weather_etl()

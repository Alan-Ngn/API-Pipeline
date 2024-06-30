
from airflow.decorators import dag, task
from airflow.models import Variable
from airflow.providers.http.operators.http import HttpOperator
from datetime import datetime, timedelta
from airflow.providers.sqlite.hooks.sqlite import SqliteHook

import csv
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
                        'lat': 21.315603,
                        'lon':-157.858093,
                        'mountain': 'Honolulu'
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

    @task
    def createcsv(data):
        with open("output.csv", mode='w', newline="") as file:
            writer = csv.writer(file)
            writer.writerows(data)


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
    create_csv = createcsv(transformed_data)
    # load_data = load(transformed_data)

weather_etl()

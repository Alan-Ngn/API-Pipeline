
from airflow.decorators import dag, task
from airflow.models import Variable
from airflow.providers.http.operators.http import HttpOperator
from datetime import datetime, timedelta
from airflow.providers.sqlite.hooks.sqlite import SqliteHook
# from airflow.providers.smtp.operators.email import EmailOperator
# from airflow.providers.smtp.operators.smtp import EmailOperator
from airflow.operators.email import EmailOperator

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
    destinations=[
                    {
                        'lat': 21.315603,
                        'lon':-157.858093,
                        'location': 'Honolulu'
                    },
                    {
                        'lat': 21.572399200615358,
                        'lon':-158.121782776238,
                        'location': 'Waialua'
                    },
                    {
                        'lat': 21.572399200615358,
                        'lon':-158.121782776238,
                        'location': 'Kailua'
                    },
                    {
                        'lat': 21.441989802394755,
                        'lon':-158.18534745569784,
                        'location': 'Waianae'
                    },
                ]

    OPENWEATHERMAP_API_KEY = Variable.get("OPENWEATHERMAP_API_KEY")

    @task
    def extract(api_results, location):
        return [location]+json.loads(api_results)['list']

    #transforming data
    @task
    def transform(extracted_destinations):
        result = [
            {
                'name': location,
                'date': datetime.utcfromtimestamp(entry['dt']).strftime('%Y-%m-%d %H:%M:%S'),
                'temp': entry['main']['temp'],
                'weather': entry['weather'][0]['description'],
                'wind': entry['wind']['speed'] if 'wind' in entry else None,
                'snow': entry['snow']['3h'] if 'snow' in entry else None,
                'rain': entry['rain']['3h'] if 'rain' in entry else None,

            }
            for location, *entries in extracted_destinations
            for entry in entries
        ]
        return result

    @task
    def load(data):
        # sqlite_hook=SqliteHook(sqlite_conn_id='sqlite_dev_db')
        target_fields = ['name', 'date', 'temp', 'weather', 'wind', 'snow','rain']
        rows = [[entry['name'], entry['date'], entry['temp'], entry['weather'], entry['wind'], entry['snow'], entry['rain']] for entry in data]
        rows.insert(0, target_fields)
        with open("output.csv", mode='w', newline="") as file:
            writer = csv.writer(file)
            writer.writerows(rows)
        # sqlite_hook.insert_rows(table='weather',rows=rows, target_fields=target_fields)
        file_path = '/opt/airflow/output.csv'
        return file_path

    @task
    def send_email(file_path):
        email = EmailOperator(
        task_id='send_email',
        to='alan.nguyen.engineer@gmail.com',
        subject='OpenWeatherMap Data',
        html_content='<p>Find attached the latest weather data.</p>',
        files=[file_path],
        )
        email.execute(context=None)
    # @task
    # def createcsv(data):
        # with open("output.csv", mode='w', newline="") as file:
        #     writer = csv.writer(file)
        #     writer.writerows(data)

    # extracting data with task
    extracted_destinations=[]
    for destination in destinations:
        destination_task_id = destination['location'].replace(' ', '_').lower()
        get_weather_results_task = HttpOperator(
            task_id =f'weather_fetch_{destination_task_id}',
            method = 'GET',
            http_conn_id='openweathermap_api',
            endpoint=f'/data/2.5/forecast',
            headers={"Content-Type": "application/json"},
            data={
                'lat':destination['lat'],
                'lon':destination['lon'],
                'appid':OPENWEATHERMAP_API_KEY,
                'units':'metric'
            },
            do_xcom_push=True,
        )
        extracted_destinations.append(extract(api_results=get_weather_results_task.output, location=destination['location']))

    transformed_data = transform(extracted_destinations)
    # create_csv = createcsv(transformed_data)
    load_data = load(transformed_data)
    send_email(load_data)
weather_etl()

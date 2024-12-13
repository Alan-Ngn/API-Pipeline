from airflow.decorators import dag, task
from airflow.models import Variable
from airflow.providers.http.operators.http import HttpOperator
from airflow.operators.email import EmailOperator
from datetime import datetime, timedelta
from airflow.utils.email import send_email

import os
import csv
import json
import boto3
import io

def get_secret(secret_name, region_name="us-west-1"):
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)
    response = client.get_secret_value(SecretId=secret_name)
    secret = json.loads(response["SecretString"])
    return secret

def task_failure_callback(context):
    failed_task = context.get('task_instance')
    subject = f"{context['execution_date']} Task {failed_task.task_id} Failed in DAG {context.get('dag').dag_id}"
    html_content = f"""
        <p>Log URL: <a href="{failed_task.log_url}">Click here to view logs</a></p>
    """

    send_email(
        to='alan.nguyen.engineer@gmail.com',
        subject=subject,
        html_content=html_content,
    )


default_args = {
    'owner':'snowglobe',
    'start_date': datetime(2023, 2, 14, 3, 0, 0),  # datetime(year, month, day, hour, minute, second)
    'on_failure_callback':task_failure_callback
    # 'retries': 1,
    # 'retries_delay': timedelta(minutes=15)
}
@dag(
    dag_id='openweathermap',
    default_args=default_args,
    schedule_interval=timedelta(hours=12),
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
                        'lat': 21.394498800858724,
                        'lon':-157.74353491625777,
                        'location': 'Kailua'
                    },
                    {
                        'lat': 21.441989802394755,
                        'lon':-158.18534745569784,
                        'location': 'Waianae'
                    },
                ]
    secrets = get_secret("airflow/openweatherapi") 
    OPENWEATHERMAP_API_KEY = secrets["OPENWEATHERMAP_API_KEY"]
    smtp_user = secrets["SMTP_USER"]
    smtp_password = secrets["SMTP_PASSWORD"]

    os.environ["AIRFLOW__SMTP__SMTP_USER"] = smtp_user
    os.environ["AIRFLOW__SMTP__SMTP_PASSWORD"] = smtp_password


    @task
    def extract(api_results):
        return json.loads(api_results)

    #transforming data
    @task
    def transform(extracted_destinations):
        result = [
            {
                'name': entry['name'],
                'date': (datetime.fromtimestamp(entry['dt'])- timedelta(hours=10)).strftime('%Y-%m-%d %I:%M:%S %p'),
                'weather': entry['weather'][0]['description'],
                'temp': entry['main']['temp'],
                'humidity': entry['main']['humidity'],
                'wind': entry['wind']['speed'] if 'wind' in entry else None,
                'snow': entry['snow']['3h'] if 'snow' in entry else None,
                'rain': entry['rain']['3h'] if 'rain' in entry else None,
                'sunrise': (datetime.fromtimestamp(entry['sys']['sunrise'])- timedelta(hours=10)).strftime('%Y-%m-%d %I:%M:%S %p'),
                'sunset': (datetime.fromtimestamp(entry['sys']['sunset'])- timedelta(hours=10)).strftime('%Y-%m-%d %I:%M:%S %p')
            }
            for entry in extracted_destinations
        ]
        return result

    # @task
    # def test_task_fail(test):
    #     raise ValueError("This task is designed to fail.")

    @task
    def load_s3(data):
        s3 = boto3.client('s3')
        bucket_name = 'alan-learning-etl-project'
        s3_key = 'output/output.csv'

        target_fields = ['name', 'date', 'weather', 'temp', 'humidity', 'wind', 'snow', 'rain', 'sunrise', 'sunset']
        rows = [[entry['name'], entry['date'], entry['weather'], entry['temp'], entry['humidity'], entry['wind'], entry['snow'], entry['rain'], entry['sunrise'], entry['sunset']] for entry in data]
        rows.insert(0, target_fields)
        
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerows(rows)

        file = csv_buffer.getvalue()

        try:
            s3.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=file
            )
            return f"s3://{bucket_name}/{s3_key}"
        except Exception as e:
            raise Exception(f"Failed to upload file to S3: {str(e)}")
        finally:
            csv_buffer.close()

    # extracting data with task
    extracted_destinations=[]
    for destination in destinations:
        destination_task_id = destination['location'].replace(' ', '_').lower()
        get_weather_results_task = HttpOperator(
            task_id =f'weather_fetch_{destination_task_id}',
            method = 'GET',
            http_conn_id='openweathermap_api',
            endpoint=f'/data/2.5/weather',
            headers={"Content-Type": "application/json"},
            data={
                'lat':destination['lat'],
                'lon':destination['lon'],
                'appid':OPENWEATHERMAP_API_KEY,
                'units':'metric'
            },
            do_xcom_push=True,
        )
        extracted_destinations.append(extract(api_results=get_weather_results_task.output))

    transformed_data = transform(extracted_destinations)
    load_s3(transformed_data)
    # test_task_fail(transformed_data)


weather_etl()
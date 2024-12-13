# API-Pipeline
## About
API pipeline extracts data from OpenWeatherAPI, transforms the data into tabular form, and loads it into s3 every 3 hours. It uses Apache Airflow to orchestrate the ETL pipeline and Amazon MWAA to manage the workflow in the cloud.
OpenWeatherAPI can be easily replaced with another API. 
## Installation
Nothing needs to be installed locally
### S3 Setup
- bucket_name/
  - dags/
    - weather_dag.py
  - requirements/
    - requirements.txt
### Secret Manager Setup
* Key : Value
  * "OPENWEATHERMAP_API_KEY" : "YOUR_API_KEY"
### MWAA Setup
- Create a MWAA environment
  - Networking
    - Web server access: Public Access
    - Allow MWAA to create a new security group unless you have one already setup
  - Environment Class
    - mw1.micro works for this project
    - mw1.small can be used if you want to increase worker count
  - Configuration
    - secrets.backend : airflow.providers.amazon.aws.secrets.secrets_manager.SecretsManagerBackend
    - secrets.backend_kwargs : {"connections_prefix" : "airflow/connections", "variables_prefix" : "airflow/openweatherapi"}
    - smtp.smtp_user :
    - smtp.smtp_password :
      - "airflow/openweatherapi" should be your secret name
  - Permissions - Execution Role
    - Allow AWS to create default permissions
      - Add s3 PUT Objects and Secret Manager List and Read
  
### Airflow UI
  - Admin -> Connections
    - Connection Id: openweathermap_api
    - Connection Type: HTTP
    - Host: https://api.openweathermap.org

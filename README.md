# WeatherAPI Pipeline
## About
API pipeline extracts data from OpenWeatherAPI, transforms the data into tabular form, and loads it into s3 every 3 hours. It uses Apache Airflow to orchestrate the ETL pipeline and Amazon MWAA to manage the workflow in the cloud.
OpenWeatherAPI can be easily replaced with another API. 
## To-Do
- [x] Add on failure callback email (Complete)
- [x] Sequential Tasks to Dynamic Task Mapping (Complete)
- [ ] Vet MWAA Policy (Incomplete)
- [x] Move to parquet format (Complete)
- [ ] Update for Docker to run locally (Incomplete)

## Installation
Nothing needs to be installed locally
### S3 Setup
- bucket_name/
  - dags/
    - weather_dag.py
  - requirements/
    - requirements.txt
### Secret Manager Setup
- Key : Value
  - "OPENWEATHERMAP_API_KEY" : "YOUR_API_KEY"
  - "SMTP_USER" : "YOUR_EMAIL"
  - "SMTP_PASSWORD" : "YOUR_EMAIL_PASSWORD"
    - go to your gmail account -> security -> 2FA -> add an app password for less secure apps

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
      - "airflow/openweatherapi" should be your secret name
    - smtp.smtp_host : smtp.gmail.com
    - smtp.smtp_ssl : False
    - smtp.smtp_smtp_mail_from : "your_email"
    - smtp.smtp_port : 587

    - smtp.smtp_starttls : True

  - Permissions - Execution Role
    - Allow AWS to create default permissions
      - Add s3 PUT Objects and Secret Manager List and Read

### MWAA Execution Policy
- Tip: Make sure that the ARNs match the MWAA. Issues when copying old policies for new MWAA environments
- Add s3 PUT Objects and Secret Manager List and Read
- Add GetLogEvents abd DescribeLogStreams
  - need to recheck these permissions
### Airflow UI
  - Admin -> Connections
    - Connection Id: openweathermap_api
    - Connection Type: HTTP
    - Host: https://api.openweathermap.org

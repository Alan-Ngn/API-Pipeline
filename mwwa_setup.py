import boto3

def create_mwaa_environment():
    mwaa = boto3.client('mwaa')

    response = mwaa.create_environment(
        Name='WeatherAirflowEnvironment',
        AirflowVersion='2.8.3',  # Example: Specify the version
        SourceBucketArn=
        ExecutionRoleArn=
        DagS3Path='dags/',
        EnvironmentClass='mw1.small',
        MaxWorkers=2,
        MinWorkers=1,
        SchedulerCount=1,
        NetworkConfiguration={
            'SecurityGroupIds': [

            ],
            'SubnetIds': [

            ],
        },
        LoggingConfiguration={
            'DagProcessingLogs': {
                'Enabled': True,
                'LogLevel': 'INFO',
            },
            'SchedulerLogs': {
                'Enabled': True,
                'LogLevel': 'INFO',
            },
            'WorkerLogs': {
                'Enabled': True,
                'LogLevel': 'INFO',
            },
            'WebserverLogs': {
                'Enabled': True,
                'LogLevel': 'INFO',
            },
            'TaskLogs': {
                'Enabled': True,
                'LogLevel': 'INFO',
            },
        },
        WeeklyMaintenanceWindowStart='SUN:06:30'
    )
    print(response)


if __name__ == "__main__":
    create_mwaa_environment()

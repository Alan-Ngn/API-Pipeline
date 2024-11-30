import boto3
import botocore
import os
s3 = boto3.client('s3')
region = 'us-west-1'
bucket_name = 'alan-learning-etl-project'



def create_s3_bucket(bucket_name, region=None):
    bucket_list = s3.list_buckets()['Buckets']
    try:
        if [bucket['Name'] for bucket in bucket_list if bucket['Name']==bucket_name]:
            print(f"Bucket {bucket_name} already exists")
        elif region is None:
            s3.create_bucket(Bucket=bucket_name)
            print(f"Bucket {bucket_name} created successfully")
        else:
            s3.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={
                    'LocationConstraint':region
                }
            )
            print(f"Bucket {bucket_name} created successfully")
    except botocore.exceptions.ClientError as e:
        print(f"Error creating bucket: {e}")
        return False
    return bucket_name



def upload_to_s3(Bucket):
    folder_path = f'dags'
    file_path=f'dags/'
    files = os.listdir(folder_path)
    file = files[1:][0]
    object_list = s3.list_objects_v2(
        Bucket=bucket_name,
        Prefix=file_path
    )

    # print('object_list:',object_list)
    if object_list['KeyCount']:
        object = [object['Key'] for object in object_list['Contents']]
        # print(object)
        if f'{file_path}{file}' not in object:
            Filename = f'{folder_path}/{file}'
            Key = f'{file_path}{file}'
            try:
                s3.upload_file(
                    Filename,
                    Bucket,
                    Key
                )
                print(f'{file} successfully uploaded')
            except botocore.exceptions.ClientError as e:
                print(f"Error uploading file: {e}")

        else:
            print(f'{file} already uploaded')
    elif object_list['KeyCount'] == 0:
        Filename = f'{folder_path}/{file}'
        Key = f'{file_path}{file}'
        try:
            s3.upload_file(
                Filename,
                Bucket,
                Key
            )
            print(f'{file} successfully uploaded')
        except botocore.exceptions.ClientError as e:
            print(f"Error uploading file: {e}")


if __name__ == "__main__":
    Bucket =  create_s3_bucket(bucket_name, region)
    if Bucket:
        upload_to_s3(Bucket)
    else:
        print("upload_s3 error")

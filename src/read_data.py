import boto3
import botocore
import config
import json


def read_s3_bucket():
    # configure S3 resource.
    session = boto3.session.Session(aws_access_key_id=config.AWS_S3_ACCESS_KEY_ID,
                                    aws_secret_access_key=config.AWS_S3_SECRET_ACCESS_KEY)
    s3_resource = session.resource('s3', config=botocore.client.Config(
        signature_version='s3v4'))
    obj = s3_resource.Object(config.AWS_BUCKET_NAME, "anchor-packages.json").get()['Body'].read()
    utf_data = obj.decode("utf-8")
    return json.loads(utf_data)

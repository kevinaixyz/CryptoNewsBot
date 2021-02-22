from googleapiclient import discovery
from google.cloud import storage
import json
import requests
from config import config

# export GOOGLE_APPLICATION_CREDENTIALS="rni-onchain-f1e6e7c3ea90.json"


def upload_google_storage(source_file_name, data, credentials):
    """Uploads a file to the bucket."""
    # bucket_name = "your-bucket-name"
    # source_file_name = "local/path/to/file"
    # destination_blob_name = "storage-object-name"

    # service = discovery.build('storage', 'v1', credentials=credentials)
    # request = service.objects().insert(bucket=config.BUCKET_NAME, body=data, contentEncoding='UTF-8', name=source_file_name)
    # response = request.execute()
    url = 'https://storage.googleapis.com/upload/storage/v1/b/{}/o?uploadType=media&contentEncoding=UTF-8&name={}'.format(config.BUCKET_NAME, source_file_name)
    headers = {
        'Content-Type':'text/json',
        'Authorization': 'Bearer {}'.format(credentials.token),
    }
    response = requests.post(url, data=data.encode('UTF-8'), headers=headers)
    """Uploads a file to the bucket."""
    # bucket_name = "your-bucket-name"
    # source_file_name = "local/path/to/file"
    # destination_blob_name = "storage-object-name"

    # storage_client = storage.Client(credentials=credentials)
    # bucket = storage_client.bucket(config.BUCKET_NAME)
    # blob = bucket.blob(source_file_name)
    #
    # blob.upload_from_string(data)
    return (response.status_code, response.text)
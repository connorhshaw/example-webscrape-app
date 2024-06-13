import os
import uuid
from dotenv import load_dotenv
from tempfile import NamedTemporaryFile
from azure.storage.blob import BlobClient

def upload_data_to_blob(container_name, data_file, blob_name):

    # Retrieve the connection string from an environment variable. Note that a
    # connection string grants all permissions to the caller, making it less
    # secure than obtaining a BlobClient object using credentials.
    #conn_string = os.environ["AZURE_STORAGE_CONNECTION_STRING"]
    load_dotenv()
    conn_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

    # Create the client object for the resource identified by the connection
    # string, indicating also the blob container and the name of the specific
    # blob we want.
    blob_client = BlobClient.from_connection_string(
        conn_string,
        container_name=container_name,
        blob_name=f"{blob_name}-{str(uuid.uuid4())[0:5]}.txt",
    )

    # Open a local file and upload its contents to Blob Storage
    #with open("stats.csv", "rb") as data:
    #    blob_client.upload_blob(data)
    #    print(f"Uploaded sample-source.txt to {blob_client.url}")
    blob_client.upload_blob(data_file)
    print(f"Uploaded {blob_name} to {blob_client.url}")


def upload_partial_data_on_date(data, date, container_name, blob_name):
    with NamedTemporaryFile(suffix=".csv") as temp_file:
        data.to_csv(temp_file.name)
        upload_data_to_blob(container_name, temp_file, f"{blob_name}-{str(date)}")


def upload_all_data_on_date(data, date):

    with NamedTemporaryFile(suffix=".csv") as temp_file:
        data['games'].to_csv(temp_file.name)
        upload_data_to_blob('games', temp_file, f"games-{str(date)}")

    with NamedTemporaryFile(suffix=".csv") as temp_file:
        data['stats'].to_csv(temp_file.name)
        upload_data_to_blob('stats', temp_file, f"stats-{str(date)}")

    with NamedTemporaryFile(suffix=".csv") as temp_file:
        data['shots'].to_csv(temp_file.name)
        upload_data_to_blob('shots', temp_file, f"shots-{str(date)}")

    with NamedTemporaryFile(suffix=".csv") as temp_file:
        data['plays'].to_csv(temp_file.name)
        upload_data_to_blob('plays', temp_file, f"plays-{str(date)}")
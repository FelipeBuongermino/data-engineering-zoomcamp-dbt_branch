import pandas as pd
from pathlib import Path
from prefect import flow, task
from prefect_gcp.cloud_storage import GcsBucket
from prefect.tasks import task_input_hash
from datetime import timedelta


@task(log_prints=True)
def write_gcs(path):
    gcp_block= GcsBucket.load("zoom-gcs")
    gcp_block.upload_from_path(from_path=f"{path}",to_path=path)
    return


@task(log_prints=True)
def write_local(df, color, dataset_file):
    path = Path(f"data/{color}/{dataset_file}.parquet")
    df.to_parquet(path, compression="gzip")
    return path


@task(log_prints=True)
def clean_data(df):
    df['tpep_pickup_datetime'] = pd.to_datetime(df['tpep_pickup_datetime'])
    df['tpep_dropoff_datetime'] = pd.to_datetime(df['tpep_dropoff_datetime'])
    return df


@task(log_prints=True, retries=3, cache_key_fn=task_input_hash, cache_expiration=timedelta(days=1))
def fetch(dataset_url):
    """Read taxi data from web into dataframe"""
    df = pd.read_csv(dataset_url)
    return df


@flow(name="Main Flow")
def etl_web_to_gcs():
    color = "yellow"
    year = 2021
    month = 2
    dataset_file = f"{color}_tripdata_{year}-{month:02}"
    dataset_url = f"https://github.com/DataTalksClub/nyc-tlc-data/releases/download/{color}/{dataset_file}.csv.gz"
    df = fetch(dataset_url)
    clean_df = clean_data(df)
    path_file = write_local(clean_df,color,dataset_file)
    write_gcs(path_file)


if __name__ == "__main__":
    etl_web_to_gcs()

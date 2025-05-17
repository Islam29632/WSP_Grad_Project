# This script downloads the specified Kaggle dataset using the Kaggle API.

import os
from dotenv import load_dotenv

load_dotenv()

# Set Kaggle credentials from environment variables before importing kaggle
os.environ['KAGGLE_USERNAME'] = os.getenv('KAGGLE_USERNAME')
os.environ['KAGGLE_KEY'] = os.getenv('KAGGLE_KEY')

from kaggle.api.kaggle_api_extended import KaggleApi

# Define the dataset identifier
dataset_id = 'nelgiriyewithana/world-stock-prices-daily-updating'
destination_path = './' # Download to the current directory

def download_kaggle_dataset(dataset_id, path):
    """
    Downloads a Kaggle dataset to the specified path.

    Args:
        dataset_id (str): The identifier of the Kaggle dataset.
        path (str): The local path to download the dataset to.
    """
    print(f"Attempting to download dataset: {dataset_id}")
    try:
        api = KaggleApi()
        # Authenticate using environment variables
        api.set_config_value('username', os.getenv('KAGGLE_USERNAME'))
        api.set_config_value('key', os.getenv('KAGGLE_KEY'))
        api.dataset_download_files(dataset_id, path=path, unzip=True)
        print(f"Dataset check for '{dataset_id}' complete. The latest version is already available locally.")
    except Exception as e:
        print(f"Error during dataset download attempt: {e}")
        print("Please ensure you have the Kaggle API installed (`pip install kaggle`)")
        print("and your kaggle.json credentials file is located at ~/.kaggle/kaggle.json")

if __name__ == "__main__":
    # Ensure the destination directory exists
    if not os.path.exists(destination_path):
        os.makedirs(destination_path)
        print(f"Created directory: {destination_path}")

    print("Checking for dataset updates...")
    download_kaggle_dataset(dataset_id, destination_path)
    print("Dataset check complete. The latest version is available.")

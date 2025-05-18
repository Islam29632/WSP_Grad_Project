"""
Download - or update - the World-Stock-Prices dataset from Kaggle.
Falls back to the CLI if the user’s kaggle wheel is too old.
"""

import os, subprocess, shutil
from dotenv import load_dotenv
from kaggle.api.kaggle_api_extended import KaggleApi

load_dotenv()

os.environ["KAGGLE_USERNAME"] = os.getenv("KAGGLE_USERNAME", "")
os.environ["KAGGLE_KEY"]     = os.getenv("KAGGLE_KEY",     "")

DATASET_ID = "nelgiriyewithana/world-stock-prices-daily-updating"
DEST       = "backend/data/raw"
os.makedirs(DEST, exist_ok=True)


def download_api():
    api = KaggleApi()
    api.authenticate()                                   # uses env vars
    api.dataset_download_files(DATASET_ID, path=DEST, unzip=True)


def download_cli():
    if shutil.which("kaggle") is None:
        raise RuntimeError("Kaggle CLI not found - run  pip install kaggle")
    subprocess.run(
        ["kaggle", "datasets", "download", "-d", DATASET_ID, "-p", DEST, "--unzip"],
        check=True,
    )


if __name__ == "__main__":
    print("⇣ Checking dataset on Kaggle …")
    try:
        download_api()
        print("✓ Download via kaggle-API succeeded")
    except AttributeError as e:                # very old wheel
        print(f"API attr error → {e}  ➜ trying CLI")
        download_cli()
    except Exception as e:
        print(f"API failed → {e}  ➜ trying CLI")
        download_cli()

    print("Dataset ready under", DEST)

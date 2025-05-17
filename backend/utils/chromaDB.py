import yfinance as yf
import chromadb
from chromadb.utils import embedding_functions
import datetime
import pandas as pd
from chromadb.config import Settings # Import Settings
import chromadb
tickers = ['PTON', 'AMD', 'ADDYY', 'AXP', 'PMMAF', 'V', 'ADBE', 'UL', 'CSCO',
           'JPM', 'LVMUY', 'ABNB', 'MAR', 'UBSFY', 'ZI', 'TM', 'HLT', 'MCD',
           'HD', 'MA', 'JNJ', 'UBER', 'PG', 'COIN', 'FDX', 'MMM', 'JWN',
           'PHG', 'NFLX', 'KO', 'FL', 'CROX', 'LUV', 'SHOP', 'AMZN', 'AAPL',
           'NKE', 'TGT', 'GOOGL', 'SPOT', 'ZM', 'DIS', 'RBLX', 'NTDOY', 'DAL',
           'MSFT', 'COST', 'AEO', 'HSY', 'TSLA', 'PINS', 'BAMXF', 'CMG',
           'POAHY', 'LOGI', 'CL', 'CRM', 'NVDA', 'SBUX', 'HMC', 'SQ']

def get_yfinance_data(tickers):
    """
    Fetches historical stock data for the given tickers from yfinance.

    Returns:
    A dictionary where keys are tickers and values are Pandas DataFrames.
    """
    data = {}
    for ticker in tickers:
        try:
            print(f"Fetching data for {ticker}...")
            ticker_data = yf.Ticker(ticker)
            historical_data = ticker_data.history(period="1y")  # Adjust the period as needed
            data[ticker] = historical_data
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            data[ticker] = None  # Store None to indicate failure
    return data

def create_chroma_collection(client, collection_name="stock_data"):
    """
    Creates a Chroma collection.

    Args:
        client: The Chroma client.
        collection_name: The name of the collection.

    Returns:
        The Chroma collection object.
    """
    collection = client.get_or_create_collection(name=collection_name)
    return collection

def add_data_to_chroma(collection, data):
    """
    Adds the yfinance data to a Chroma collection.

    Args:
        collection: The Chroma collection.
        data: A dictionary where keys are tickers and values are Pandas DataFrames.
    """
    for ticker, df in data.items():
        if df is not None:
            records = df.to_dict(orient="records")
            ids = []
            documents = []
            metadatas = []

            for i, record in enumerate(records):
                record_id = f"{ticker}_{i}"
                ids.append(record_id)
                document_string = f"Date: {record['Open']}, Open: {record['Open']}, High: {record['High']}, Low: {record['Low']}, Close: {record['Close']}, Volume: {record['Volume']}"
                documents.append(document_string)
                metadatas.append({
                    "ticker": ticker,
                    "date": str(df.index[i]),
                    "open": record['Open'],
                    "high": record['High'],
                    "low": record['Low'],
                    "close": record['Close'],
                    "volume": record['Volume'],
                })
            try:
                collection.add(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas,
                )
                print(f"Added data for {ticker} to ChromaDB.")
            except Exception as e:
                print(f"Error adding data for {ticker} to ChromaDB: {e}")
        else:
            print(f"Skipping {ticker} as no data was retrieved.")

if __name__ == "__main__":
    # 1. Get data from yfinance
    yf_data = get_yfinance_data(tickers)

    # 2. Initialize Chroma client with persistence
    # Specify the directory where you want to save the database
    persist_directory = "stock_data_chroma"
    client = chromadb.PersistentClient(path="chroma_db")  # Persistence enabled

    # 3. Create a Chroma collection
    chroma_collection = create_chroma_collection(client)

    # 4. Add data to Chroma
    add_data_to_chroma(chroma_collection, yf_data)

    # 5. Persist the data to disk (optional, but recommended for clarity)

    print(f"Data ingestion into ChromaDB complete.  Data persisted to {persist_directory}")

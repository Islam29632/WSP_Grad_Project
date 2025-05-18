import pandas as pd
import os
from crewai.tools import tool
from typing import Optional,List, Dict, Any
import json
from utils.data_processor import train_and_forecast
@tool("process_data")
def preprocess( min_rows: int = 20) -> pd.DataFrame:
        """Preprocesses stock data by standardizing column names and ensuring a minimum number of rows."""

        # Step 1: Standardize column names
        df = pd.read_csv('data/processed/cleaned_stock_data.csv')
        df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]
        '''
        # Step 2: Filter for specific tickers
        if tickers:
            tickers = [t.upper() for t in tickers]
            df = df[df['ticker'].isin(tickers)]
        '''
        # Step 3: Convert 'Date' to datetime and drop rows with missing 'Close' values
        df['date'] = pd.to_datetime(df['date'], utc=True)
        df = df.dropna(subset=['close'])

        # Step 4: Sort by 'ticker' and 'date', then fill missing values by ticker
        df = df.sort_values(by=['ticker', 'date']).reset_index(drop=True)
        df = df.groupby('ticker').apply(lambda g: g.ffill().bfill()).reset_index(drop=True)

        # Step 5: Feature engineering - Use `transform` instead of `apply`
        df['sma_5'] = df.groupby('ticker')['close'].transform(lambda x: x.rolling(window=5).mean())
        df['sma_10'] = df.groupby('ticker')['close'].transform(lambda x: x.rolling(window=10).mean())
        df['sma_21'] = df.groupby('ticker')['close'].transform(lambda x: x.rolling(window=21).mean())
        df['std_5'] = df.groupby('ticker')['close'].transform(lambda x: x.rolling(window=5).std())
        df['return'] = df.groupby('ticker')['close'].pct_change()

        # Step 6: Drop tickers with fewer than 'min_rows' records
        valid_tickers = df['ticker'].value_counts()[lambda x: x >= min_rows].index
        df = df[df['ticker'].isin(valid_tickers)]

        # Step 7: Drop rows with remaining NaNs in the features
        df = df.dropna(subset=['sma_5', 'sma_10', 'sma_21', 'std_5', 'return'])

        # Step 8: Select relevant columns
        df = df[
            ['date', 'ticker', 'open', 'high', 'low', 'close', 'volume', 'industry_tag', 'sma_5', 'sma_10', 'sma_21',
             'std_5', 'return']]

        OUTPUT_PATH ='data/processed/cleaned_stock_data2.csv'
        os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
        df.to_csv(OUTPUT_PATH, index=False)
        return df

@tool("show_one")
def show_ticker(tickers: list[str]) -> pd.DataFrame:
    """Fetches data for a list of specific tickers from the cleaned stock data."""
    df = pd.read_csv('data/processed/cleaned_stock_data2.csv')
    list_of_dfs = [] # Initialize an empty list to store DataFrames
    for ticker in tickers:
        ticker_df = df[df['ticker'] == ticker].copy()
        list_of_dfs.append(ticker_df)

    if list_of_dfs:
        combined_df = pd.concat(list_of_dfs).reset_index(drop=True)
        return combined_df
    else:
        return pd.DataFrame()


@tool("fetch_data")
def collect() -> pd.DataFrame:
        """Fetcnong stock data and taks the important rows."""
        # Initialize 'data' as an empty DataFrame
        data = pd.DataFrame()
        df = pd.read_csv("database/World-Stock-Prices-Dataset.csv")
        data = df[['Industry_Tag', 'Date', 'Open', 'High', 'Low', 'Close', 'Volume','Ticker']].dropna()
        OUTPUT_PATH ='data/processed/cleaned_stock_data.csv'
        os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
        df.to_csv(OUTPUT_PATH, index=False)
        return data

@tool("generate_sector_map")
def generate_sector_map() ->  pd.DataFrame:
    """Generates a mapping of stock tickers to their industry sectors and saves it to a JSON file."""
    input_csv = "data/processed/cleaned_stock_data2.csv"
    output_json = "outputs/ticker_sector_map.json"
    df = pd.read_csv(input_csv)
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]
    df = df.dropna(subset=["ticker", "industry_tag"])

    ticker_sector_map = (
        df.groupby("ticker")["industry_tag"]
       .agg(lambda x: x.value_counts().idxmax())
       .to_dict()
    )

    os.makedirs("outputs", exist_ok=True)
    with open(output_json, "w") as f:
        json.dump(ticker_sector_map, f, indent=4)
    print(f"✅ Saved sector map with {len(ticker_sector_map)} entries to {output_json}")
    return ticker_sector_map

@tool("compute_statistics")
def compute_statistics() -> pd.DataFrame:
    """Computes and saves sector and ticker statistics based on historical stock data and a sector map."""
    # Load and clean the CSV
    input_csv = "data/processed/cleaned_stock_data2.csv"
    sector_map_path = "outputs/ticker_sector_map.json"
    df = pd.read_csv(input_csv)
    df['date'] = pd.to_datetime(df['date'], utc=True)
    # Load sector mapping
    with open(sector_map_path, "r") as f:
        sector_map = json.load(f)

    # Filter only known tickers
    df = df[df["ticker"].isin(sector_map.keys())]

    # Vectorized statistics
    hi = df.groupby("ticker")["high"].max().rename("highest_price")
    lo = df.groupby("ticker")["low"].min().rename("lowest_price")

    y20 = df[df.date.dt.year == 2020]
    growth = (
            (y20.groupby("ticker")["close"].last() -
             y20.groupby("ticker")["close"].first()) /
            y20.groupby("ticker")["close"].first() * 100
    ).rename("growth_2020_percent")

    # Merge all stats
    summary_df = pd.concat([hi, lo, growth], axis=1).reset_index()

    # Add sector info to each ticker
    summary_df["sector"] = summary_df["ticker"].map(sector_map)

    # Per-sector averages
    sector_summary = summary_df.groupby("sector").agg({
        "growth_2020_percent": lambda x: round(x.dropna().mean(), 2),
        "highest_price": lambda x: round(x.mean(), 2),
        "lowest_price": lambda x: round(x.mean(), 2)
    }).reset_index()

    # Save to JSON
    os.makedirs("outputs", exist_ok=True)
    summary_df.set_index("ticker").to_json("outputs/ticker_analysis.json", indent=4, orient="index")
    sector_summary.to_json("outputs/sector_summary.json", indent=4, orient="records")
    print("Sector and ticker statistics saved to outputs/")
    return sector_summary

@tool("forecast_prices")
def forecast_prices(tickers: Optional[list] = None) -> str:
    """Forecasts prices for a given list of tickers using a pre-existing function."""
    # Assuming train_and_forecast function is defined elsewhere and accessible

    results = train_and_forecast(tickers)

    if not results:
        return "Forecasting failed or no tickers were processed."

    output_path = "outputs/forecast_results.json"
    print(f"Forecasting complete for {len(results)} tickers. Results saved to {output_path}")
    return results


#Importing
from crewai import LLM,Agent
import google.generativeai as genai
import os
from dotenv import load_dotenv
import pandas as pd
from typing import Optional

#Loading the environment variables
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=api_key)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
local_loc = os.path.join(project_root, "backend", "database", "World-Stock-Prices-Dataset.csv")

#local_loc = r"C:\Users\Ostor\PycharmProjects\PythonProject\.venv\WSP\World-Stock-Prices-Dataset.csv"
#Note All the Agents are built almost the same but the configurations only different.
#Creating Class Collectorgent
class Collectorgent(Agent):
    def __init__(self):

        #Setting the parametter to be used
        gemini_pro = "gemini/gemini-1.5-pro" # has 15 requests limit per day
        gemini_flash = "gemini/gemini-2.0-flash" # has 1500 requests limit per day
        gemini_llm = LLM(model=gemini_flash, api_key=api_key)
        
        # Setting the parameter to be used
        super().__init__(
            role = "Stock Data Collector", #what the agent acts like
            goal = "Fetch Companies Stocks", #mission
            backstory = #agent characteristics
               "You are a seasoned data engineer and analyst with years of experience in collecting raw data from csv files. "
               "cleaning inconsistencies, handling missing values, and converting it into structured formats."
               "You understand that clean, well-prepared data is the foundation of every successful AI project."
               "You've worked across domains and know how to deal with messy, real-world data using modern tools and best practices."
                "You mastered working with Stocking data and know how to handle them."
            ,
            llm = gemini_llm #LLM model -> Gemini
                    )
    def data_loc(self):
        return local_loc

    def collect(self, targets: Optional[list], col_name="Ticker") -> pd.DataFrame:
        # Initialize 'data' as an empty DataFrame
        data = pd.DataFrame()
        df = pd.read_csv(self.data_loc())
        if targets:
            for target in targets:
                if target in df[col_name].unique():
                    # Concatenate only if target is found in the 'col_name' column
                    data = pd.concat([data, df[df[col_name] == target]], ignore_index=True)
                else:
                    print(f"Target '{target}' Not Found")
        else:
            # Select specific columns (Note: Correct column selection syntax)
            data = df[['Industry_Tag', 'Date', 'Open', 'High', 'Low', 'Close', 'Volume']]

        return data

    def preprocess(self, df: pd.DataFrame, tickers: Optional[list] = None, min_rows: int = 20) -> pd.DataFrame:
        # Step 1: Standardize column names
        df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

        # Step 2: Filter for specific tickers
        if tickers:
            tickers = [t.upper() for t in tickers]
            df = df[df['ticker'].isin(tickers)]

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

        return df


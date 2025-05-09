import os
import json
import pandas as pd
from crewai import Agent
from crewai.llm import LLM
from dotenv import load_dotenv
from utils.data_processor import train_and_forecast

# Load environment variables from .env
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class DataProcessorAgent(Agent):
    def __init__(self):
        dummy_llm = LLM(model="gemini/gemini-1.5-flash", api_key=GEMINI_API_KEY)

        super().__init__(
            role="Financial Data Analyst Agent",
            goal="Perform sector classification, compute historical stock performance metrics, and deliver accurate time series forecasts for selected tickers.",
            backstory=(
                "An expert in quantitative finance and machine learning, this agent specializes in processing large-scale financial datasets, "
                "deriving insightful metrics, and generating reliable forecasts using advanced deep learning models. With a strong background "
                "in financial time series modeling and domain-specific knowledge of equity markets, the agent enables data-driven decisions "
                "for investment strategies and market analysis."
            ),
            llm=dummy_llm
        )

    def generate_sector_map(self, input_csv="data/raw/World-Stock-Prices-Dataset.csv", output_json="outputs/ticker_sector_map.json") -> str:
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

        return f"✅ Saved sector map with {len(ticker_sector_map)} entries to {output_json}"

    def compute_statistics(self, input_csv="data/raw/World-Stock-Prices-Dataset.csv", sector_map_path="outputs/ticker_sector_map.json") -> str:

        # Load and clean the CSV
        df = pd.read_csv(input_csv)
        df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]
        df["date"] = pd.to_datetime(df["date"], utc=True)

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

        return "Sector and ticker statistics saved to outputs/"
        
    def forecast_prices(self, tickers=None) -> str:
        results = train_and_forecast(tickers)

        if not results:
            return "Forecasting failed or no tickers were processed."

        output_path = "outputs/forecast_results.json"
        return f"Forecasting complete for {len(results)} tickers. Results saved to {output_path}"

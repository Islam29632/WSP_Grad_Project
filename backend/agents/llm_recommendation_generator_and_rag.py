import os
import yfinance as yf
import google.generativeai as genai
from crewai import LLM, Agent
from dotenv import load_dotenv
from langchain_community.embeddings import HuggingFaceEmbeddings
import duckdb
import pandas as pd
from typing import Optional, Dict, Any
from pydantic import ConfigDict

# Load API key from environment
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

duckdb_file = "../backend/input/stock_data.db"

gemini_pro = "gemini/gemini-1.5-pro"  # has 15 requests limit per day
gemini_flash = "gemini/gemini-2.0-flash"  # has 1500 requests limit per day


class LLMRecommendationAgent(Agent):
    duckdb_con: Optional[duckdb.DuckDBPyConnection] = None

    # Pydantic V2 model config
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="forbid"
    )

    def __init__(self):
        super().__init__(
            role="LLM Financial Advisor",
            goal="Provide Buy/Hold/Sell recommendations with stock info from yfinance and insights from DuckDB",
            backstory=(
                "An expert LLM-powered advisor trained on market analytics and risk-based decision making. "
                "Combines real-time stock data from yfinance with insights retrieved from a DuckDB database."
            ),
            llm=LLM(model=gemini_flash, api_key=api_key),
        )
        self._initialize_duckdb()

    def _initialize_duckdb(self):
        """Connect to the DuckDB database."""
        try:
            self.duckdb_con = duckdb.connect(database=duckdb_file, read_only=True)
            print(f"[DuckDB Init] Successfully connected to '{duckdb_file}'.")
        except Exception as e:
            print(f"[DuckDB Init Error] {e}")

    def _get_duckdb_context(self, symbol: str, sector: str) -> str:
        if not self.duckdb_con:
            return ""

        table_name = f"{symbol.lower()}_historical"
        try:
            # Construct a query to get relevant information. You might need to adjust this
            # based on what kind of "RAG" context you want to extract from the historical data.
            # This example fetches the latest 5 closing prices and the average volume.
            query = f"""
                SELECT Close FROM {table_name} ORDER BY Date DESC LIMIT 5;
                SELECT AVG(Volume) FROM {table_name};
            """
            results = self.duckdb_con.execute(query).fetchall()

            if results:
                latest_closes = ", ".join(str(r[0]) for r in results[0])
                avg_volume = results[1][0] if results[1] else "N/A"
                context = (
                    f"\nHistorical Stock Data (from DuckDB):\n"
                    f"- Latest 5 Closing Prices: {latest_closes}\n"
                    f"- Average Volume: {avg_volume:.2f}\n"
                    f"- Note: This is a basic example. You can create more sophisticated "
                    f"queries to extract more meaningful context."
                )
                return context
            else:
                return f"\nNo historical data found in DuckDB for '{symbol}'."

        except Exception as e:
            print(f"[DuckDB Retrieval Error] {e}")
            return ""

    def _get_yfinance_info(self, symbol: str) -> Dict[str, Any]:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return {
                "company_name": info.get("longName", "N/A"),
                "sector": info.get("sector", "N/A"),
                "industry": info.get("industry", "N/A"),
                "current_price": info.get("currentPrice", info.get("regularMarketPrice", "N/A")),
                "market_cap": info.get("marketCap", "N/A"),
                "pe_ratio": info.get("trailingPE", "N/A"),
                "dividend_yield": info.get("dividendYield", "N/A"),
                "52_week_high": info.get("fiftyTwoWeekHigh", "N/A"),
                "52_week_low": info.get("fiftyTwoWeekLow", "N/A"),
                "beta": info.get("beta", "N/A")
            }
        except Exception as e:
            print(f"[yfinance Error] {e}")
            return {}

    def generate_recommendations(self,user_pov: str = "moderate investor") -> dict:
        output = {}
        with open("../backend/outputs/forecast_results.json") as f1, open("../backend/outputs/ticker_analysis.json") as f2:
            forecast_data_u = json.load(f1)
            forecast_data_u = json.load(f2)

            # Filter data for our target tickers
        forecast_data = {k: v for k, v in forecast_data_u.items() if k in tickers}
        analysis_data = {k: v for k, v in forecast_data_u.items() if k in tickers}

        for symbol, forecast in forecast_data.items():
            analysis = analysis_data.get(symbol)
            if not analysis:
                output[symbol] = {"error": "Missing analysis data"}
                continue

            yfinance_info = self._get_yfinance_info(symbol)
            sector = yfinance_info.get("sector", "N/A")
            duckdb_context = self._get_duckdb_context(symbol, sector)

            actual_price = forecast.get("actual_price", "N/A")
            target_date = forecast.get("target_date", "N/A")
            lstm_data = forecast.get("LSTM", {})
            mlp_data = forecast.get("MLP", {})

            lstm_forecast = lstm_data.get("forecast", "N/A")
            mlp_forecast = mlp_data.get("forecast", "N/A")

            try:
                lstm_rmse = lstm_data.get("rmse", float('inf'))
                mlp_rmse = mlp_data.get("rmse", float('inf'))
                best_model = "LSTM" if lstm_rmse < mlp_rmse else "MLP"
            except:
                best_model = "N/A"

            high = analysis.get("highest_price", "N/A")
            low = analysis.get("lowest_price", "N/A")
            growth = analysis.get("growth_2020_percent", "N/A")

            prompt = f'''
                You're a trusted financial advisor helping an investor decide what to do with their {symbol} stock.

                **Stock Information (from yfinance)**:
                - Company: {yfinance_info.get('company_name')}
                - Sector: {sector}
                - Industry: {yfinance_info.get('industry')}
                - Current Price: {round(float(actual_price), 2) if actual_price != 'N/A' else 'N/A'}
                - Market Cap: {yfinance_info.get('market_cap')}
                - P/E Ratio: {yfinance_info.get('pe_ratio')}
                - 52-Week Range: {yfinance_info.get('52_week_low')} - {yfinance_info.get('52_week_high')}

                **Technical Analysis**:
                - Current price: {round(float(actual_price), 2) if actual_price != 'N/A' else 'N/A'}
                - Forecasted range: {round(min(lstm_forecast, mlp_forecast), 2) if isinstance(lstm_forecast, (int, float)) and isinstance(mlp_forecast, (int, float)) else 'N/A'} to {round(max(lstm_forecast, mlp_forecast), 2) if isinstance(lstm_forecast, (int, float)) and isinstance(mlp_forecast, (int, float)) else 'N/A'}
                - Historical High: {high}
                - Historical Low: {low}
                - Growth during 2020: {growth}%

                {duckdb_context}

                **Instructions**:
                1. Provide clear recommendation: **Buy**, **Hold**, or **Sell**
                2. Explain reasoning in 2-4 sentences
                3. Consider: price trends, valuation metrics, sector outlook, and historical data from DuckDB.
                4. Use simple, non-technical language.
            '''

            try:
                model = genai.GenerativeModel(gemini_flash)
                response = model.generate_content(prompt)
                llm_text = response.text.strip() if response.text else "No response"
            except Exception as e:
                llm_text = f"Gemini API error: {e}"

            output[symbol] = {
                "recommendation": llm_text,
                "yfinance_info": yfinance_info,
                "technical_analysis": {
                    "best_model": best_model,
                    "current_price": actual_price,
                    "lstm_forecast": lstm_forecast,
                    "mlp_forecast": mlp_forecast,
                    "historical_high": high,
                    "historical_low": low,
                    "growth_2020": growth
                },
                "duckdb_used": bool(duckdb_context)
            }

        return output

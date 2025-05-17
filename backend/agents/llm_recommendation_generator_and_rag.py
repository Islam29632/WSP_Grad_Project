import os
import yfinance as yf
import google.generativeai as genai
from crewai import LLM,Agent
from dotenv import load_dotenv
from langchain_community.document_loaders import CSVLoader, JSONLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
import chromadb
from chromadb.config import Settings
from typing import Optional, Dict, Any
from chromadb import Client, Collection

# Load API key from environment
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
rag_file_path = "input/chroma_db"
gemini_pro = "gemini/gemini-1.5-pro"  # has 15 requests limit per day
gemini_flash = "gemini/gemini-2.0-flash"  # has 1500 requests limit per day

class LLMRecommendationAgent(Agent):
    chroma_client: Optional[Client] = None
    chroma_collection: Optional[Collection] = None
    # Setting the parametter to be used

    # Allow arbitrary types like ChromaDB Collection
    model_config = {
        "arbitrary_types_allowed": True
    }

    def __init__(self):
        super().__init__(
            role="LLM Financial Advisor",
            goal="Provide Buy/Hold/Sell recommendations with stock info from yfinance and RAG",
            backstory=(
                "An expert LLM-powered advisor trained on market analytics and risk-based decision making. "
                "Combines real-time stock data from yfinance with RAG-enhanced insights."
            ),
            llm= LLM(model=gemini_flash, api_key=api_key),
        )
        self._initialize_rag()



    def _initialize_rag(self):
        """Connect to existing ChromaDB persisted in chroma.sqlite3"""

        if not rag_file_path:
            print("[RAG Init] No file path provided.")
            return

        try:
            # Assume rag_file_path is a folder that contains chroma.sqlite3 (Chroma needs a folder, not file directly)
            persist_dir = os.path.dirname(rag_file_path) if rag_file_path.endswith(
                '.sqlite3') else rag_file_path

            self.chroma_client = Client(
                Settings(
                    persist_directory=persist_dir,
                    anonymized_telemetry=False
                )
            )

            # Connect to existing collection
            self.chroma_collection = self.chroma_client.get_or_create_collection(name="rag_collection")
            print("[RAG Init] Successfully connected to ChromaDB collection.")

        except Exception as e:
            print(f"[RAG Init Error] {e}")


    def _get_rag_context(self, symbol: str, sector: str) -> str:
        if not self.chroma_collection:
            return ""

        try:
            query = f"{symbol} stock in {sector} sector: financial analysis and outlook"
            embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
            # Use embed_documents or embed_query, NOT encode_documents
            vector = embeddings.embed_query(query)

            results = self.chroma_collection.query(query_embeddings=[vector], n_results=3)
            if not results or not results.get("documents"):
                return ""

            context = "\nAdditional Market Context (from RAG system):\n"
            for i, doc in enumerate(results['documents'][0]):
                context += f"- Source {i + 1}: {doc[:500]}"
                if len(doc) > 500:
                    context += "... [truncated]"
                context += "\n"
            return context
        except Exception as e:
            print(f"[RAG Retrieval Error] {e}")
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

    def generate_recommendations(self, forecast_data: dict, analysis_data: dict,
                                 user_pov: str = "moderate investor") -> dict:
        output = {}

        for symbol, forecast in forecast_data.items():
            analysis = analysis_data.get(symbol)
            if not analysis:
                output[symbol] = {"error": "Missing analysis data"}
                continue

            yfinance_info = self._get_yfinance_info(symbol)

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

            sector = analysis.get("sector", "N/A")
            rag_context = self._get_rag_context(symbol, sector)

            high = analysis.get("highest_price", "N/A")
            low = analysis.get("lowest_price", "N/A")
            growth = analysis.get("growth_2020_percent", "N/A")

            prompt = f'''
You're a trusted financial advisor helping an investor decide what to do with their {symbol} stock.

**Stock Information (from RAG)**:
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

{rag_context}

**Instructions**:
1. Provide clear recommendation: **Buy**, **Hold**, or **Sell**
2. Explain reasoning in 2-4 sentences
3. Consider: price trends, valuation metrics, sector outlook
4. Incorporate RAG insights if available
5. Use simple, non-technical language
'''

            try:
                model = genai.GenerativeModel(gemini_flash)
                response = model.generate_content(prompt)
                llm_text = response.text.strip() if response.text else "No response"
            except Exception as e:
                llm_text = f"Gemini API error: {e}"

            output[symbol] = {
                "recommendation": llm_text,
                "yfinance_info (RAG context)": yfinance_info,
                "technical_analysis": {
                    "best_model": best_model,
                    "current_price": actual_price,
                    "lstm_forecast": lstm_forecast,
                    "mlp_forecast": mlp_forecast,
                    "historical_high": high,
                    "historical_low": low,
                    "growth_2020": growth
                },
                "rag_used": bool(rag_context)
            }

        return output

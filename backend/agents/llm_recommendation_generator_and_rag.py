import os
import json
import yfinance as yf
import google.generativeai as genai
from crewai import Agent
from dotenv import load_dotenv
from langchain.document_loaders import TextLoader, JSONLoader, CSVLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from typing import Optional, Dict, Any

# Load API key from environment
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

class LLMRecommendationAgent(Agent):
    def __init__(self, rag_file_path: Optional[str] = None):
        super().__init__(
            role="LLM Financial Advisor",
            goal="Provide Buy/Hold/Sell recommendations with stock info from yfinance and RAG",
            backstory=(
                "An expert LLM-powered advisor trained on market analytics and risk-based decision making. "
                "Combines real-time stock data from yfinance with RAG-enhanced insights."
            ),
            llm=None
        )
        self.rag_file_path = rag_file_path
        self.vectorstore = self._initialize_rag() if rag_file_path else None

    def _initialize_rag(self):
        """Initialize RAG components using LangChain"""
        try:
            if self.rag_file_path.endswith('.txt'):
                loader = TextLoader(self.rag_file_path)
            elif self.rag_file_path.endswith('.csv'):
                loader = CSVLoader(self.rag_file_path)
            elif self.rag_file_path.endswith('.json'):
                loader = JSONLoader(
                    file_path=self.rag_file_path,
                    jq_schema='.',
                    text_content=False
                )
            else:
                raise ValueError(f"Unsupported file format: {self.rag_file_path}")
            
            documents = loader.load()
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            splits = text_splitter.split_documents(documents)
            
            embeddings = HuggingFaceEmbeddings(
                model_name="all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'}
            )
            
            return FAISS.from_documents(splits, embeddings)
            
        except Exception as e:
            print(f"Error initializing RAG: {e}")
            return None

    def _get_rag_context(self, symbol: str, sector: str) -> str:
        """Retrieve relevant context using RAG"""
        if not self.vectorstore:
            return ""
        
        try:
            query = f"{symbol} stock in {sector} sector: financial analysis and outlook"
            relevant_docs = self.vectorstore.similarity_search(query, k=3)
            
            if not relevant_docs:
                return ""
            
            context = "\nAdditional Market Context (from RAG system):\n"
            for i, doc in enumerate(relevant_docs):
                context += f"- Source {i+1}: {doc.page_content[:500]}"
                if len(doc.page_content) > 500:
                    context += "... [truncated]"
                context += "\n"
            
            return context
            
        except Exception as e:
            print(f"Error in RAG retrieval: {e}")
            return ""

    def _get_yfinance_info(self, symbol: str) -> Dict[str, Any]:
        """Fetch stock info from yfinance"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Extract relevant information
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
            print(f"Error fetching yfinance data for {symbol}: {e}")
            return {}

    def generate_recommendations(self, forecast_data: dict, analysis_data: dict,
                               user_pov: str = "moderate investor") -> dict:
        output = {}

        for symbol, forecast in forecast_data.items():
            analysis = analysis_data.get(symbol)
            if not analysis:
                output[symbol] = {"error": "Missing analysis data"}
                continue

            # Get yfinance data
            yfinance_info = self._get_yfinance_info(symbol)
            
            # Extract forecast data
            actual_price = forecast.get("actual_price", "N/A")
            target_date = forecast.get("target_date", "N/A")

            lstm_data = forecast.get("LSTM", {})
            mlp_data = forecast.get("MLP", {})

            lstm_forecast = lstm_data.get("forecast", "N/A")
            lstm_rmse = lstm_data.get("rmse", "N/A")

            mlp_forecast = mlp_data.get("forecast", "N/A")
            mlp_rmse = mlp_data.get("rmse", "N/A")
            
            # Pick the best model
            try:
                lstm_rmse = forecast.get("LSTM", {}).get("rmse", float('inf'))
                mlp_rmse = forecast.get("MLP", {}).get("rmse", float('inf'))
                best_model = "LSTM" if lstm_rmse < mlp_rmse else "MLP"
            except:
                best_model = "N/A"

            # Get RAG context
            sector = analysis.get("sector", "N/A")
            rag_context = self._get_rag_context(symbol, sector)

            # Get analysis info
            high = analysis.get("highest_price", "N/A")
            low = analysis.get("lowest_price", "N/A")
            growth = analysis.get("growth_2020_percent", "N/A")
            sector = analysis.get("sector", "N/A")

            # Construct the LLM prompt
            prompt = f'''
            You're a trusted financial advisor helping an investor decide what to do with their {symbol} stock.
            
            **Stock Information(from RAG)**:
            - Company: {yfinance_info.get('company_name', 'N/A')}
            - Sector: {sector}
            - Industry: {yfinance_info.get('industry', 'N/A')}
            - Current Price: {round(float(actual_price), 2) if actual_price != 'N/A' else 'N/A'}
            - Market Cap: {yfinance_info.get('market_cap', 'N/A')}
            - P/E Ratio: {yfinance_info.get('pe_ratio', 'N/A')}
            - 52-Week Range: {yfinance_info.get('52_week_low', 'N/A')} - {yfinance_info.get('52_week_high', 'N/A')}
            
            **Technical Analysis**:
             - Current price: {round(actual_price, 2)}
            - Forecasted range: {round(min(lstm_forecast, mlp_forecast), 2)} to {round(max(lstm_forecast, mlp_forecast), 2)}
            - Historical High: {high}
            - Historical Low: {low}
            - Growth during 2020: {growth}%
            - Sector: {sector}
            
            {rag_context}
            
            **Instructions**:
            1. Provide clear recommendation: **Buy**, **Hold**, or **Sell**
            2. Explain reasoning in 2-4 sentences
            3. Consider: price trends, valuation metrics, sector outlook
            4. Incorporate RAG insights if available
            5. Use simple, non-technical language
            '''

            # Call Gemini
            try:
                model = genai.GenerativeModel("gemini-1.5-flash")
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

if __name__ == "__main__":

    with open("outputs/forecast_results.json") as f1, open("outputs/ticker_analysis.json") as f2:
        forecast_data = json.load(f1)
        analysis_data = json.load(f2)

    agent = LLMRecommendationAgent()
    results = agent.generate_recommendations(forecast_data, analysis_data, user_pov="I'm a cautious investor seeking long-term growth.")

    with open("outputs/llm_recommendations.json", "w") as f:
        json.dump(results, f, indent=2)

    print("Saved LLM investment advice to outputs/llm_recommendations.json")


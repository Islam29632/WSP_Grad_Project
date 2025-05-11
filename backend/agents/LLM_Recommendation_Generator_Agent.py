# llm_recommendation_generator.py
import json
import os
from crewai import Agent
from crewai.llm import LLM
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class LLMRecommendationGenerator(Agent):
    def __init__(self):
        dummy_llm = LLM(model="gemini/gemini-1.5-flash", api_key=GEMINI_API_KEY)
        
        super().__init__(
            role="Financial Market Analyst",
            goal="Generate actionable investment recommendations based on technical analysis and forecasts",
            backstory=(
                "With years of experience in financial markets and AI-powered analysis, this agent specializes in "
                "synthesizing complex financial data into clear, actionable recommendations. Combining technical "
                "analysis skills with deep learning insights, it provides institutional-grade recommendations "
                "tailored to different investment horizons and risk profiles."
            ),
            llm=dummy_llm,
            allow_delegation=False
        )
        
    def _load_analysis_data(self):
        """Load all the processed data from previous agents"""
        try:
            with open("outputs/ticker_analysis.json", "r") as f:
                ticker_analysis = json.load(f)
            with open("outputs/sector_summary.json", "r") as f:
                sector_summary = json.load(f)
            with open("outputs/forecast_results.json", "r") as f:
                forecast_results = json.load(f)
            return ticker_analysis, sector_summary, forecast_results
        except Exception as e:
            print(f"Error loading analysis data: {e}")
            return {}, [], {}
    
    def _build_prompt(self, ticker, ticker_data, sector_data, forecast_data):
        """Construct a detailed prompt for the LLM"""
        prompt = (
            f"Analyze the following investment case for {ticker} and provide a detailed recommendation:\n\n"
            f"COMPANY FUNDAMENTALS:\n"
            f"- Highest Price: ${ticker_data.get('highest_price', 'N/A'):.2f}\n"
            f"- Lowest Price: ${ticker_data.get('lowest_price', 'N/A'):.2f}\n"
            f"- 2020 Growth: {ticker_data.get('growth_2020_percent', 'N/A'):.2f}%\n"
            f"- Sector: {ticker_data.get('sector', 'N/A')}\n\n"
            
            f"SECTOR PERFORMANCE:\n"
            f"- Average 2020 Growth: {next((s['growth_2020_percent'] for s in sector_data if s['sector'] == ticker_data.get('sector')), 'N/A')}%\n\n"
            
            f"FORECAST RESULTS:\n"
            f"- Actual Price (Jan 2025): ${forecast_data.get('actual_price', 'N/A'):.2f}\n"
            f"- LSTM Forecast: ${forecast_data['LSTM']['forecast']:.2f} (RMSE: {forecast_data['LSTM']['rmse']:.2f})\n"
            f"- MLP Forecast: ${forecast_data['MLP']['forecast']:.2f} (RMSE: {forecast_data['MLP']['rmse']:.2f})\n\n"
            
            "ANALYSIS REQUEST:\n"
            "1. Compare the forecasts against the actual price and sector performance\n"
            "2. Identify any significant discrepancies between model predictions\n"
            "3. Assess the stock's technical indicators and momentum\n"
            "4. Provide a clear Buy/Hold/Sell recommendation with confidence level (Low/Medium/High)\n"
            "5. Suggest an appropriate investment horizon (Short/Medium/Long term)\n"
            "6. Highlight key risks and opportunities\n\n"
            "Structure your response with clear headings and bullet points."
        )
        return prompt
    
    def generate_recommendations(self, tickers=None):
        """Generate recommendations for specified tickers"""
        ticker_analysis, sector_summary, forecast_results = self._load_analysis_data()
        
        if not tickers:
            tickers = list(forecast_results.keys())
            
        recommendations = {}
        
        for ticker in tickers:
            if ticker not in ticker_analysis or ticker not in forecast_results:
                print(f"Skipping {ticker} - missing analysis or forecast data")
                continue
                
            prompt = self._build_prompt(
                ticker,
                ticker_analysis[ticker],
                sector_summary,
                forecast_results[ticker]
            )
            
            try:
                response = self.llm.generate(
                    prompt=prompt,
                    temperature=0.3  # Lower temperature for more conservative recommendations
                )
                recommendations[ticker] = response
            except Exception as e:
                print(f"Error generating recommendation for {ticker}: {e}")
                recommendations[ticker] = "Recommendation generation failed"
        
        # Save recommendations
        os.makedirs("outputs", exist_ok=True)
        with open("outputs/investment_recommendations.json", "w") as f:
            json.dump(recommendations, f, indent=4)
            
        return recommendations
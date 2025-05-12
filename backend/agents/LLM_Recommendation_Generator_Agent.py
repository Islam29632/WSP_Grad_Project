import os
import json
import google.generativeai as genai
from crewai import Agent
from dotenv import load_dotenv

# Load API key from environment
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

class LLMRecommendationAgent(Agent):
    def __init__(self):
        super().__init__(
            role="LLM Financial Advisor",
            goal="Provide Buy/Hold/Sell recommendations using price forecasts and stock analytics",
            backstory=(
                "An expert LLM-powered advisor trained on market analytics and risk-based decision making. "
                "Leverages Google Gemini to synthesize structured data into investor-grade advice."
            ),
            llm=None  # Not used here, since we use genai directly
        )

    def generate_recommendations(self, forecast_data: dict, analysis_data: dict,
                                 user_pov: str = "moderate investor") -> dict:
        output = {}

        for symbol, forecast in forecast_data.items():
            analysis = analysis_data.get(symbol)
            if not analysis:
                output[symbol] = {"error": "Missing analysis data"}
                continue

            # Extract actual price and model forecasts
            actual_price = forecast.get("actual_price", "N/A")
            target_date = forecast.get("target_date", "N/A")

            lstm_data = forecast.get("LSTM", {})
            mlp_data = forecast.get("MLP", {})

            lstm_forecast = lstm_data.get("forecast", "N/A")
            lstm_rmse = lstm_data.get("rmse", "N/A")

            mlp_forecast = mlp_data.get("forecast", "N/A")
            mlp_rmse = mlp_data.get("rmse", "N/A")

            # Pick the best model based on lower RMSE
            try:
                best_model = "LSTM" if lstm_rmse < mlp_rmse else "MLP"
            except:
                best_model = "N/A"

            # Get analysis info
            high = analysis.get("highest_price", "N/A")
            low = analysis.get("lowest_price", "N/A")
            growth = analysis.get("growth_2020_percent", "N/A")
            sector = analysis.get("sector", "N/A")

            # Construct the LLM prompt
            prompt = f"""
            You're a trusted financial advisor helping a cautious investor decide what to do with their {symbol} stock by January 31, 2025.

            Here is the relevant data:
            - Current price: {round(actual_price, 2)}
            - Forecasted range: {round(min(lstm_forecast, mlp_forecast), 2)} to {round(max(lstm_forecast, mlp_forecast), 2)}
            - Historical high: {high}
            - Historical low: {low}
            - Growth during 2020: {growth}%
            - Sector: {sector}

            Instructions:
            - Give a clear, friendly recommendation: **Buy**, **Hold**, or **Sell**.
            - Use simple, confident language a typical investor can understand.
            - Avoid all technical terms (no mention of models, RMSE, or algorithms).
            - Focus on price trends, risk level, and sector behavior.
            - 2 to 4 sentences only.
            """

            # Call Gemini
            try:
                model = genai.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content(prompt)
                llm_text = response.text.strip() if response.text else "No response"
            except Exception as e:
                llm_text = f"Gemini API error: {e}"

            output[symbol] = {
                "recommendation": llm_text,
                "best_model": best_model,
                "actual": actual_price,
                "lstm_forecast": lstm_forecast,
                "mlp_forecast": mlp_forecast
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


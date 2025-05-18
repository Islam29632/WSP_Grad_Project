import json
import os
from crewai import Crew, Task, Agent
from agents.DC_Agent import Collectorgent
from agents.data_processor_agent import DataProcessorAgent
from agents.llm_recommendation_generator_and_rag import LLMRecommendationAgent
def create_crew(tickers):
    collect = Collectorgent()
    process_data = DataProcessorAgent()
    llm = LLMRecommendationAgent()

    task_collect_preprocess = Task(
        name="Collect and Preprocess Data",
        description=f"Collect raw stock data for tickers {tickers} and preprocess it for further analysis.",
        expected_output="Cleaned and structured stock data for given tickers.",
        agent=collect
)

    task_generate_stats = Task(
        name="Generate Sector Statistics",
        description="Generate sector mapping and compute statistical indicators for each stock in the dataset.",
        expected_output="Sector map and key financial statistics for each stock.",
        agent=process_data
)

    task_forecast_prices = Task(
        name="Run Forecast Models",
        description="Use LSTM and MLP models to predict future prices for each stock and select the best-performing model.",
        expected_output="Forecast results including model performance and predicted prices.",
        agent=process_data
)

    task_generate_recommendations = Task(
        name="Generate LLM Recommendations",
        description=(
            f"Generate investment recommendations for {tickers} using analysis data, forecast results, "
            "and RAG-enhanced context for a cautious long-term growth investor."
        ),
        expected_output="A JSON array of recommendation objects. Each object should have 'ticker' (string), 'recommendation' (string), 'reasoning' (string), and 'forecast' (object). The 'forecast' object should have model names (e.g., 'LSTM', 'MLP') as keys and their respective forecast data (object with metrics like 'predicted_price', 'performance') as values.",
        agent=llm
)

# === Crew Assembly ===

    stock_crew = Crew(
        agents=[collect, process_data, llm],
        tasks=[
            task_collect_preprocess,
            task_generate_stats,
            task_forecast_prices,
            task_generate_recommendations
    ],
        verbose=True # Set verbose to True for more output
)
    print("Starting Crew execution...") # Added print statement
    crew_result = stock_crew.kickoff()
    print("Crew execution finished.") # Added print statement

    # Define the output directory and file path
    output_dir = "../backend/outputs"
    output_file = os.path.join(output_dir, "crew_result.json")

    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Save the result to a JSON file
    with open(output_file, "w") as f:
        # Extract JSON string from the CrewOutput string representation
        crew_result_str = str(crew_result)
        json_start = crew_result_str.find("```json") + 7
        json_end = crew_result_str.rfind("```")
        json_content = crew_result_str[json_start:json_end].strip()

        # Load the extracted JSON string into a Python dictionary
        crew_result_dict = json.loads(json_content)

        # Save the dictionary as JSON
        json.dump(crew_result_dict, f, indent=2) # Save the crew result as JSON

    print(f"Crew result saved to {output_file}")

    return crew_result

if __name__ == "__main__":
    # Placeholder tickers for testing
    #tickers = ["AAPL"]
    tickers = ["AMD", "AAPL", "MSFT", "GOOGL"]
    print(f"Running crew for tickers: {tickers}") # Added print statement
    crew_result = create_crew(tickers)
    print("Crew execution result:")
    print(crew_result)

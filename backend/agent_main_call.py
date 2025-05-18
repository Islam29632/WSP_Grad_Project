import json
import os
import pathlib
import sys
from crewai import Crew, Task, Agent

BASE_DIR = pathlib.Path(__file__).resolve().parents[1]
BACKEND_DIR = BASE_DIR / "backend"
sys.path.insert(0, str(BASE_DIR))

from backend.agents.DC_Agent import ResearchAgent
from backend.data_processor_agent import DataProcessorAgent
from backend.llm_recommendation_generator_and_rag import LLMRecommendationAgent
from backend.utils.agent_tools import *

def create_crew(tickers, usr_pov):
    #Objects of the Agents
    research_agent  = ResearchAgent()
    processor_agent = DataProcessorAgent()
    recommendor = LLMRecommendationAgent()

    # Define tasks with context for dependencies
    collect_task = Task(
        description=f"Fetch monthly stock data of all tickers.",
        agent=research_agent,
        expected_output=f"Collect the data out of raw data and retrun in it the speificied output in CSV format"
                    f"Return no code or explanations, just raw data, don't fake data. ",
        output_key="collect_output",
        tools=[collect]
)

    research_task = Task(
        description=f"Fetch monthly stock data of all tickers.",
        agent=research_agent,
        expected_output=f"Collect the data out of raw data and retrun in it the speificied output in CSV format"
                        f"List of dictionary representing preprocessed monthly stock data for. "
                        f"Return no code or explanations, just raw data, don't fake data. ",
        output_key="research_output",
        context = [collect_task],
        tools=[preprocess]
    )
    fetching_task = Task(
        description=f"Fetch monthly stock data of {tickers} Ticker.",
        agent=research_agent,
        expected_output=f"List of dictionary representing preprocessed monthly stock data for {tickers}. Return no code or explanations, just raw data, don't fake data. ",
        output_key="filtering_output",
        tools=[show_ticker]
    )

    process_task = Task(
        description="Generate sector mapping and compute statistical indicators for each stock in the dataset,",
        agent=processor_agent,
        expected_output=f"Sector map and key financial statistics for each stock,"
                        f"Feturn no code or explanations, just raw data, don't fake data.",
        output_key="process_output",
        context=[fetching_task],
       tools=[generate_sector_map, compute_statistics]
    )
    forecast_task = Task(
        description=f"Generate Forecasting for {tickers},",
        agent=processor_agent,
        expected_output=f"Forecasting prices for each give ticker {tickers},"
                        f"Feturn no code or explanations, just raw data, don't fake data.",
        output_key="forecast_output",
        context=[process_task],
        tools=[forecast_prices]
    )
    recommend_task = Task(
        description=
                f"Generate investment recommendations for {tickers} using analysis data, forecast results, "
                "and RAG-enhanced context for a cautious long-term growth investor.",
        agent=recommendor,
        expected_output=
            "A JSON array of recommendation objects. Each object should have 'ticker' (string), 'recommendation' (string), 'reasoning' (string), and 'forecast' (object)."
            "he 'forecast' object should have model names (e.g., 'LSTM', 'MLP') as keys and their respective forecast data (object with metrics like 'predicted_price', 'performance') as values.",

        output_key="final_output",
        context=[forecast_task],
    )

    # === Crew Assembly ===

    crew = Crew(
        agents=[research_agent,processor_agent,recommendor],
        tasks=[collect_task,research_task,fetching_task,
               process_task,forecast_task,
               recommend_task],
        verbose=True
    )

    # Execute the pipeline
    print("Starting Crew execution...") # Added print statement
    final_output = crew.kickoff(inputs={"tickers": tickers, "user_pov": usr_pov})
    print("Crew execution finished.") # Added print statement

    # Define the output directory and file path "../backend/outputs"
    output_dir = "outputs"
    output_file = os.path.join(output_dir, "crew_result.json")

    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Save the result to a JSON file
    with open(output_file, "w") as f:
        # Extract JSON string from the CrewOutput string representation
        crew_result_str = str(final_output)
        json_start = crew_result_str.find("```json") + 7
        json_end = crew_result_str.rfind("```")
        json_content = crew_result_str[json_start:json_end].strip()

        # Load the extracted JSON string into a Python dictionary
        crew_result_dict = json.loads(json_content)

        # Save the dictionary as JSON
        json.dump(crew_result_dict, f, indent=2) # Save the crew result as JSON

    print(f"Crew result saved to {output_file}")

    return process_task.output,forecast_task.output,final_output

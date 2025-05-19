# agent_main_call.py

import json
import os
import pathlib
import sys
import argparse
from typing import List
from crewai import Crew, Task

# Setup path resolution
BASE_DIR = pathlib.Path(__file__).resolve().parents[1]
BACKEND_DIR = BASE_DIR / "backend"
sys.path.insert(0, str(BASE_DIR))

# Import agents and tools
from backend.agents.DC_Agent import ResearchAgent
from backend.agents.data_processor_agent import DataProcessorAgent
from backend.agents.llm_recommendation_generator_and_rag import LLMRecommendationAgent
from backend.utils.agent_tools import (
    collect, preprocess, show_ticker,
    generate_sector_map, compute_statistics,
    forecast_prices
)


def create_crew(tickers: List[str], usr_pov: str) -> Crew:
    research_agent = ResearchAgent()
    processor_agent = DataProcessorAgent()
    recommendor = LLMRecommendationAgent()

    collect_task = Task(
        description="Fetch monthly stock data of all tickers.",
        agent=research_agent,
        expected_output="Collect the data out of raw data and return it in the specified output in CSV format. "
                        "Return no code or explanations, just raw data, don't fake data.",
        output_key="collect_output",
        tools=[collect]
    )

    research_task = Task(
        description="Preprocess monthly stock data.",
        agent=research_agent,
        expected_output="List of dictionaries representing preprocessed monthly stock data. "
                        "Return no code or explanations, just raw data, don't fake data.",
        output_key="research_output",
        context=[collect_task],
        tools=[preprocess]
    )

    fetching_task = Task(
        description=f"Fetch monthly stock data of {tickers}.",
        agent=research_agent,
        expected_output=f"List of dictionaries representing preprocessed monthly stock data for {tickers}. "
                        "Return no code or explanations, just raw data, don't fake data.",
        output_key="filtering_output",
        tools=[show_ticker]
    )

    process_task = Task(
        description="Generate sector mapping and compute statistical indicators.",
        agent=processor_agent,
        expected_output="Sector map and key financial statistics for each stock. "
                        "Return no code or explanations, just raw data, don't fake data.",
        output_key="process_output",
        context=[fetching_task],
        tools=[generate_sector_map, compute_statistics]
    )

    forecast_task = Task(
        description=f"Generate forecasting for {tickers}.",
        agent=processor_agent,
        expected_output=f"Forecasting prices for each given ticker {tickers}. "
                        "Return no code or explanations, just raw data, don't fake data.",
        output_key="forecast_output",
        context=[process_task],
        tools=[forecast_prices]
    )

    recommend_task = Task(
        description=f"Generate investment recommendations for {tickers} using analysis data, forecast results, "
                    "and RAG-enhanced context for a cautious long-term growth investor.",
        agent=recommendor,
        expected_output="A JSON array of recommendation objects. Each object should have 'ticker' (string), "
                        "'recommendation' (string), 'reasoning' (string), and 'forecast' (object). The 'forecast' "
                        "object should have model names (e.g., 'LSTM', 'MLP') as keys and their respective forecast "
                        "data (object with metrics like 'target_date', 'actual_price', 'predicted_price', 'performance') as values.",
        output_key="final_output",
        context=[forecast_task]
    )

    return Crew(
        agents=[research_agent, processor_agent, recommendor],
        tasks=[
            collect_task, research_task, fetching_task,
            process_task, forecast_task, recommend_task
        ],
        verbose=True
    )


def run_crew(tickers: List[str], usr_pov: str):
    print("🚀 Running Crew pipeline...")
    crew = create_crew(tickers, usr_pov)
    result = crew.kickoff(inputs={"tickers": tickers, "user_pov": usr_pov})
    print("✅ Crew execution finished.")

    # Save result
    output_dir = "../backend/outputs"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "crew_result.json")

    try:
        result_str = str(result)
        json_start = result_str.find("```json") + 7
        json_end = result_str.rfind("```")
        json_content = result_str[json_start:json_end].strip()
        result_dict = json.loads(json_content)

        with open(output_file, "w") as f:
            json.dump(result_dict, f, indent=2)

        print(f"📁 Crew result saved to {output_file}")
    except Exception as e:
        print("❌ Failed to save crew result:", str(e))
        with open(output_file, "w") as f:
            f.write(str(result))  # Fallback to raw string

    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbols", type=str, required=True)
    parser.add_argument("--user_pov", type=str, required=True)
    args = parser.parse_args()

    tickers = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    research, analysis, recs = run_crew(tickers, args.user_pov)
    out = {
        "research":        research,
        "analysis":        analysis,
        "recommendations": recs,
    }
    out_path = pathlib.Path("backend/outputs/crew_result.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2))



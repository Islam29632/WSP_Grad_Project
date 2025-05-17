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
        expected_output="Final recommendation JSON with reasoning and forecasts per ticker.",
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
        verbose=False
)
    return stock_crew.kickoff()

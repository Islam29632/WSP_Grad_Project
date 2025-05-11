# main.py
from data_processor_agent import DataProcessorAgent
from DC_Agent import Collectorgent
from LLM_Recommendation_Generator_Agent import LLMRecommendationGenerator

def main():
    # Initialize agents
    collector = Collectorgent()
    processor = DataProcessorAgent()
    recommender = LLMRecommendationGenerator()
    
    # Example tickers to analyze
    tickers = ["AAPL", "MSFT", "GOOGL"]
    
    # Data collection and processing pipeline
    raw_data = collector.collect(tickers)
    processor.generate_sector_map()
    processor.compute_statistics()
    processor.forecast_prices(tickers)
    
    # Generate recommendations
    recommendations = recommender.generate_recommendations(tickers)
    
    print("Recommendations generated successfully!")
    for ticker, rec in recommendations.items():
        print(f"\n===== {ticker} =====")
        print(rec)

if __name__ == "__main__":
    main()
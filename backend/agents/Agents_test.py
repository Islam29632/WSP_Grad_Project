import os
import json
from data_processor_agent import DataProcessorAgent
from DC_Agent import Collectorgent
from llm_recommendation_generator_and_rag import LLMRecommendationAgent

def main():
    # Initialize agents
    collector = Collectorgent()
    processor = DataProcessorAgent()
    
    # Example tickers to analyze
    tickers = ["AAPL", "MSFT", "GOOGL"]
    
    # Data collection and processing pipeline
    print("🔍 Collecting and preprocessing data...")
    raw_data = collector.collect(targets=tickers)
    processed_data = collector.preprocess(raw_data, tickers=tickers)
    print("✅ Data collection and preprocessing complete")
    
    # Data analysis and forecasting
    print("\n📊 Processing sector mapping and statistics...")
    processor.generate_sector_map()
    processor.compute_statistics()
    print("✅ Sector mapping and statistics complete")
    
    print("\n🔮 Running price forecasts...")
    forecast_result = processor.forecast_prices(tickers=tickers)
    print(f"✅ {forecast_result}")
    
    # Initialize recommendation agent with optional RAG file
    rag_file_path = "data/rag/context.txt"  
    recommender = LLMRecommendationAgent(rag_file_path=rag_file_path)
    
    # Generate recommendations
    print("\n💡 Generating recommendations...")
    
    # Load the required data files
    with open("outputs/forecast_results.json") as f1, \
         open("outputs/ticker_analysis.json") as f2:
        forecast_data = json.load(f1)
        analysis_data = json.load(f2)
    
    # Filter data for our target tickers
    filtered_forecast = {k: v for k, v in forecast_data.items() if k in tickers}
    filtered_analysis = {k: v for k, v in analysis_data.items() if k in tickers}
    
    recommendations = recommender.generate_recommendations(
        forecast_data=filtered_forecast,
        analysis_data=filtered_analysis,
        user_pov="I'm a cautious investor seeking long-term growth."
    )
    
    # Save and display results
    output_path = "outputs/final_recommendations.json"
    with open(output_path, "w") as f:
        json.dump(recommendations, f, indent=2)
    
    print("\n🎉 Recommendations generated successfully!")
    print(f"Results saved to {output_path}\n")
    
    for ticker, rec in recommendations.items():
        print(f"===== {ticker} =====")
        print(f"Recommendation: {rec.get('recommendation', 'N/A')}")
        print(f"Current Price: {rec.get('actual', 'N/A')}")
        print(f"LSTM Forecast: {rec.get('lstm_forecast', 'N/A')}")
        print(f"MLP Forecast: {rec.get('mlp_forecast', 'N/A')}")
        print(f"Best Model: {rec.get('best_model', 'N/A')}")
        if rec.get('rag_used'):
            print("(Includes RAG-enhanced insights)")
        print()

if __name__ == "__main__":
    main()

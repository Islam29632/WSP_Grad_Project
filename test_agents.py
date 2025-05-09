import os
from dotenv import load_dotenv
import pandas as pd
from backend.agents.DC_Agent import Collectorgent


def main():
    # Load environment variables
    load_dotenv()

    try:
        # Initialize the Collector Agent
        collector = Collectorgent()
        print("✓ Successfully initialized Collector Agent")
        try:
            all_data = collector.collect(targets=None)
            print("✓ Shape of all data:", all_data.shape)
            print("\nSample of all data:")
            print(all_data.head())

            # Test preprocessing
            print("\n🔧 Testing preprocessing:")
            processed_data = collector.preprocess(all_data.copy())
            print("✓ Shape after preprocessing:", processed_data.shape)
            print("\nSample of processed data:")
            print(processed_data.head())
            
        except Exception as e:
            print("❌ Error collecting/processing all data:", str(e))

    except Exception as e:
        print("❌ Error initializing Collector Agent:", str(e))


if __name__ == "__main__":
    main()
# Importing
from crewai import LLM, Agent
import google.generativeai as genai
import os
from dotenv import load_dotenv
import pandas as pd

# Load environment variables from .env file
# WSP.config give my error so I used dotenv to load the key
# from WSP.config import load_key
# api_key = load_key()

from typing import Optional

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

genai.configure(api_key=api_key)

# Setting the path to the local file work on windows / linux / macOS
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
local_loc = os.path.join(project_root, "backend", "database", "World-Stock-Prices-Dataset.csv")

# Note All the Agents are built almost the same but the configurations only different.
# Creating Class Collectorgent


class Collectorgent(Agent):
    def __init__(self):

        gemini_llm = LLM(model='gemini/gemini-1.5-pro', api_key=api_key)
        # Setting the parametter to be used
        super().__init__(
            role="Stock Data Collector",  # what the agent acts like
            goal="Fetch Companies Stocks",  # mission
            backstory=  # agent characteristics
            "You are a seasoned data engineer and analyst with years of experience in collecting raw data from csv files. "
            "cleaning inconsistencies, handling missing values, and converting it into structured formats."
            "You understand that clean, well-prepared data is the foundation of every successful AI project."
            "You've worked across domains and know how to deal with messy, real-world data using modern tools and best practices."
            "You mastered working with Stocking data and know how to handle them.",
            llm=gemini_llm  # LLM model -> Gemini
        )

    def data_loc(self):
        return local_loc

    def collect(self, targets: Optional[list], col_name="Industry_Tag") -> pd.DataFrame:
        # Initialize 'data' as an empty DataFrame
        data = pd.DataFrame()
        df = pd.read_csv(self.data_loc())
        if targets:
            for target in targets:
                if target in df[col_name].unique():
                    # Concatenate only if target is found in the 'col_name' column
                    data = pd.concat(
                        [data, df[df[col_name] == target]], ignore_index=True)
                else:
                    print(f"Target '{target}' Not Found")
        else:
            # Select specific columns (Note: Correct column selection syntax)
            data = df[['Industry_Tag', 'Date', 'Open',
                       'High', 'Low', 'Close', 'Volume']]

        return data

    # "['Capital Gains'] not found in axis"
    # TODO: preprocess the data
    def preprocess(self, df) -> pd.DataFrame:
        df.drop('Capital Gains', axis=1, inplace=True)
        df.dropna(inplace=True)  # Can be ignored
        df['Date'] = pd.to_datetime(df['Date'], utc=True)
        return df

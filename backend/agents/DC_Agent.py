#Importing
from crewai import Agent
import google.generativeai as genai
import os
from dotenv import load_dotenv
import pandas as pd
from typing import Optional
from crewai.llm import LLM
#Loading the environment variables
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# genai.configure(api_key=api_key)

# project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# local_loc = os.path.join(project_root, "backend", "database", "World-Stock-Prices-Dataset.csv")

#Note All the Agents are built almost the same but the configurations only different.
#Creating Class Collectorgent
class ResearchAgent(Agent):
    def __init__(self):
        gemini_llm = LLM(model="gemini/gemini-2.0-flash", api_key=api_key)
        super().__init__(
            role="Stock Data Fetcher",
            goal="Fetch monthly stock data for multiple companies",
            backstory="Expert in retrieving financial data from APIs.",
            llm=gemini_llm
        )

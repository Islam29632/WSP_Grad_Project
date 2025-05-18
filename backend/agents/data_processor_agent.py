import os
import json
import pandas as pd
from crewai import Agent
from crewai.llm import LLM
from dotenv import load_dotenv
from integration.utils.data_processor import train_and_forecast
from typing import Optional

# Load environment variables from .env
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class DataProcessorAgent(Agent):
    def __init__(self):
        gemini_llm = LLM(model="gemini/gemini-1.5-flash", api_key="AIzaSyDnxKYmz9BXTM3Vb0JmBFLgZmdGfDonlDc")

        super().__init__(
            role="Financial Data Analyst Agent",
            goal="Perform sector classification, compute historical stock performance metrics, and deliver accurate time series forecasts for selected tickers.",
            backstory=(
                "An expert in quantitative finance and machine learning, this agent specializes in processing large-scale financial datasets, "
                "deriving insightful metrics, and generating reliable forecasts using advanced deep learning models. With a strong background "
                "in financial time series modeling and domain-specific knowledge of equity markets, the agent enables data-driven decisions "
                "for investment strategies and market analysis."
            ),
            llm=gemini_llm
        )

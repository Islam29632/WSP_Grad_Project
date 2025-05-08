#Importing
from crewai import LLM,Agent
import google.generativeai as genai
import os
from dotenv import load_dotenv
import pandas as pd
# Load environment variables from .env file
from WSP.config import load_key

api_key = load_key()

genai.configure(api_key=api_key)
#Note All the Agents are built almost the same but the configurations only different.
#Creating Class Collectorgent
class Collectorgent(Agent):
    def __init__(self):

        gemini_llm = LLM(model = 'gemini/gemini-1.5-pro',api_key = api_key)
        #Setting the parametter to be used
        super().__init__(
            role = "Expert in collecting, cleaning, and structuring raw data into a usable DataFrame.", #what the agent acts like
            goal = "Ensure high-quality, well-formatted, and analysis-ready data for downstream tasks.", #mission
            backstory = #agent characteristics
               "You are a seasoned data engineer and analyst with years of experience in collecting raw data from csv files. "
               "cleaning inconsistencies, handling missing values, and converting it into structured formats."
               "You understand that clean, well-prepared data is the foundation of every successful AI project."
               "You've worked across domains and know how to deal with messy, real-world data using modern tools and best practices."
                "You mastered working with Stocking data and know how to handle them."
            ,
            llm = gemini_llm #LLM model -> Gemini
                    )

    def collect(self, data_frame: pd.DataFrame) -> pd.DataFrame:
        #Agent Function -> what will it generate
        prompt = f"""
        You are a data preprocessing expert. Your task is to collect relevant data from the following source: {data_frame}, 
        then clean and structure it into a well-formed tabular dataset (DataFrame).
        Instructions:
            1. Collect raw data from dataframe.
            2. Clean the data: remove duplicates, handle missing/null values, fix data types.
            3. Normalize and encode categorical values by  Label Encoding.
            4. Output the final data as a Pandas DataFrame code block, ready for use in machine learning or analysis.
        Output :
            1. The data processed as a Pandas DataFrame code block, ready for use in machine learning or analysis.
                    """
        #getting the LLM model response
        llm_advice = self.__generate_with_gemini(prompt)
        return llm_advice

    def __generate_with_gemini(self, prompt: str) -> str:
        try:
            #Gemini Configurations
            model = genai.GenerativeModel("gemini-1.5-pro")
            response = model.generate_content(prompt)
            return response.text.strip() if response.text else "No response from Gemini LLM"
        except Exception as e:
            return f"Gemini LLM error: {str(e)}"
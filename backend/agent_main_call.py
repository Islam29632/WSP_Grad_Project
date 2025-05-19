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


def run_crew(tickers: List[str], usr_pov: str):
    return 1




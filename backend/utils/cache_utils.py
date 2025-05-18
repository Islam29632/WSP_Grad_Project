import os
import json

PARAM_CACHE_PATH = "backend/outputs/cached_params.json"

def load_cached_params():
    if os.path.exists(PARAM_CACHE_PATH):
        with open(PARAM_CACHE_PATH, "r") as f:
            return json.load(f)
    else:
        return {}

def save_cached_params(cache):
    os.makedirs(os.path.dirname(PARAM_CACHE_PATH), exist_ok=True)
    with open(PARAM_CACHE_PATH, "w") as f:
        json.dump(cache, f, indent=4)

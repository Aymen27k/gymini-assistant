import os
import requests
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("gymini-search-key")
CX = "d5cf4b299c6f14de3"

def search_web_impl(query: str):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,
        "key": API_KEY,
        "cx": CX,
        "num": 5
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

response = search_web_impl("squat better practices")
print(response)
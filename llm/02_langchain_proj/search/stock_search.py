import meilisearch
import json
import os
from dotenv import load_dotenv
load_dotenv()
search_key = os.getenv("MIELIE_SEARCH_KEY")

client = meilisearch.Client('http://localhost:7700', search_key)

def stock_search(query):
  return client.index('nasdaq').search(query)
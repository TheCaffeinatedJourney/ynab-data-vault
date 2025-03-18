import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Read values from the environment
YNAB_API_KEY = os.getenv("YNAB_API_KEY")
BUDGET_ID = os.getenv("BUDGET_ID")

BASE_URL = "https://api.ynab.com/v1"

# SINCE_DATE is the date of the first transaction to fetch (defaults to 30 days ago if not set)
SINCE_DATE = "2025-01-01"  
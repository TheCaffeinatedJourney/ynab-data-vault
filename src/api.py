import sys
import os
import time
import requests
from datetime import datetime, timedelta

# Import config.py from the project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config

class YnabAPI:
    def __init__(self):
        """Initialize the YNAB API with credentials from config.py."""
        self.api_key = config.YNAB_API_KEY
        self.budget_id = config.BUDGET_ID
        self.base_url = config.BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.request_count = 0  # Track API requests made

        # If SINCE_DATE is empty, default to 30 days ago
        if not config.SINCE_DATE:
            self.since_date = (datetime.today() - timedelta(days=30)).strftime("%Y-%m-%d")
        else:
            self.since_date = config.SINCE_DATE

    def _handle_rate_limit(self, attempt):
        """Handles rate limits using exponential backoff starting at 30 seconds."""
        wait_time = 30 * (2 ** attempt)  # 30s, 60s, 120s, etc.

        """print(f"\nRate limit hit. Retrying in {wait_time} seconds...")"""

        # Show a countdown progress bar
        for remaining in range(wait_time, 0, -1):
            print(f"Rate limit hit. Retrying in {remaining - 1} seconds... ", end="\r", flush=True)
            time.sleep(1)

        print("\nRetrying now...")

    def _make_request(self, endpoint, params=None, max_retries=5):
        """Helper method to make GET requests to the YNAB API with rate limit handling."""
        url = f"{self.base_url}/{endpoint}"
        attempt = 0
        
        while attempt < max_retries:
            try:
                response = requests.get(url, headers=self.headers, params=params)
                self.request_count += 1  # Track requests
                
                # Handle Rate Limit (429)
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    if retry_after:
                        wait_time = int(retry_after)
                    else:
                        wait_time = 30 * (2 ** attempt)  # Default exponential backoff

                    self._handle_rate_limit(attempt)
                    attempt += 1
                    continue

                response.raise_for_status()  # Raise exception for HTTP errors (4xx, 5xx)
                return response.json()
            
            except requests.exceptions.RequestException as e:
                print(f"API request failed (attempt {attempt+1}): {e}")
                self._handle_rate_limit(attempt)
                attempt += 1

        print("Max retries reached. Skipping this request.")
        return None  # Return None if all retries fail

    def get_transactions(self, account_id=None):
        """Fetch all transactions, handling pagination and rate limits."""
        endpoint = f"budgets/{self.budget_id}/transactions"
        params = {"since_date": self.since_date, "account_id": account_id, "page": 1}

        all_transactions = []
        page_count = 1  

        print(f"Fetching transactions since {self.since_date}...")  

        while True:
            response = self._make_request(endpoint, params)
            if response and "data" in response and "transactions" in response["data"]:
                transactions = response["data"]["transactions"]

                if not transactions:  # Stop if no transactions in this page
                    break

                all_transactions.extend(transactions)
                print(f"Fetched {len(all_transactions)} transactions... (Page {page_count})", end="\r", flush=True)

                params["page"] += 1
                page_count += 1
            else:
                break  # Stop if response is None or malformed

        print(f"\nTotal transactions retrieved: {len(all_transactions)}")  
        return all_transactions

    def get_accounts(self):
        """Fetch accounts for the configured budget ID."""
        endpoint = f"budgets/{self.budget_id}/accounts"
        return self._make_request(endpoint)

    def get_categories(self):
        """Fetch all budget categories."""
        endpoint = f"budgets/{self.budget_id}/categories"
        return self._make_request(endpoint)

if __name__ == "__main__":
    ynab = YnabAPI()
    transactions = ynab.get_transactions()

    print(f"\nTotal API Requests Made: {ynab.request_count}")

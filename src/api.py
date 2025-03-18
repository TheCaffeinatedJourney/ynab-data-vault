import sys
import os
import time
import requests
import json
from datetime import datetime, timedelta

# Ensure the script can import config.py from the project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config

class YnabAPI:
    def __init__(self, full_refresh=False):
        """Initialize YNAB API with delta request handling."""
        self.api_key = config.YNAB_API_KEY
        self.budget_id = config.BUDGET_ID
        self.base_url = config.BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.request_count = 0  # Track API requests made
        self.server_knowledge_file = "server_knowledge.txt"
        
        # If SINCE_DATE is empty, default to 30 days ago
        if not config.SINCE_DATE:
            self.since_date = (datetime.today() - timedelta(days=30)).strftime("%Y-%m-%d")
        else:
            self.since_date = config.SINCE_DATE
        
        # Handle full refresh
        if full_refresh:
            print("Performing full refresh... Resetting server knowledge.")
            self.server_knowledge = None
            self.save_server_knowledge(0)
        else:
            self.server_knowledge = self.get_server_knowledge()

    def get_server_knowledge(self):
        """Retrieve the last known server_knowledge value from file."""
        if os.path.exists(self.server_knowledge_file):
            with open(self.server_knowledge_file, "r") as file:
                try:
                    return int(file.read().strip())
                except ValueError:
                    return None  # Reset if invalid
        return None

    def save_server_knowledge(self, knowledge):
        """Save the current server_knowledge value to file."""
        with open(self.server_knowledge_file, "w") as file:
            file.write(str(knowledge))

    def _handle_rate_limit(self, attempt):
        """Handles rate limits with exponential backoff (180s, 540s, 1620s, 4860s), totaling 7200 seconds which is the max rate limit time."""
        wait_time = 180 * (3 ** attempt)  

        for remaining in range(wait_time, 0, -1):
            print(f"Rate limit hit. Retrying in {remaining - 1} seconds... ", end="\r", flush=True)
            time.sleep(1)

        print("\nRetrying now...")

    def _make_request(self, endpoint, params=None, max_retries=4):
        """Helper method to make GET requests with rate limit handling."""
        url = f"{self.base_url}/{endpoint}"
        attempt = 0
        
        while attempt < max_retries:
            try:
                response = requests.get(url, headers=self.headers, params=params)
                self.request_count += 1  # Track API requests
                
                # Handle Rate Limit (429)
                if response.status_code == 429:
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
        return None  

    def get_transactions(self):
        """Fetch transactions using delta requests, saving to file."""
        endpoint = f"budgets/{self.budget_id}/transactions"
        params = {"since_date": config.SINCE_DATE}  # Always include SINCE_DATE

        # Use last known server knowledge if available
        if self.server_knowledge:
            params["last_knowledge_of_server"] = self.server_knowledge

        print(f"Fetching transactions since {config.SINCE_DATE} using delta requests (server_knowledge: {self.server_knowledge})...")

        response = self._make_request(endpoint, params)

        if response and "data" in response and "transactions" in response["data"]:
            transactions = response["data"]["transactions"]
            server_knowledge = response["data"].get("server_knowledge", self.server_knowledge)

            print(f"Retrieved {len(transactions)} transactions.")

            # Save transactions to a file
            self._save_to_file("transactions.json", transactions)

            # Save updated server knowledge
            if server_knowledge:
                self.save_server_knowledge(server_knowledge)
                print(f"Updated server knowledge: {server_knowledge}")

            return transactions
        else:
            print("No new transactions found.")
            return []
    
    def _save_to_file(self, filename, data):
        """Save API response data to a JSON file."""
        with open(filename, "w") as file:
            json.dump(data, file, indent=4)
        print(f"Data saved to {filename}")

if __name__ == "__main__":
    full_refresh = "--full-refresh" in sys.argv  # Allow full refresh via CLI flag
    ynab = YnabAPI(full_refresh=full_refresh)
    
    transactions = ynab.get_transactions()
    
    print(f"\nTotal API Requests Made: {ynab.request_count}")

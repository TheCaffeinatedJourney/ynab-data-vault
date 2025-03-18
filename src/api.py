import sys
import os

# Add the parent directory of 'src/' to sys.path so we can import config.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import config
import requests

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

    def _make_request(self, endpoint):
        """Helper method to make GET requests to the YNAB API."""
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()  # Raise exception for HTTP errors (4xx, 5xx)
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            return None

    def get_accounts(self):
        """Fetch accounts for the configured budget ID."""
        endpoint = f"budgets/{self.budget_id}/accounts"
        data = self._make_request(endpoint)
        return data if data else {}

if __name__ == "__main__":
    ynab = YnabAPI()
    accounts = ynab.get_accounts()
    print(accounts)

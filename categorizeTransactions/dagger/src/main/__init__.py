"""
A generated module for CategorizeTransactions functions

This module retrieves financial transactions from a spreadsheet that have not been categorized, 
uses AI to correctly categorize transactions and write the results back to the same Spreadsheet.

"""

import dagger
from dagger import dag, function, object_type

@object_type
class CategorizeTransactions:
    @function
    def spreadsheet(self) -> str:
        """Reads data from a Google Spreadsheet using the Sheets API and an API key hardcoded"""
        python_script = """
import requests
import json
api_key = '***'
spreadsheet_id = '***'
url = f'https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/Transactions?key={api_key}'
response = requests.get(url)
data = response.json()

if 'values' in data:
    headers = data['values'][0] 
    rows = data['values'][1:] 
    transactions = []
    for row in rows:
        transaction = {headers[i]: row[i] for i in range(len(headers))}
        transactions.append(transaction)

    json_output = json.dumps(transactions, indent=4)
    print(json_output)
else:
    print('No data found.')
        """.strip()
        return (
            dag.container()
            .from_("python:3.9-slim")
            .with_exec([
                "pip", "install", "requests"
            ])
            .with_exec([
                "python", "-c", python_script
            ])
            .stdout()
        )

# 208396907668-6hdmcsjoqmu1f6jju2vu4h9dssc4bqod.apps.googleusercontent.com
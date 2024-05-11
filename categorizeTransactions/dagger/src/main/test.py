"""
A generated module for CategorizeTransactions functions

This module retrieves financial transactions from a spreadsheet that have not been categorized, 
uses AI to correctly categorize transactions and write the results back to the same Spreadsheet.

"""

import json
import dagger
from dagger import dag, function, object_type, Secret
import os
import pymongo

@object_type
class CategorizeTransactions:
    @function
    async def spreadsheet(self, hftoken: Secret, apiKey: Secret, sheet: Secret, database: Secret) -> str:
        """Reads data from a Google Spreadsheet using the Sheets API and an API key hardcoded"""
        connection_string = await database.plaintext()
        python_script = """
import requests
import json
import os

api_key = os.environ.get('API_KEY')
spreadsheet_id = os.environ.get('SPREADSHEET_ID')
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
        process_script = """
import sys
import json
import requests
import os
import time

# Read the input data from the command line argument
input_data = sys.argv[1]

try:
    transactions = json.loads(input_data.replace('\\\\', '\\\\'))
except json.JSONDecodeError as e:
    print(f"Error decoding JSON: {e}")
    sys.exit(1)

hf_api_key = os.environ.get('HUGGING_FACE')
hf_url = 'https://api-inference.huggingface.co/models/facebook/bart-large-mnli'

# Define categories
categories = [
    "Grocery", "Snacks", "Takeouts", "Entertainment", "Transportation",
    "Credit Card Payment", "Shopping", "Personal Care", "Healthcare"
]

max_retries = 5
retry_delay = 10
requests_per_minute = 30  # Define the number of requests per minute allowed
batch_size = 30  # Number of requests to send before pausing
batch_time = 60  # Time in seconds to complete one batch
request_count = 0  # Count the number of requests
start_time = time.time()  # Start timing the batch

# Process each transaction
for transaction in transactions:
    description = transaction['Description']

    payload = {
        "inputs": description,
        "parameters": {"candidate_labels": categories}
    }

    attempts = 0
    while attempts < max_retries:
        hf_response = requests.post(
            hf_url,
            headers={"Authorization": f"Bearer {hf_api_key}"},
            json=payload
        )

        if hf_response.status_code == 429:
            print("Rate limit exceeded, please try again later")
            sys.exit(1)
        
        elif hf_response.status_code != 200:
            print(f"Error from API: {hf_response.text}")
            sys.exit(1)
    
        hf_data = hf_response.json()

        if 'error' in hf_data and 'currently loading' in hf_data['error']:
            estimated_time = hf_data.get('estimated_time', retry_delay)
            time.sleep(estimated_time)  
            attempts += 1
            continue

        # Extract the predicted category
        if 'labels' in hf_data and 'scores' in hf_data:
            predicted_category = hf_data['labels'][0]
            transaction['Category'] = predicted_category
            break
        else:
            print("Unexpected response format")
            sys.exit(1)
    
    request_count += 1  # Increment request count after processing

    if request_count >= batch_size:
        elapsed_time = time.time() - start_time
        if elapsed_time < batch_time:
            sleep_time = batch_time - elapsed_time
            print(f"Pausing for {sleep_time:.2f} seconds to manage API rate limit.")
            time.sleep(sleep_time)
        start_time = time.time()  # Reset start time for the next batch
        request_count = 0  # Reset request count for the next batch

# Return the enriched data
print(json.dumps(transactions, indent=4))
"""
        container = (
            dag.container()
            .from_("python:3.9-slim")
            .with_exec([
                "pip", "install", "requests"
            ])
            .with_secret_variable("API_KEY", apiKey)
            .with_secret_variable("SPREADSHEET_ID", sheet)
            .with_exec([
                "python", "-c", python_script
            ])
        )
        spreadsheet_data = await container.stdout()
        new_transactions = self.filter_existing(spreadsheet_data, connection_string)
        enriched_data = await container.with_secret_variable("HUGGING_FACE", hftoken).with_exec(["python", "-c", process_script, new_transactions]).stdout()
        db = self.authenticate(connection_string)
        return self.write_to_db(enriched_data, db)
    """
        Login to MongoDB
    """
    def authenticate(self, connection_string:str):
        try: 
            client = pymongo.MongoClient(connection_string)
            collection = client.financials
            db = collection.transactions
            db.find_one()
            return db
        except RuntimeError as e: 
            raise RuntimeError("Failed to authenticate with MongoDB") from e
    """
        Write new transactions to MongoDB
    """
    def write_to_db(self, enriched_data: str, db: any):
        parsed_data = json.loads(enriched_data)
        try:
            for transaction in parsed_data:
                print('***', transaction)
                transaction_id = transaction.get('Transaction ID')
                print('Processing transaction:', transaction_id)
                if not transaction:
                    print("Skipping transaction without Transaction ID")
                    continue
                update_document = {"$set": {key: value for key, value in transaction.items() if key}}
                print('Update document:', update_document)
                db.update_one(
                    filter={'Transaction ID': transaction_id}, 
                    update=update_document,
                    upsert=True
                )
        except RuntimeError as e:
            raise RuntimeError("Failed to write to MongoDB") from e
        return enriched_data
    """
    Filter off transactions that are already in the database
    """
    def filter_existing(self, spreadsheet_data: str, connection_string: str):
        db = self.authenticate(connection_string)
        parsed_data = json.loads(spreadsheet_data)
        existing_transactions = [transaction['Transaction ID'] for transaction in db.find({}, {'Transaction ID': 1})]
        filtered_data = [transaction for transaction in parsed_data if transaction['Transaction ID'] not in existing_transactions]   
        return json.dumps(filtered_data)            


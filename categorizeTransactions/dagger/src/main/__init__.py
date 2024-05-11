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
import asyncio

@object_type
class CategorizeTransactions:
    @function
    async def spreadsheet(self, hftoken: Secret, apiKey: Secret, sheet: Secret, database: Secret) -> str:
        """Retrieves transactions from a spreadsheet, processes them, and writes back to MongoDB."""
        connection_string = await database.plaintext()
        transactions = await self.get_spreadsheet_data(apiKey, sheet)
        filtered_transactions = self.filter_existing(transactions, connection_string)
        processed, unprocessed = await self.process_transactions(filtered_transactions, hftoken)

        db = self.authenticate(connection_string)
        self.write_to_db(json.dumps(processed), db)

        while unprocessed:
            additional_processed, unprocessed = await self.process_transactions(json.dumps(unprocessed), hftoken)
            self.write_to_db(json.dumps(additional_processed), db)
            processed.extend(additional_processed)

        return json.dumps(processed, indent=4)

    async def get_spreadsheet_data(self, apiKey: Secret, sheet: Secret):
        """Fetches transaction data from a Google Spreadsheet."""
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
    transactions = [dict(zip(headers, row)) for row in rows]
    print(json.dumps(transactions))
else:
    print('[]')
"""
        container = (
            dag.container()
            .from_("python:3.9-slim")
            .with_exec(["pip", "install", "requests"])
            .with_secret_variable("API_KEY", apiKey)
            .with_secret_variable("SPREADSHEET_ID", sheet)
            .with_exec(["python", "-c", python_script])
        )
        output = await container.stdout()
        return output

    async def process_transactions(self, transactions_data, hftoken):
        """Processes transactions to categorize them using an AI model from Hugging Face."""
        max_retries = 3
        retries = 0
        while retries < max_retries:
            try:
                process_script = """
import sys
import json
import requests
import os

hf_api_key = os.environ.get('HUGGING_FACE')
hf_url = 'https://api-inference.huggingface.co/models/facebook/bart-large-mnli'
categories = ["Grocery", "Snacks", "Takeouts", "Entertainment", "Transportation", "Credit Card Payment", "Shopping", "Personal Care", "Healthcare"]

transactions = json.loads(sys.argv[1])
processed = []
unprocessed = []

for transaction in transactions:
    description = transaction.get('Description', '')
    payload = {"inputs": description, "parameters": {"candidate_labels": categories}}
    response = requests.post(hf_url, headers={"Authorization": f"Bearer {hf_api_key}"}, json=payload)
    if response.ok:
        data = response.json()
        if 'labels' in data and 'scores' in data:
            transaction['Category'] = data['labels'][0]
            processed.append(transaction)
        else:
            unprocessed.append(transaction)
    else:
        unprocessed.append(transaction)

print(json.dumps({'processed': processed, 'unprocessed': unprocessed}))
"""
                container = (
                    dag.container()
                    .from_("python:3.9-slim")
                    .with_exec(["pip", "install", "requests"])
                    .with_secret_variable("HUGGING_FACE", hftoken)
                    .with_exec(["python", "-c", process_script, transactions_data])
                )
                output = await container.stdout()
                results = json.loads(output)
                return results['processed'], results['unprocessed']
            except Exception as e:
                print(f"Error processing transactions: {e}. Retrying...")
                retries += 1
                await asyncio.sleep(5)
        raise RuntimeError("Failed to process transactions after multiple retries")

    def authenticate(self, connection_string):
        """Authenticates with MongoDB and returns a reference to the transactions collection."""
        client = pymongo.MongoClient(connection_string)
        db = client.financials
        return db.transactions

    def write_to_db(self, enriched_data, transactions_collection):
        """Writes processed data back to MongoDB."""
        parsed_data = json.loads(enriched_data)
        try:
            for transaction in parsed_data:
                print('***', transaction)
                transaction_id = transaction.get('Transaction ID')
                if not transaction:
                    print("Skipping transaction without Transaction ID")
                    continue
                update_document = {"$set": {key: value for key, value in transaction.items() if key}}
                print('Update document:', update_document)
                transactions_collection.update_one(
                    filter={'Transaction ID': transaction_id},
                    update=update_document,
                    upsert=True
                )
        except RuntimeError as e:
                raise RuntimeError("Failed to write to MongoDB") from e
        return enriched_data

    def filter_existing(self, transactions_data, connection_string):
        """Filters out transactions that are already in the database."""
        transactions = json.loads(transactions_data)
        db = self.authenticate(connection_string)
        existing_ids = {item['Transaction ID'] for item in db.find({}, {'Transaction ID': 1})}
        filtered_transactions = [trans for trans in transactions if trans.get('Transaction ID') not in existing_ids]
        return json.dumps(filtered_transactions)

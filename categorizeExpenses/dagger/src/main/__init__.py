"""
A generated module for CategorizeExpenses functions

This module has been developed to leverage advanced natural language processing capabilities provided by Hugging Face's transformers library to categorize financial transactions into predefined categories. Utilizing the BART large MNLI model, this module interprets transaction descriptions and intelligently classifies them into categories such as Grocery, Snacks, Entertainment, and more, based on the content of the description.

The BART large MNLI model is a classification model trained on a multi-genre natural language inference corpus. It's designed to understand the context of sentences and predict appropriate labels, making it highly effective for tasks like categorizing unstructured text into specific categories.

Categories used for classification include:
- **Grocery**: Transactions related to food and general supermarket purchases.
- **Snacks**: Small, typically impulsive purchases of food or drinks.
- **Takeouts**: Expenses for food ordered from restaurants for consumption off the premises.
- **Entertainment**: Transactions related to leisure activities.
- **Transportation**: Expenses associated with travel, including fares for buses, trains, taxis, etc.
- **Credit Card Payment**: Payments made towards credit card bills.
- **Shopping**: General shopping expenses, excluding groceries.
- **Personal Care**: Expenses on products or services related to personal hygiene and grooming.
- **Healthcare**: Medical or health-related expenses.

This module includes functions to handle the retrieval and processing of transaction data, employing robust error handling and retry logic to manage API limits and ensure reliable operation.

Functions:
- `process_batch`: Processes a batch of transactions by submitting descriptions to the Hugging Face model and categorizing them based on the model's predictions. This function handles API responses and segregates processed transactions from those that couldn't be categorized due to errors or API limits.

- `categorize`: The main function of the module, orchestrating the retrieval of transaction data, invoking the `process_batch` function, and managing retries in case of failures. It ensures that all transactions are processed, leveraging asynchronous programming to handle potentially large volumes of data efficiently.

- `adjust_batch_size`: Adjusts the batch size dynamically based on response times and API rate limits to optimize throughput.

- `cleanup_api_call_times`: Cleans up the API call times to keep track of calls made within the last minute to manage rate limits effectively.

Args:
- `data (str)`: A JSON string containing an array of transactions, where each transaction includes a description and other relevant details.

- `hftoken (Secret)`: A Secret object that contains the API token for accessing the Hugging Face model.

Return:
- The function returns a JSON string that represents the categorized transactions. Each transaction in this string includes the original details supplemented with a 'Category' field indicating the classification assigned by the model.

Example Call:

`dagger call categorize --data='[{"Description": "Apple purchase at grocery", "Amount": 30}]' --hftoken=env:[KEY]`

Usage of this module can significantly streamline the process of categorizing financial transactions, reducing manual effort and improving the accuracy and consistency of financial record-keeping. It is particularly valuable for applications involving expense management, financial tracking, or any system requiring detailed categorization of transaction data.
"""


from dagger import dag, function, object_type, Secret
import json
import asyncio
import time 

@object_type
class CategorizeExpenses:
    initial_batch_size = 50  
    current_batch_size = initial_batch_size
    api_call_times = []
    response_times = []

    @function
    async def categorize(self, data: str, hftoken: Secret) -> str:
        """Processes transactions using an AI model from Hugging Face with retry logic for API limits."""
        retry_delay = 5  
        processed = []
        unprocessed = json.loads(data)

        while unprocessed:
            batch_size = self.adjust_batch_size()
            batch = unprocessed[:batch_size]
            unprocessed = unprocessed[batch_size:]

            start_time = time.time()
            batch_processed, batch_unprocessed = await self.process_batch(batch, hftoken)
            end_time = time.time()

            self.api_call_times.append(end_time)
            self.response_times.append(end_time - start_time)
            self.cleanup_api_call_times()
 
            processed.extend(batch_processed)
            unprocessed = batch_unprocessed + unprocessed

            if unprocessed:
                print(f"API limit reached or error occurred. {len(unprocessed)} entries remain unprocessed. Retrying after {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)  

        return json.dumps(processed, indent=4)  
    
    def adjust_batch_size(self):
        """Adjust the batch size based on the response times and API rate limits."""
        if len(self.api_call_times) > 1 and (self.api_call_times[-1] - self.api_call_times[0] < 60):
            self.current_batch_size = max(1, self.current_batch_size - 1)
        elif self.response_times and len(self.response_times) >= 5 and sum(self.response_times[-5:]) / 5 < 1:
            self.current_batch_size += 1

        return self.current_batch_size
    
    def cleanup_api_call_times(self):
        """Clean up the API call times to keep track within the last minute."""
        current_time = time.time()
        self.api_call_times = [call_time for call_time in self.api_call_times if current_time - call_time < 60]

    async def process_batch(self, transactions, hftoken):
        """Processes a batch of transactions and categorizes them."""
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
            .with_exec(["python", "-c", process_script, json.dumps(transactions)])
        )
        output = await container.stdout()
        results = json.loads(output)
        return results['processed'], results['unprocessed']

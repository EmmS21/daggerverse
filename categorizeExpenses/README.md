# CategorizeExpenses Module

## Overview

The `CategorizeExpenses` module is designed to leverage the advanced capabilities of natural language processing to categorize financial transactions automatically. Using the BART large MNLI model from Hugging Face, this module interprets the descriptions of financial transactions and categorizes them into predefined categories based on the textual content. This automated process aids in financial analysis, budgeting, and accounting by reducing manual categorization efforts.

### Model Details

- **Model Used**: [BART large MNLI](https://huggingface.co/facebook/bart-large-mnli)
- **Provider**: Hugging Face

### Categories

- **Grocery**
- **Snacks**
- **Takeouts**
- **Entertainment**
- **Transportation**
- **Credit Card Payment**
- **Shopping**
- **Personal Care**
- **Healthcare**

## Prerequisites

Before you use the `CategorizeExpenses` module, ensure you have the following:

- Access to MongoDB.
- An API key for Hugging Face.

## Functions
`categorize`
The main function of the module, orchestrating the retrieval of transaction data, invoking the process_batch function, and managing retries in case of failures. It ensures that all transactions are processed, leveraging asynchronous programming to handle potentially large volumes of data efficiently.

`process_batch`
Processes a batch of transactions by submitting descriptions to the Hugging Face model and categorizing them based on the model's predictions. This function handles API responses and segregates processed transactions from those that couldn't be categorized due to errors or API limits.

`adjust_batch_size` 
Adjusts the batch size dynamically based on response times and API rate limits to optimize throughput.

`cleanup_api_call_times`
 Cleans up the API call times to keep track of calls made within the last minute to manage rate limits effectively.


## Set Environment Varibles
```
export HUGGING_FACE_TOKEN="your_hugging_face_api_token"
```

## Example Call
`dagger call categorize --data='[{"Description": "Dinner at Italian restaurant", "Amount": 120}]' --hftoken=env:HUGGING_FACE_TOKEN`

## Expected Output
```
{
  "Transactions": [
    {
      "Description": "Dinner at Italian restaurant",
      "Amount": 120,
      "Category": "Takeouts"
    }
  ]
}
```
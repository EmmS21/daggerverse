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
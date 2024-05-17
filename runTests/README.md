# Daggerverse Repository

Welcome to the **Daggerverse** repository, a collection of Dagger modules designed and built by **Emmanuel Sibanda**. This repository aims to automate various aspects of financial data processing, analysis, and test generation. Below is a detailed yet concise overview of each module to ensure engineering managers can quickly understand and evaluate the technical capabilities presented here.

## What is Dagger?

Dagger is a programmable tool that allows you to replace your software project's artisanal scripts with a modern API and cross-language scripting engine. It simplifies and automates complex workflows, making development and deployment processes more efficient.

For more detailed documentation, refer to the [Dagger documentation](https://docs.dagger.io/).

## Modules Overview

### 1. CategorizeExpenses

#### Overview
The `CategorizeExpenses` module leverages natural language processing to automatically categorize financial transactions. Using the BART large MNLI model from Hugging Face, it interprets transaction descriptions and assigns them to predefined categories, aiding in financial analysis and budgeting.

#### Model Details
- **Model Used**: [BART large MNLI](https://huggingface.co/facebook/bart-large-mnli)
- **Provider**: Hugging Face

#### Categories
- Grocery
- Snacks
- Takeouts
- Entertainment
- Transportation
- Credit Card Payment
- Shopping
- Personal Care
- Healthcare

#### Prerequisites
- Access to MongoDB
- API key for Hugging Face

#### Set Environment Variables
```bash
export HUGGING_FACE_TOKEN="your_hugging_face_api_token"
```

#### Example Call
```bash
dagger call categorize --data='[{"Description": "Dinner at Italian restaurant", "Amount": 120}]' --hftoken=env:HUGGING_FACE_TOKEN
```

#### Expected Output
```bash
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

### 2. Sveltekit Unit Test Generator with LangChain

#### Description
This module automates the generation of unit tests for Sveltekit projects using LangChain AI capabilities, improving developer productivity.

#### Functionality
- GenerateUnitTests: Utilizes LangChain's ChatOpenAI model to create unit tests based on system messages and human input prompts.

### 3. FetchSpreadsheetData

#### Overview
Automates fetching transaction data from Google Spreadsheets populated by Tiller, converting it into structured JSON for financial analysis and expense management.

#### Functionality
- Securely connects to Google Sheets and retrieves transaction data.
- Parses data into structured JSON.
- Handles errors gracefully.

#### Usage
``` bash
dagger call fetch-data --apiKey=env:[KEY] --sheet=env:[KEY]
```

### 4. FilterForNewTransactions

#### Overview
Filters new transactional data from a given spreadsheet against existing records in MongoDB, isolating transactions not yet recorded.

#### Features
- Filters existing transactions based on unique identifiers.
- Interfaces with MongoDB for authentication and retrieval.
- Handles retries and exceptions.

#### Example Usage
``` bash
dagger call filter --data=[DATA] --connection=env:[KEY] --database=[DBNAME] --collection=[COLLECTIONNAME]
```

### 5. GetAdvice

#### Overview
Provides personalized financial advice using AI, aiding in budget management and financial planning. Integrates LangChain with OpenAI's GPT models to process data and deliver insights.

#### Functions
- **generate:** Provides insights on weekly spending and budget adherence.
- **update_prompt:** Updates initial prompts based on user feedback and regenerates advice.

#### Example Usage
``` bash
dagger call generate --data='{"current_week": {"Groceries": "$150", "Utilities": "$120"}, "previous_weeks": {"Groceries": "$130", "Utilities": "$110"}}' --openai=env:OPENAI_SECRET --connection=env:DB_CONNECTION
```
``` bash
dagger call update_prompt --feedback='I prefer more savings tips.' --data='{"current_week": {"Groceries": "$150", "Utilities": "$120"}, "previous_weeks": {"Groceries": "$130", "Utilities": "$110"}}' --openai=env:OPENAI_SECRET --connection=env:DB_CONNECTION
```

### 6. GetFromMongo

#### Overview
Facilitates advanced data retrieval and aggregation from MongoDB using Atlas Search, providing detailed financial insights by grouping transactions by weeks and categories.

#### Example Usage
``` bash
dagger call get-data --connection=env:MONGO --database=[DBNAME] --collection=[COLLECTIONNAME]
```

### 7. NodeJS Unit Test Runner

#### Overview
Runs unit tests in a containerized environment for NodeJS projects, ensuring consistent test results across different environments.

#### Example Usage
``` bash
dagger call test
```
``` bash
dagger call build-test --src=../../ --repo=emms21/interviewsageai --tag=latest
```

## Dependencies
`dagger`


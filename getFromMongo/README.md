# GetFromMongo Module

## Overview

The `GetFromMongo` module is designed to facilitate advanced data retrieval and aggregation from MongoDB, specifically using MongoDB's Atlas Search capabilities. This module allows for the aggregation of financial transaction data, grouping it by weeks and categories to provide a structured overview of financial trends and behaviors.

This solution is ideal for financial analysts, data scientists, and developers working on financial applications that require detailed and regular analysis of transaction data.

## Features

- **Secure Database Connection**: Utilizes MongoDB's secure connection capabilities to ensure data integrity and security.
- **Advanced Data Aggregation**: Leverages MongoDB's powerful aggregation pipeline to summarize transaction data.
- **Detailed Financial Insights**: Groups transactions by weeks and categories, calculating totals for deep financial analysis.

## Prerequisites

Before you can use the `GetFromMongo` module, ensure you have the following:

- MongoDB Atlas account and database setup with the necessary collections and data.
- Python 3.8+ environment with `pymongo` and `dagger` packages installed.
- Access to a Dagger environment capable of executing the module.

## Setting up Environment Variables
```
export MONGO="your_mongodb_connection_string"`
```

## Example Usage

`dagger call get-data --connection=env:MONGO --database=[DBNAME] --collection=[COLLECTIONNAME]`

## Example Output
"""
{
  "Week: 2021-06-07": {
    "Categories": {
      "Grocery": {
        "Transactions": [
          {"Description": "Apple purchase", "Amount": 30}
        ],
        "Total": 150
      }
    },
    "TotalWeek": 450
  }
}
"""
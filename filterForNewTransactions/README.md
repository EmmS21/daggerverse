# FilterForNewTransactions

This module is designed to interface with MongoDB and filter new transactional data from a given spreadsheet against the existing records in the database. It aims to identify and isolate transactions that have not yet been recorded in the MongoDB collection.

## Features

- Filters out transactions that already exist in the MongoDB database based on their unique identifiers.
- Interfaces with MongoDB to authenticate and retrieve the transaction collection.
- Handles retries and exceptions during the MongoDB connection process.
- Accepts transaction data as a JSON string.
- Returns a JSON string representing the filtered transactions that are new to the database.

## Functions

### `authenticate(connection_string: str, database: str, collection: str)`

This utility function establishes a connection to the specified MongoDB collection using the provided credentials and returns a reference to the collection. It is used internally by the `filter` function and is not directly callable via the CLI.

### `filter(data: str, connection: Secret, database: str, collection: str) -> str`

This is the primary function of the module. It accepts transaction data as a JSON string along with MongoDB connection details, and filters out transactions that are already present in the database.

#### Arguments

- `data (str)`: A JSON string representing an array of transactions. Each transaction should be a dictionary containing at least a 'Transaction ID' key.
- `connection (Secret)`: A Secret object containing the MongoDB connection string. This should have sufficient privileges to access the specified database and collection.
- `database (str)`: The name of the MongoDB database to connect to.
- `collection (str)`: The name of the MongoDB collection within the specified database where transaction records are stored.

#### Return Value

The `filter` function returns a JSON string representing an array of transactions that are new to the database (i.e., their 'Transaction ID's are not found in the existing records).

## Example Usage

`dagger call filter --data=[DATA] --connection=env:[KEY] --database=[DBNAME] --collection=[COLLECTIONNAME]`

Replace `[DATA]` with the JSON string representing the transactions, `[KEY]` with the environment variable containing the MongoDB connection string, `[DBNAME]` with the name of the MongoDB database, and `[COLLECTIONNAME]` with the name of the MongoDB collection.

## Dependencies

- `dagger`
- `json`
- `pymongo`

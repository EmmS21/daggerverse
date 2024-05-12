"""
A generated module for FilterForNewTransactions functions

This module is specifically designed to interface with MongoDB to filter new transactional data from a given spreadsheet against the existing records in the database. It aims to identify and isolate transactions that have not yet been recorded in the MongoDB collection. This functionality is crucial for applications that require up-to-date transactional data without duplicates, such as financial tracking systems, expense management applications, or any system needing reconciliation between reported and recorded transactions.

The module provides functions to authenticate to MongoDB and to filter new transactions based on their unique identifiers. These functions can be called via the dagger CLI or programmatically through one of the supported SDKs.

Functions:
- `authenticate`: This utility function establishes a connection to a specified MongoDB collection using provided credentials and returns a reference to the collection. It is not directly callable via the CLI but is used internally by other functions.
- `filter`: This is the primary function of the module. It accepts transaction data as a JSON string along with MongoDB connection details, and filters out transactions that are already present in the database.

Args:
- `data (str)`: A JSON string representing an array of transactions. Each transaction should be a dictionary containing at least a 'Transaction ID'.
- `connection (Secret)`: A Secret object containing the MongoDB connection string. This should have sufficient privileges to access the specified database and collection.
- `database (str)`: The name of the MongoDB database to connect to.
- `collection (str)`: The name of the MongoDB collection within the specified database where transaction records are stored.

Return:
- The `filter` function returns a JSON string representing an array of transactions that are new to the database (i.e., their 'Transaction ID's are not found in the existing records).

Example Call:
`dagger call filter --data=[DATA] --connection=env:[KEY] --database=[DBNAME] --collection=[COLLECTIONNAME]
"""

from dagger import dag, function, object_type, Secret
import json
import pymongo
from pymongo.errors import AutoReconnect, OperationFailure

@object_type
class FilterForNewTransactions:
    @function
    async def filter(self, data: str, connection: Secret, database: str, collection: str) -> str:
        """Filters out transactions that are already in the database."""
        transactions = json.loads(data)
        connection_string = await connection.plaintext()
        db = self.authenticate(connection_string, database, collection)
        existing_ids = {item.get('Transaction ID') for item in db.find({}, {'Transaction ID': 1}) if 'Transaction ID' in item}
        filtered_transactions = [trans for trans in transactions if trans.get('Transaction ID') not in existing_ids]
        return json.dumps(filtered_transactions)

    def authenticate(self, connection_string: str, database: str, collection: str):
        """Authenticates with MongoDB and returns a reference to the transactions collection."""
        max_retries = 3
        retries = 0
        while retries < max_retries:
            try:
                client = pymongo.MongoClient(connection_string)
                db = client[database]
                return db[collection]
            except AutoReconnect as e:
                retries += 1
                if retries == max_retries:
                    raise OperationFailure(f"Failed to connect to MongoDB after {max_retries} retries: {e}")
            except OperationFailure as e:
                raise OperationFailure(f"Failed to authenticate with MongoDB: {e}")

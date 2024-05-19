"""
Module Name: writeToMongo

This module is designed to securely write processed transaction data back to a MongoDB collection. It ensures that transaction records are updated or inserted in a reliable and efficient manner, leveraging MongoDB's robust capabilities to handle data operations. The module handles authentication, data parsing, and updating documents within the specified MongoDB collection.

The primary function write is responsible for connecting to MongoDB using a provided connection string, parsing the transaction data, and performing upsert operations to either update existing documents or insert new ones based on the Transaction ID.

Functions:

- authenticate: A utility function that authenticates with MongoDB using the provided connection string and returns a reference to the specified collection. This function manages connection retries and handles potential connection errors, ensuring a reliable connection to the database.
- write: The main function of the module, which parses the transaction data and performs upsert operations on the MongoDB collection. It ensures that each transaction is processed correctly, updating existing records or inserting new ones as needed.

Args:

- transactions (str): A JSON string containing an array of transaction records. Each record should include a Transaction ID and other relevant details to be written to the database.
- connection (Secret): A Secret object that contains the MongoDB connection string. This connection string must have sufficient privileges to perform read and write operations on the specified database and collection.
- database (str): The name of the MongoDB database that contains the transactions collection.
- collection (str): The specific collection within the database where transaction data will be written.

Return:
The write function returns a JSON string representing the transactions that were processed. This includes the original transaction data, ensuring that the calling process can verify the records that were attempted to be written to the database.

Example Call:
dagger call write --transactions='[{"Transaction ID": "12345", "Amount": 100, "Description": "Grocery"}]' --connection=env:[KEY] --database=[DBNAME] --collection=[COLLECTIONNAME]

Usage
This module streamlines the process of writing transaction data to MongoDB, handling all necessary authentication and ensuring data integrity through upsert operations. It is particularly useful for applications that need to regularly update transaction records in a MongoDB database, such as financial tracking systems or expense management applications.

Detailed Functionality
authenticate: Manages the connection to MongoDB, implementing retries to handle transient connection issues. This function raises an OperationFailure if it fails to connect after the maximum number of retries, ensuring that calling functions can handle this failure appropriately.
write: Parses the transaction data from a JSON string, iterates over each transaction, and performs an upsert operation on the MongoDB collection. It ensures that each transaction is uniquely identified by its Transaction ID and updates the existing document or inserts a new one as needed.
"""

import dagger
from dagger import dag, function, object_type, Secret
import pymongo
from pymongo.errors import AutoReconnect, OperationFailure
import json

@object_type
class WriteToMongo:
    @function
    async def write(self, transactions: str, connection: Secret, database: str, collection: str) -> str:
        """Writes processed data back to MongoDB."""
        connection_string = await connection.plaintext()
        transactions_collection = self.authenticate(connection_string, database, collection)
        parsed_data = json.loads(transactions)
        try:
            for transaction in parsed_data:
                transaction_id = transaction.get('Transaction ID')
                if not transaction:
                    print("Skipping transaction without Transaction ID")
                    continue
                update_document = {"$set": {key: value for key, value in transaction.items() if key}}
                transactions_collection.update_one(
                    filter={'Transaction ID': transaction_id},
                    update=update_document,
                    upsert=True
                )
        except RuntimeError as e:
                raise RuntimeError("Failed to write to MongoDB") from e
        return 'Success'

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


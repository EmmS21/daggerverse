"""Module Name: StocksToMongo

Overview:
This module writes stocks data from the GetStocks function to a MongoDB document, each stock is written as it's own document

Functionality:
- Fetches stock data for specified sectors.
- Writes processed stock data to MongoDB.

Args:
- connection (Secret): Mongo Connection string
- db (str): Name of the database
- collection (str): Name of the collections
- sectors_of_interest (str): Name of the sectors of interest as a string
- period (str): Period of time to return returns and stock price for

Returns:
- Sucess if data is successfully written

Example Call:
dagger call getStocks --connection=[Secret] --db=[str] --collection=<str> --sectors_of_interest=<str> --period=<str>
"""

import dagger
from dagger import dag, function, object_type, Secret
import pymongo
from pymongo.errors import AutoReconnect, OperationFailure
import json
from datetime import datetime

@object_type
class StocksToMongo:
    @function
    async def getStocks(self, connection: Secret, db: str, collection: str, sectors_of_interest: str, period: str) -> str:
        stocks_data = await dag.get_stocks().stocks(sectors_of_interest, period) 
        return await self.writeStocksToMongo(stocks_data, connection, db, collection)
    
    async def writeStocksToMongo(self, stocks_data: str, connection: Secret, db: str, collection: str) -> str:
        """Writes processed stock data back to MongoDB."""
        connection_string = await connection.plaintext()
        stocks_collection = self.authenticate(connection_string, db, collection)
        parsed_data = json.loads(stocks_data)
        investments = parsed_data.get("investments", [])
        stock_data_last_update = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        try:
            for stock in investments:
                symbol = stock.get('symbol')
                if not symbol:
                    print("Skipping stock without symbol")
                    continue

                update_document = {
                    "$set": {**stock, "stock_data_last_update": stock_data_last_update}
                }

                stocks_collection.update_one(
                    filter={'symbol': symbol},
                    update=update_document,
                    upsert=True
                )
        except RuntimeError as e:
            raise RuntimeError("Failed to write to MongoDB") from e
        return 'Success'

    def authenticate(self, connection_string: str, db: str, collection: str):
        """Authenticates with MongoDB and returns a reference to the stocks collection."""
        max_retries = 3
        retries = 0
        while retries < max_retries:
            try:
                client = pymongo.MongoClient(connection_string)
                db = client[db]
                return db[collection]
            except AutoReconnect as e:
                retries += 1
                if retries == max_retries:
                    raise OperationFailure(f"Failed to connect to MongoDB after {max_retries} retries: {e}")
            except OperationFailure as e:
                raise OperationFailure(f"Failed to authenticate with MongoDB: {e}")




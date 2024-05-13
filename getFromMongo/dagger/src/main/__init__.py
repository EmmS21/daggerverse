"""
A generated module for GetFromMongo functions

This module is tailored for retrieving and aggregating transaction data from MongoDB using Atlas Search, a powerful full-text search engine integrated within MongoDB Atlas. It is designed to enhance financial analysis by grouping transactions by weeks and categories, facilitating a comprehensive overview of financial trends and spending behaviors.

The module leverages MongoDB's aggregation pipeline to dynamically group and summarize transaction data. It then formats this data into a structured JSON response that is easy to interpret and use in financial reporting or analysis applications.

Functions:
- `authenticate`: A utility function to authenticate with MongoDB using provided credentials and obtain a reference to a specific transactions collection. This function is critical for establishing a secure and reliable connection to the database.
- `get_data`: The primary function of this module. It retrieves transaction data, processes it through MongoDB's aggregation pipeline, and returns it grouped by weeks and categories.

Args:
- `connection (Secret)`: A Secret object that stores the MongoDB connection string. This should have sufficient privileges to access and execute aggregation commands on the specified database and collection.
- `database (str)`: The name of the MongoDB database that contains the transactions collection.
- `collection (str)`: The specific collection within the database from which transaction data is retrieved.

Return:
- The `get_data` function outputs a JSON string. This string represents an organized collection of data with transactions grouped by weeks and within each week by categories. Each category contains a list of transactions and the total amount spent in that category for the week, alongside the total spent for the entire week.

Example Call:
`dagger call get-data --connection=env:[KEY] --database=[DBNAME] --collection=[COLLECTIONNAME]`

This module simplifies complex financial data aggregation tasks and presents them in an easily accessible format, making it an invaluable tool for businesses that need to perform regular financial reviews or audits.
"""

from dagger import function, object_type, Secret
import json
import pymongo
from pymongo.errors import AutoReconnect, OperationFailure

@object_type
class GetFromMongo:
    @function
    async def get_data(self, connection: Secret, database: str, collection: str) -> str:
        pipeline = [
            {
                "$group": {
                    "_id": {"Week": "$Week", "Category": "$Category"},
                    "Transactions": {
                        "$push": {
                            "Description": "$Description",
                            "Amount": "$Amount" 
                        }
                    },
                    "Total": {
                        "$sum": "$Amount"
                    }
                }
            },
            {
                "$group": {
                    "_id": "$_id.Week",
                    "Categories": {
                        "$push": {
                            "Category": "$_id.Category",
                            "Transactions": "$Transactions",
                            "Total": "$Total"
                        }
                    },
                    "TotalWeek": {"$sum": "$Total"}
                }
            },
            {
                "$sort": {"_id": -1} 
            }
        ]
        connection_string = await connection.plaintext()
        db = self.authenticate(connection_string, database, collection)
        aggregatedData = list(db.aggregate(pipeline))
        response = {}
        for week_data in aggregatedData:
            week_str = "Week: " + week_data['_id'].strftime("%Y-%m-%d")
            categories = week_data.get("Categories", [])
            total_week = week_data.get("TotalWeek", 0)
            categories_data = {}
            for category_data in categories:
                category = category_data["Category"]
                transactions = category_data["Transactions"]
                total_category = category_data["Total"]
                categories_data[category] = {
                    "Transactions": transactions,
                    "Total": total_category
                }
            response[week_str] = {"Categories": categories_data, "TotalWeek": total_week}
        json_response = json.dumps(response)
        return json_response

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

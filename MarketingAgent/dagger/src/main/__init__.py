"""
MarketingAgent module for generating and storing marketing content

This module provides functionality to generate marketing content using an AI agent
and store the results in a MongoDB database. It includes methods for calling the
marketing agent API, writing data to MongoDB, and handling authentication.

Input required:
- persona: str (marketing persona description)
- business_name: str (name of the business)
- connection: Secret (MongoDB connection string)
- database: str (name of the MongoDB database)

Expected output:
- str: 'Success' if the operation completes successfully, otherwise raises an exception
"""
from dagger import function, object_type, Secret
import requests
import pymongo
from pymongo.errors import AutoReconnect, OperationFailure
import json
from datetime import datetime
from urllib.parse import quote_plus

@object_type
class MarketingAgent:
    @function
    async def run(self, persona: str, business_name: str, connection: Secret, database: str) -> str:
        """Calls marketing agent and writes the response to MongoDB"""
        marketing_data = self.call_marketing_agent(persona, business_name)        
        if "error" in marketing_data:
            raise RuntimeError(f"Error from marketing agent: {marketing_data['error']}")
        marketing_data_json = json.dumps(marketing_data)
        write_result = await self.write(marketing_data_json, connection, database, business_name)
        return write_result
    
    def call_marketing_agent(self, persona: str, business_name: str):
        url = "https://emms21--marketing-agent-agent.modal.run"
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "persona": persona,
            "business_name": business_name
        }
        
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": "Failed to call the endpoint",
                "status_code": response.status_code,
                "response": response.text
            }
                
    async def write(self, data: str, connection: Secret, database: str, company_name: str) -> str:
        """Writes processed data into MongoDB under a collection named after the company."""
        connection_string = await connection.plaintext()
        collection = self.authenticate(connection_string, database, company_name)
        parsed_data = json.loads(data)       
        current_date = datetime.now()
        parsed_data['date_written'] = {
            'year': current_date.year,
            'month': current_date.month,
            'day': current_date.day
        }
                
        try:
            collection.insert_one(parsed_data)
        except (RuntimeError, OperationFailure) as e:
            raise RuntimeError("Failed to write to MongoDB") from e         
        return 'Success'

    def authenticate(self, connection_string: str, database: str, collection_name: str):
            """Authenticates with MongoDB and returns a reference to the collection."""
            max_retries = 3
            retries = 0
            while retries < max_retries:
                try:
                    client = pymongo.MongoClient(connection_string)
                    db = client[database]
                    return db[collection_name]
                except AutoReconnect as e:
                    retries += 1
                    if retries == max_retries:
                        raise OperationFailure(f"Failed to connect to MongoDB after {max_retries} retries: {e}")
                except OperationFailure as e:
                    raise OperationFailure(f"Failed to authenticate with MongoDB: {e}")
                
    def encode_credentials(self, connection_string: str) -> str:
        """Encodes the username and password in the connection string."""
        parts = connection_string.split('@')
        creds, host = parts[0], parts[1]
        username, password = creds.split('//')[1].split(':')
        encoded_username = quote_plus(username)
        encoded_password = quote_plus(password)
        return f"mongodb+srv://{encoded_username}:{encoded_password}@{host}"

# # Example usage
# result = call_marketing_agent("Finance bros turning Software Engineer", "fractaltech")
# print(result)

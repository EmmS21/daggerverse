"""
A generated module for ResearcherContainer functions

This module interacts with an AI Agent hosted in Modal.
It carries out research on a company; what they do and who its users are, grouping them into user personas.

It does this by interacting with a web automation tool to browse the internet. It generates paths the agent should explore.

Exploring these paths returns keywords and adtext. This data is written into a MongoDB collection matching the company's name.

Args: 
business_name (str): Name of the business
personas (str): The user personas
connection (Secret): Mongo connection string
modal_entry_point: web entry point to AI Agent deployed in Modal

Returns:
- Success if data is successfully written to MongoDB

"""
import pymongo
import requests
import json
from datetime import datetime
from urllib.parse import quote_plus
from pymongo.errors import AutoReconnect, OperationFailure
from dagger import function, object_type, Secret

@object_type
class ResearcherContainer:
    @function
    def run(self, business_name: str, personas: str, connection: Secret, modal_entry_point: Secret) -> str:
        """Calls marketing agent with business and persona data, then writes results to MongoDB."""
        try: 
            research_output = self.call_marketing_agent(personas, business_name, modal_entry_point)
            research_json = json.dumps(research_output)
        except RuntimeError as e:
            raise RuntimeError(f"Error from marketing agent: {research_json['error']}, error:{e}")
        return self.write(research_json, connection, "marketing_agent", business_name)

    async def call_marketing_agent(self, persona: str, business_name: str, modal_entry_point: Secret):
        """Sends a POST request to the marketing agent API with persona and business data."""
        modal_url = await modal_entry_point.plaintext()
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "persona": persona,
            "business_name": business_name
        }
        
        response = requests.post(modal_url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": "Failed to call the endpoint",
                "status_code": response.status_code,
                "response": response.text
            }
    
    async def write(self, data: str, connection: Secret, database: str, business_name: str) -> str:
        """Writes processed data into MongoDB under a collection named after the company."""
        connection_string = await connection.plaintext()
        collection = self.authenticate(connection_string, database, business_name)
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
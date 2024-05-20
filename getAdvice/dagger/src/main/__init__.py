"""
GetAdvice Module
This module leverages AI to provide personalized financial advice, aiding users in budget management and financial planning. By integrating LangChain with OpenAI's GPT models, the module processes transactional data and user interactions to deliver actionable insights and recommendations.

Functions:
generate
This function simulates a financial advisor, providing insights on weekly spending, budget adherence, and management of shared expenses. It is designed to run twice a week to offer timely financial advice.

Args:

data (str): A JSON string containing transaction data for the current and previous weeks, including amounts, categories, and other relevant metadata.
openai (Secret): A Secret object storing the OpenAI API key for authentication and access to OpenAI's AI models.
connection (Secret): A Secret object storing the MongoDB connection string for database access.

Returns:

A JSON string with tailored financial advice, generated by comparing current spending against historical data and considering budget limits and shared financial responsibilities.

Example Use Case:

dagger call generate --data='{"current_week": {"Groceries": "$150", "Utilities": "$120"}, "previous_weeks": {"Groceries": "$130", "Utilities": "$110"}}' --openai=env:OPENAI_SECRET --connection=env:DB_CONNECTION


Function - update_prompt:
This function updates the initial prompt based on user feedback and regenerates advice using the updated prompt. It is triggered each time the user provides feedback on the AI-generated advice.

Args:

feedback (str): User feedback on the previous advice, used to refine and improve future recommendations.
data (str): A JSON string containing the same spending data as used in the generate function.
openai (Secret): A Secret object storing the OpenAI API key for authentication and access to OpenAI's AI models.
connection (Secret): A Secret object storing the MongoDB connection string for database access.
Returns:

A JSON string with updated financial advice, incorporating user feedback and adjusting recommendations accordingly.

Example Use Case:

dagger call update_prompt --feedback='I prefer more savings tips.' --data='{"current_week": {"Groceries": "$150", "Utilities": "$120"}, "previous_weeks": {"Groceries": "$130", "Utilities": "$110"}}' --openai=env:OPENAI_SECRET --connection=env:DB_CONNECTION

This command processes the feedback and data, uses the updated prompt to generate new advice, and outputs refined recommendations based on the user’s input.

Technical Details
Both functions interact with MongoDB to manage conversation states and ensure personalized advice that evolves over time. The generate function establishes an initial context, while update_prompt modifies this context based on user feedback, ensuring advice remains relevant and personalized.

The module aims to empower users with AI-driven insights for better financial discipline and smarter spending habits, making it an invaluable tool for personal finance apps, budgeting tools, and financial advisory services.
"""

from dagger import function, object_type, Secret
import json
from langchain.chains import ConversationChain
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.prompts.prompt import PromptTemplate
import pymongo
from pymongo.errors import AutoReconnect, OperationFailure
from pymongo.collection import Collection

@object_type
class GetAdvice:
    @function
    async def generate(self, data: str, openai: Secret, connection: Secret) -> str:
        """
        Uses LangChain with OpenAI to generate financial advice based on the AI's role as a financial advisor.
        This function manages conversation states for insights on weekly spending, budget adherence, and shared expenses management.

        Args:
            data (str): A JSON string containing the spending data.
            openai_secret_key (str): The OpenAI API key.

        Returns:
            Dict[str, Union[str, bool]]: A dictionary containing the generated advice or an error message.
        """
        transaction_data = json.loads(data)
        current_week_key = next(iter(transaction_data))
        previous_weeks_data = {k: v for k, v in transaction_data.items() if k != current_week_key}
        openai_secret_key = await openai.plaintext()
        connection_string = await connection.plaintext()
        db = self.authenticate(connection_string, 'financials', 'memory')
        openai = ChatOpenAI(openai_api_key=openai_secret_key, model_name="gpt-3.5-turbo")
        
        template = """
        You are a financial advisor tasked with providing weekly spending insights, comparing these against historical data, advising on budget adherence for a $500 monthly limit on variable expenses, and considering shared expenses between Emmanuel and Jasmine. Generate advice that is highly personalized and summarized, focusing on cost-effective solutions and concise summaries. The advice should dynamically adapt based on their financial goals and the feedback that you have been given from your history. Keep your advice concise, highly personalized and actionable, ensuring it does not exceed 1000 characters.       
        history: {history}
        Human: {input} 
        """
        prompt_template = PromptTemplate(input_variables=["history", "input"], template=template)
        context = {
            "input": f"Here is this week's spending data: {transaction_data[current_week_key]}, and previous data: {previous_weeks_data}.",
        }

        memory_data = self.get_memory_from_mongodb('JasEmm', db)
        memory = ConversationBufferMemory(memory_key="history", buffer=memory_data)
        memory_variables = memory.load_memory_variables(inputs=context)
        context["history"] = memory_variables.get("history", "")

        conversation = ConversationChain(prompt=prompt_template, llm=openai, memory=memory)
        response = conversation.predict(input=context["input"], history=context["history"])
        memory.save_context(inputs={"input": context["input"]}, outputs={"history": response})

        new_memory_data = [
            {"role": "human", "content": context["input"]},
            {"role": "ai", "content": response}
        ]

        self.save_memory_to_mongodb('JasEmm', context["input"], "current_data", db)
        self.save_memory_to_mongodb('JasEmm', new_memory_data, "conversational", db)

        return json.dumps({'advice': response})
    
    @function
    async def update_prompt(self, feedback: str, data: str, openai: Secret, connection: Secret) -> str:
        """
        Updates the initial prompt based on user feedback, then regenerates advice using the updated prompt.
        
        Args:
            feedback (str): User feedback on the previous advice.
            data (str): A JSON string containing the spending data, same as in the generate function.
            openai (Secret): Secret object storing the OpenAI API key.
        
        Returns:
            str: Updated financial advice.
        """
        transaction_data = json.loads(data)
        current_week_key = next(iter(transaction_data))
        previous_weeks_data = {k: v for k, v in transaction_data.items() if k != current_week_key}
        openai_secret_key = await openai.plaintext()
        connection_string = await connection.plaintext()
        db = self.authenticate(connection_string, 'financials', 'memory')
        openai = ChatOpenAI(openai_api_key=openai_secret_key, model_name="gpt-3.5-turbo")
        
        template = """
            You are a financial advisor. Based on previous advice and user feedback, focus on incorporating the feedback given. Provide updated financial advice. Keep your advice concise, highly personalized and actionable, ensuring it does not exceed 1000 characters.
            {history}
            Human: {input}
        """
        prompt_template = PromptTemplate(input_variables=["input"], template=template)
        memory_data = self.get_memory_from_mongodb('JasEmm', db)
        memory = ConversationBufferMemory(memory_key="history", buffer=memory_data)

        context = {
            "input": f"Here is this week's spending data: {transaction_data[current_week_key]}, and previous data: {previous_weeks_data}. feedback: {feedback}",
        }
        memory_variables = memory.load_memory_variables(inputs=context)
        context["history"] = memory_variables.get("history", "")

        conversation = ConversationChain(prompt=prompt_template, llm=openai, memory=memory)
        try:
            updated_response = conversation.predict(input=context["input"], history=context["history"])
            memory.save_context(inputs={"input": context["input"]}, outputs={"history": updated_response})

            new_memory_data = [
                {"role": "human", "feedback": feedback},
                {"role": "ai", "content": updated_response}
            ]
            self.save_memory_to_mongodb('JasEmm', new_memory_data, "conversational", db)

            return json.dumps({'advice': updated_response})
        except Exception as e:
            return str(e)

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
    
    def save_memory_to_mongodb(self, user_id: str, data: dict, data_type: str, db:Collection) -> None:
        """
        Saves or updates the user input or appends new memory data for a given user in MongoDB.

        Args:
            user_id (str): The ID of the user.
            data (dict): The data to be saved.
            data_type (str): The type of data ('user_input' or 'memory').
            db (Collection): The MongoDB collection.
        """
        if data_type == "current_data":
            db.update_one(
                {"current_data": user_id, "type": data_type},
                {"$set": {"content": data}},
                upsert=True
            )
        elif data_type == "conversational":
            existing_memory = self.get_memory_from_mongodb(user_id, db)["conversational"]
            updated_memory = existing_memory + data
            db.update_one(
                {"user_id": user_id, "type": data_type},
                {"$set": {"content": updated_memory}},
                upsert=True
            )
    
    def get_memory_from_mongodb(self, user_id: str, db: Collection) -> list[dict]:
        """
        Fetches the memory data and user input for a given user from MongoDB.

        Args:
            user_id (str): The ID of the user.
            db (Collection): The MongoDB collection.

        Returns:
            dict: A dictionary containing the user input and memory data.
        """
        current_data = db.find_one({"user_id": user_id, "type": "current_data"})
        conversational = db.find_one({"user_id": user_id, "type": "conversational"})
        return {
            "current_data": current_data.get("content") if current_data else "",
            "conversational": conversational.get("content") if conversational else []
        }
        


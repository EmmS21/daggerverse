"""
A generated module for GetAdvice functions

This module harnesses the power of artificial intelligence to provide tailored financial advice, making it an essential tool for users seeking guidance on budget management and financial planning. Using LangChain coupled with OpenAI's powerful GPT models, this module processes transactional data and user interactions to generate actionable insights and advice.

The integration of LangChain with OpenAI allows the module to maintain conversation states, making it possible to deliver advice that not only reflects current financial data but also adapts based on historical spending patterns and ongoing user feedback. This dynamic approach helps users make informed decisions that align with their financial goals.

Functions:
- `generate`: The primary function of the module, it takes in user transaction data and uses an AI model to generate financial advice. This function is designed to simulate a financial advisor, providing insights into weekly spending, budget adherence, and management of shared expenses.

Args:
- `data (str)`: A JSON string containing detailed transaction data for the current and previous weeks. This data should include amounts, categories, and other relevant transaction metadata.
- `openai (Secret)`: A Secret object that stores the OpenAI API key, which is used to authenticate with the OpenAI service and access its AI models.

Returns:
- The function outputs a JSON string that includes tailored financial advice. This advice is generated based on a comparison of current spending against historical data, with considerations for budget limits and shared financial responsibilities.

Example Use Case:
A user submits transaction data through the Dagger CLI using the following command:
`dagger call generate --data='{"current_week": {"Groceries": "$150", "Utilities": "$120"}, "previous_weeks": {"Groceries": "$130", "Utilities": "$110"}}' --openai=env:OPENAI_SECRET`
The function then processes this data, engages in an AI-driven dialogue to understand context and user preferences, and outputs customized advice on how to better manage expenses.

This module is ideal for applications requiring advanced financial analysis, such as personal finance apps, budgeting tools, and financial advisory services. It empowers users to achieve better financial discipline and smarter spending habits through AI-driven insights and recommendations.
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
        You are a financial advisor tasked with providing weekly spending insights, comparing these against historical data, advising on budget adherence for a $500 monthly limit on variable expenses, and considering shared expenses between Emmanuel and Jasmine. Generate advice that is highly personalized and summarized, focusing on cost-effective solutions and concise summaries. The advice should dynamically adapt based on their financial goals and the feedback they give you.        
        {history}
        Human: {input} 
        """
        prompt_template = PromptTemplate(input_variables=["history", "input"], template=template)
        context = {
            "input": f"Here is this week's spending data: {transaction_data[current_week_key]}, and previous data: {previous_weeks_data}.",
        }
        memory = ConversationBufferMemory(memory_key="history")
        memory_variables = memory.load_memory_variables(inputs=context)
        context["history"] = memory_variables.get("history", "")

        conversation = ConversationChain(prompt=prompt_template, llm=openai, memory=memory)
        response = conversation.predict(input=context["input"], history=context["history"])
        memory.save_context(inputs={"input": context["input"]}, outputs={"history": response})

        advice = response
        self.save_memory_to_mongodb('JasEmm', memory.buffer, db)

        return json.dumps({'advice': advice})
    
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
            You are a financial advisor. Based on previous advice and user feedback, focus on incorporating the feedback given. Provide updated financial advice.
            {history}
            Human: {input}
        """
        prompt_template = PromptTemplate(input_variables=["input"], template=template)
        memory = ConversationBufferMemory(memory_key="history")

        context = {
            "input": f"Here is this week's spending data: {transaction_data[current_week_key]}, and previous data: {previous_weeks_data}. feedback: {feedback}",
        }
        memory_variables = memory.load_memory_variables(inputs=context)
        context["history"] = memory_variables.get("history", "")

        conversation = ConversationChain(prompt=prompt_template, llm=openai, memory=memory)
        try:
            updated_response = conversation.predict(input=context["input"], history=context["history"])
            memory.save_context(inputs={"input": context["input"]}, outputs={"history": updated_response})
            self.save_memory_to_mongodb('JasEmm', memory.buffer, db)
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
    
    def save_memory_to_mongodb(self, user_id: str, memory_data: list[dict], db:Collection) -> None:
        """Saves or updates the memory data for a given user in MongoDB."""
        db.update_one(
            {"user_id": user_id},
            {"$set": {"memory": memory_data}},
            upsert=True
        )
        


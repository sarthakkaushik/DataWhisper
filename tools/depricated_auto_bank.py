import os
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser, JsonOutputToolsParser
from langchain.prompts import PromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field, validator
from langchain_core.output_parsers import JsonOutputParser

from langchain.agents.agent_types import AgentType
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent

from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool, StructuredTool, tool
from pydantic import BaseModel, Field
from typing import List
import pandas as pd
from pydantic.config import ConfigDict

from langchain_openai import OpenAI
from langchain_openai import AzureChatOpenAI
from langchain_openai import AzureOpenAIEmbeddings

from typing import Annotated

from typing_extensions import TypedDict
from langgraph.checkpoint.memory import MemorySaver

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

# from dotenv import load_dotenv
# load_dotenv()

os.environ['OPENAI_API_KEY'] = 'Your API'

aoai_api_key = os.getenv("AZURE_OPENAI_API_KEY") 
aoai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
aoai_api_version = os.getenv("AZURE_OPENAI_API_VERSION")

llm = AzureChatOpenAI(
    model="gpt-4o",
    deployment_name="gpt-4o",
    api_key=aoai_api_key,
    azure_endpoint=aoai_endpoint,
    api_version=aoai_api_version,
)

# llm = ChatOpenAI(temperature=0, model="gpt-4")

# You need to deploy your own embedding model as well as your own chat completion model
# embed_model = AzureOpenAIEmbeddings(
#     model="text-embedding-ada-002",
#     deployment_name="text-embedding-ada-002",
#     api_key=aoai_api_key,
#     azure_endpoint=aoai_endpoint,
#     api_version=aoai_api_version,
# )




# LANGGRAPH
class MainState(TypedDict):

    question:str
    similar_query:str
    Index_similar_query:int
    confidence:float
    
graph_builder = StateGraph(MainState)

class Autoquestion(BaseModel):

    similar_query:str=Field(
        ..., description="Get the Similary query to user from the given list of query")
    Index_similar_query:int=Field(
        ..., description="Index no. of similar question")
    confidence:float =Field(
        ..., description="confidence score between 0 to 1, of how similar the given user query is th existing list of question"
    )

def query_check(state:MainState):
    # aoai_api_key = os.getenv("AZURE_OPENAI_API_KEY") 
    # aoai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    # aoai_api_version = os.getenv("AZURE_OPENAI_API_VERSION")

    

    parser = JsonOutputParser(pydantic_object=Autoquestion)
    # message
    # user_question = "Show me FY 23 vs FY 24 Performance for brnads in India"
    user_question = state['question']
    list_Of_exsiting_question = """
    1. Show me FY 2023 vs FY 2024 Performance for top brand in Russia
    2. show me actual sales, country wise for April 2024 in a table
    3. brazil performance across years for sales in table
    4. Country Russia sales achievement % country Product May 2024
    5. what is the CAGR of Russia sales from fy 2022 to fy2024
    6. what is the CAGR of Russia
    7. show me sales for may 2024 vs le vs budget across countries
    8. Show me list of products where achievement and growth is satisfactory
    9. budget country Fy2025
    10. country sales budget Fy2024
    11. Show me Sales vs Budget vs LE vs PY sales vs sales achievement % vs growth % by country by Brand by Channel for May 2024 in matrix
    12. Show me the sales russia for month and fy year in matrix
    13. show me brand by country and achievement% where achievement % is less than 1 in table for April 2024
    14. Top brand by sales & Budget in Russia for April 2024 in table
    15.Show sales by Brand classification in matrix by country/brand for FY 2024
    16. Inhouse vs external sales for FY 2024 in Table
    17. Show me Sales vs Budget vs LE vs PY sales vs growth % by country by Moleculefor FY 2024 in matrix
    18 .Show me Sales, sequential value,sequential growth by country for Q1 FY 2024 in matrix


    """

    template = """
    Your task is to from the give user query match for most similar question from the exitinging list of given question with confidence interval between 0 to 1.

    FOr Example:
    #Example-1
    User query = Show me FY 2023 vs FY 2024 Performance for top brand in Brazil.
    Similar question= Show me FY 2023 vs FY 2024 Performance for top brand in Russia
    Index_similar_query=1
    Confidence= 0.99
    #Example-2
    User query = Show me FY 2021 vs FY 2022 Performance for top brand in Brazil.
    Similar question= Show me FY 2023 vs FY 2024 Performance for top brand in Russia.
    Index_similar_query=1
    Confidence= 0.95
    #Example-3
    User query = Show me FY 2023 vs FY 2024 Performance for top brand in Russia.
    Similar question= Show me FY 2023 vs FY 2024 Performance for top brand in Russia.
    Index_similar_query=1
    Confidence= 0.99
    #Example-4
    User query = Show me FY 2023 vs FY 2024 Performance for top brand in Brazil.
    Similar question= Show me FY 2023 vs FY 2024 Performance for top brand in Russia.
    Index_similar_query=1
    Confidence= 0.99
    #Example-5
    User query = what is the CAGR of Brazil sales from fy 22 to fy 24
    Similar question= what is the CAGR of Russia sales from fy 2022 to fy2024
    Index_similar_query=5
    Confidence= 0.95

    If you find confidence scroe to be <=0.40 then mark "Similar question"="NONE
    Index_similar_query=0
    Confidence=0

    User Question: {user_question}
    List Of Smilar question: {list_Of_exsiting_question}

    Format Requirement:
    {format_instructions}
                        
    Answer:

    """
    prompt = PromptTemplate(
    template= template,
    input_variables= ["user_question", "list_Of_exsiting_questiont_answer"],
    partial_variables={"format_instructions": parser.get_format_instructions()},
)

    chain = prompt | llm | parser

    answer = chain.invoke({"user_question": user_question ,"list_Of_exsiting_question": list_Of_exsiting_question})
    
    state['similar_query']=answer['similar_query']
    state['Index_similar_query']=answer['Index_similar_query']
    state['confidence']=answer['confidence']

    return state



# def query_check_agent(user_query,thread_id_no):
def query_check_agent(user_query):

    memory = MemorySaver()
    builder = StateGraph(MainState)
    builder.add_node("chatbot",query_check )
    builder.set_entry_point("chatbot")
    builder.add_edge('chatbot', END)
    # graph = builder.compile(checkpointer=memory)
    graph = builder.compile()


    # thread = {"configurable": {"thread_id": str(thread_id_no)}}
    
    # for s in graph.stream({ 'question': user_query,}, thread):
    #     print(s)
    
    # current_state = graph.get_state(thread)
    current_state = graph.invoke({'question': user_query})
    return current_state


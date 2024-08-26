import os
from typing import Any, Annotated, Literal
from typing_extensions import TypedDict
import json
from dotenv import load_dotenv

from langchain_community.utilities import SQLDatabase
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import ToolMessage, AIMessage, AnyMessage
from langchain_core.runnables import RunnableLambda, RunnableWithFallbacks
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_core.pydantic_v1 import BaseModel, Field
from langgraph.prebuilt import ToolNode
from langgraph.graph import END, StateGraph, START
from langgraph.graph.message import add_messages
from langchain_community.agent_toolkits import SQLDatabaseToolkit
# from sql_prompts import query_check_system_prompt, query_gen_system_prompt

load_dotenv()

def initialize_llm():
    """Initialize and return an AzureChatOpenAI instance."""
    return AzureChatOpenAI(
        model="gpt-4o",
        deployment_name="gpt-4o",
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    )

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

class SubmitFinalAnswer(BaseModel):
    """Submit the final answer to the user based on the query results."""
    final_answer: str = Field(..., description="The final answer to the user")

def handle_tool_error(state) -> dict:
    """Handle tool errors and return an error message."""
    error = state.get("error")
    tool_calls = state["messages"][-1].tool_calls
    return {
        "messages": [
            ToolMessage(
                content=f"Error: {repr(error)}\n please fix your mistakes.",
                tool_call_id=tc["id"],
            )
            for tc in tool_calls
        ]
    }

def create_tool_node_with_fallback(tools: list) -> RunnableWithFallbacks[Any, dict]:
    """Create a ToolNode with a fallback to handle errors and surface them to the agent."""
    return ToolNode(tools).with_fallbacks([RunnableLambda(handle_tool_error)], exception_key="error")

@tool
def db_query_tool(query: str) -> str:
    """
    Execute a SQL query against the database and get back the result.
    If the query is not correct, an error message will be returned.
    If an error is returned, rewrite the query, check the query, and try again.
    """
    result = db.run_no_throw(query)
    return result if result else "Error: Query failed. Please rewrite your query and try again."

def first_tool_call(state: State) -> dict[str, list[AIMessage]]:
    return {
        "messages": [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "sql_db_list_tables",
                        "args": {},
                        "id": "tool_abcd123",
                    }
                ],
            )
        ]
    }

def model_check_query(state: State) -> dict[str, list[AIMessage]]:
    """Use this tool to double-check if your query is correct before executing it."""
    return {"messages": [query_check.invoke({"messages": [state["messages"][-1]]})]}

def query_gen_node(state: State):
    message = query_gen.invoke(state)
    tool_messages = []
    if message.tool_calls:
        for tc in message.tool_calls:
            if tc["name"] != "SubmitFinalAnswer":
                tool_messages.append(
                    ToolMessage(
                        content=f"Error: The wrong tool was called: {tc['name']}. Please fix your mistakes. Remember to only call SubmitFinalAnswer to submit the final answer. Generated queries should be outputted WITHOUT a tool call.",
                        tool_call_id=tc["id"],
                    )
                )
    return {"messages": [message] + tool_messages}

def should_continue(state: State) -> Literal[END, "correct_query", "query_gen"]:
    last_message = state["messages"][-1]
    if getattr(last_message, "tool_calls", None):
        return END
    return "query_gen" if last_message.content.startswith("Error:") else "correct_query"

def create_workflow(db_uri):
    global db, query_check, query_gen
    db = SQLDatabase.from_uri(db_uri)
    llm = initialize_llm()
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    tools = toolkit.get_tools()

    workflow = StateGraph(State)

    list_tables_tool = next(tool for tool in tools if tool.name == "sql_db_list_tables")
    get_schema_tool = next(tool for tool in tools if tool.name == "sql_db_schema")

    # query_check_system = query_check_system_prompt
    query_check_system= """You are a SQL expert with a strong attention to detail.
Double check the SQLite query for common mistakes, including:
- Using NOT IN with NULL values
- Using UNION when UNION ALL should have been used
- Using BETWEEN for exclusive ranges
- Data type mismatch in predicates
- Properly quoting identifiers
- Using the correct number of arguments for functions
- Casting to the correct data type
- Using the proper columns for joins

Question Interpretation:
- For certain questions, rephrase or expand the query to ensure comprehensive answers:
    Example1: 
    User: "Show me Sales Performance by country"
    Interpreted as: "Show me actual sales, Budget, LE (Latest Estimate), by country"
    Example 2:
    User:"Show me market share percentage for DRL for Russia for each brand wise"
    Interpreted as: -Filter data on the country = Russia
                    - Group by Product and calculate total DRL Sales and Market Sales
                    - Calculate the market share percentage for each product
                    - Finally map each product with their brand name

If there are any of the above mistakes, rewrite the query. If there are no mistakes, just reproduce the original query.

You will call the appropriate tool to execute the query after running this check."""
    



    
    query_check_prompt = ChatPromptTemplate.from_messages(
        [("system", query_check_system), ("placeholder", "{messages}")]
    )
    query_check = query_check_prompt | llm.bind_tools([db_query_tool], tool_choice="required")

    # query_gen_system = query_gen_system_prompt
    query_gen_system= """You are a SQL expert with a strong attention to detail.

    Given an input question, output a syntactically correct SQLite query to run, then look at the results of the query and return the answer.

    DO NOT call any tool besides SubmitFinalAnswer to submit the final answer.

    When generating the query:

    ENsure Question Interpretation:
            - For certain questions, rephrase or expand the query to ensure comprehensive answers:
                Example1: 
                User: "Show me Sales Performance by country"
                Interpreted as: "Show me actual sales, Budget, LE (Latest Estimate), by country"
                Example 2:
                User:"Show me market share percentage for DRL for Russia for each brand wise"
                Interpreted as: -Filter data on the country = Russia
                                - Group by Product and calculate total DRL Sales and Market Sales
                                - Calculate the market share percentage for each product
                                - Finally map each product with their brand name

    Output the SQL query that answers the input question without a tool call.


    You can order the results by a relevant column to return the most interesting examples in the database.
    Never query for all the columns from a specific table, only ask for the relevant columns given the question.

    If you get an error while executing a query, rewrite the query and try again.

    If you get an empty result set, you should try to rewrite the query to get a non-empty result set. 
    NEVER make stuff up if you don't have enough information to answer the query... just say you don't have enough information.

    If you have enough information to answer the input question, simply invoke the appropriate tool to submit the final answer to the user.

    DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database."""

    query_gen_prompt = ChatPromptTemplate.from_messages(
        [("system", query_gen_system), ("placeholder", "{messages}")]
    )
    query_gen = query_gen_prompt | llm.bind_tools([SubmitFinalAnswer])

    workflow.add_node("first_tool_call", first_tool_call)
    workflow.add_node("list_tables_tool", create_tool_node_with_fallback([list_tables_tool]))
    workflow.add_node("get_schema_tool", create_tool_node_with_fallback([get_schema_tool]))
    workflow.add_node("model_get_schema", lambda state: {"messages": [llm.bind_tools([get_schema_tool]).invoke(state["messages"])]})
    workflow.add_node("query_gen", query_gen_node)
    workflow.add_node("correct_query", model_check_query)
    workflow.add_node("execute_query", create_tool_node_with_fallback([db_query_tool]))

    workflow.add_edge(START, "first_tool_call")
    workflow.add_edge("first_tool_call", "list_tables_tool")
    workflow.add_edge("list_tables_tool", "model_get_schema")
    workflow.add_edge("model_get_schema", "get_schema_tool")
    workflow.add_edge("get_schema_tool", "query_gen")
    workflow.add_conditional_edges("query_gen", should_continue)
    workflow.add_edge("correct_query", "execute_query")
    workflow.add_edge("execute_query", "query_gen")

    return workflow.compile()

def run_sql_agent(db_uri, user_query):
    app = create_workflow(db_uri)
    messages = app.invoke({"messages": [("user", user_query)]})
    json_str = messages["messages"][-1].additional_kwargs["tool_calls"][0]["function"]["arguments"]
    result = json.loads(json_str)["final_answer"]
    return result
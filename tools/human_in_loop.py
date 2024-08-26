import os 
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from IPython.display import Image, display
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser

import pandas as pd
from typing import List

def dataframe_info(dataframes: List[pd.DataFrame]) -> str:
    output = []
    
    for idx, df in enumerate(dataframes, start=1):
        name = f"DataFrame_{idx}"
        df_info = f"{name}:\n"
        df_info += "Schema:\n"
        df_info += str(df.dtypes) + "\n"
        df_info += "Head:\n"
        df_info += df.head().to_string() + "\n"
        df_info += "-"*40 + "\n"
        output.append(df_info)
    
    return "\n".join(output)


################################################# Agent Object Class ###################################################################################### 

class State(TypedDict):
    data_schema: str
    user_query: str
    reframe_needed: bool
    step1_suggestion: str
    h_feedback: str
    last_output : str
    
    
######################################## query_to_table_schema_step_1 #########################################################################################
class q_to_b(BaseModel):
    reframe_needed: bool = Field(description=" True: If the user query does not match or can be computed with information we have in the data schemas , False: If the user query is valid with respect to the data schema")
    suggestions: str = Field(description="One alternative question that user can ask about the data, with respect to their question and schema")


def query_to_table_schema_step_1(state):
    print("---Step 1---")
    
    praser = JsonOutputParser(pydantic_object=q_to_b)
    format_instructions = praser.get_format_instructions()
    db_schema = state["data_schema"]
    user_q = state["user_query"]
    model = ChatOpenAI(temperature=0, model="gpt-4")
    if state["h_feedback"] is None:
        template = """Your task is to analyze whether a user query relates to the data schema that is provided to you 
                      sometimes user might ask queries that may require further explaination from their end , like a metric which is ambiqous or not defined in the schema and sometimes user has enterd a value that does not make any sense 
                      in these cases you need to return True for the output reframe_needed.

                      In cases where the user query is valid w.r.t to the data schema you need to return False in the output reframe_needed 
                      
                      The following is the user query : {user_q}

                      Use the data schema to fullfill your task : 
                      
                      {db_schema}

                      Lastly, give three alternative suggestion question to the user with respect to their query and the data schema in the output suggestions.

                      {format}
                      """
        prompt = PromptTemplate(
            template= template,
            input_variables= ["user_q", "db_schema"],
            partial_variables={"format": format_instructions},)
        
        chain = prompt | model | praser

        answer = chain.invoke({"user_q": user_q ,"db_schema": db_schema})
        state["reframe_needed"] = answer["reframe_needed"]
        state["step1_suggestion"] = answer["suggestions"]
        return state

    else:
        sugg = state["step1_suggestion"]
        f_back = state["h_feedback"] 
        template = """Your task is to analyze the user feedback, with respect to the task where the user needs to reframe their query or accept earlier suggested query to have an output of False to  output reframe_needed

                      In the cases that the converstation of user feedback will result in a query  which is valid w.r.t to the data schema you need to return False in the output reframe_needed.

                      if there are still issue with the user feedback conversation not resulting in any meanigful outcomes with respect to data schema then return True in the output reframe_needed.
                      
                      Use the data schema to fullfill your task : 
                      
                      {db_schema}


                      Conversation:

                      The following was the earlier user query : {user_q}

                      The following was the earlier suggestion made to the user by an earlier chain/AI  : {sugg}

                      The feedback response given by the user after observing his ealrier query and AI suggestion : {f_back}

                      

                      Lastly, give three alternative suggestion question to the user with respect to their query and the data schema in the output suggestions. Even now if the user query is not approriate along with suggested question
                      give the user a reason as to why his query does not relate to the data and if so what steps he can take

                      {format}"""
        
        prompt = PromptTemplate(
            template= template,
            input_variables= ["user_q", "db_schema","sugg","f_back"],
            partial_variables={"format": format_instructions},)
        
        chain = prompt | model | praser

        answer = chain.invoke({"user_q": user_q ,"db_schema": db_schema ,"sugg":sugg, "f_back":f_back})
        state["reframe_needed"] = answer["reframe_needed"]
        state["step1_suggestion"] = answer["suggestions"]
        return state
    

def decider(state):
    if state["reframe_needed"] == True:
        return True
    else:
        return False

################################################ human_feedback ################################################################################################

def human_feedback(state):
    print("---human_feedback---")
    pass

########################################### query_to_table_schema_step_1 ########################################################################################
class output_class(BaseModel):
    user_query: str = Field(description="keep the user_query input as it is and pass it in the output")
    alternative_sugg: str = Field(description="In a list of 3 , give 3 other alternatives questions that the user can ask from the data schema which will be useful for them")


def output(state):
    print("---Step 3---")

    praser = JsonOutputParser(pydantic_object=output_class)
    format_instructions = praser.get_format_instructions()
    db_schema = state["data_schema"]
    user_q = state["user_query"]
    sugg = state["step1_suggestion"]
    model = ChatOpenAI(temperature=0, model="gpt-4")
    
    if state["h_feedback"] is None:
        print("---Step 3 LLM Flow : NO HIL---")

        template = """Your task is to provide in total three other alternative suggestion questions to the user based on their intial query and Data schema.
                    Please return the user query as is without altering it in the output user_query

                    And provide in total three other suggestion questions which will aid the user into analyzing the data better

                    Please use the following information:

                    user_query : {user_q}

                    Use the data schema to fullfill your task : 
                        
                    {db_schema}

                    earlier suggestion given by an earlier chain: {sugg}

                    retain the user_query as is without altering it in any fashion 

                    {format}  
                """
        prompt = PromptTemplate(
                template= template,
                input_variables= ["user_q", "db_schema","sugg"],
                partial_variables={"format": format_instructions},)
            
        chain = prompt | model | praser

        answer = chain.invoke({"user_q": user_q ,"db_schema": db_schema ,"sugg":sugg})
        state["step1_suggestion"] = answer["alternative_sugg"]
        state["last_output"] = state["user_query"]
        return state
    else:
        f_back = state["h_feedback"] 
        print("---Step 3 LLM Flow : HIL---")

        template = """Your task is to provide in total three other alternative suggestion questions to the user based on their intial query and Data schema.
                    Please return the user query as is without altering it in the output user_query

                    And provide in total three other suggestion questions which will aid the user into analyzing the data better

                    Please use the following information:

                    reframed_user query : {f_back}

                    Use the data schema to fullfill your task : 
                        
                    {db_schema}

                    earlier suggestion given by an earlier chain: {sugg}

                    retain the user_query as is without altering it in any fashion 

                    {format}  
                """
        prompt = PromptTemplate(
                template= template,
                input_variables= ["f_back", "db_schema","sugg"],
                partial_variables={"format": format_instructions},)
            
        chain = prompt | model | praser

        answer = chain.invoke({"f_back": f_back ,"db_schema": db_schema ,"sugg":sugg})
        state["step1_suggestion"] = answer["alternative_sugg"]
        state["last_output"] = state["h_feedback"]
        return state

################################################### LANGRAPH Design ###############################################################################################

def nlq_hil_agent(user_query,open_ai_key,dataframes: List[pd.DataFrame],thread_id):
    
    os.environ['OPENAI_API_KEY'] = open_ai_key

    builder = StateGraph(State)
    builder.add_node("query_to_table_schema", query_to_table_schema_step_1)
    builder.add_node("human_feedback", human_feedback)
    builder.add_node("output", output)

    builder.add_edge(START, "query_to_table_schema")
    builder.add_conditional_edges(
        "query_to_table_schema",
        decider,
        {
            # If `tools`, then we call the tool node.
            True: "human_feedback",
            # Otherwise we finish.
            False: "output",
        },
    )
    builder.add_edge("human_feedback", "query_to_table_schema")
    builder.add_edge("output", END)


    memory = MemorySaver()

    # Add
    graph = builder.compile(checkpointer=memory, interrupt_before=["human_feedback"])

    db_schema = dataframe_info(dataframes)

    initial_input = {"user_query": user_query ,"data_schema":db_schema}
    thread = {"configurable": {"thread_id": thread_id}}

    for event in graph.stream(initial_input, thread, stream_mode="values"):
        print(event)
    
    current_state = graph.get_state(thread)

    return current_state,graph
import streamlit as st

from langchain_openai import ChatOpenAI


from langchain.agents.agent_types import AgentType
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain_openai import ChatOpenAI

import os

from langchain_openai import OpenAI
import streamlit as st






def excel_llm_agent(df_list,query,api_key):

    os.environ['OPENAI_API_KEY'] = api_key
    try:
        agent = create_pandas_dataframe_agent(ChatOpenAI(temperature=0, model="gpt-4"),
                                              df_list,agent_type=AgentType.OPENAI_FUNCTIONS,
                                                verbose=True,return_intermediate_steps = True,
                                                  number_of_head_rows = 10,
                                                    handle_parsing_errors=True,
                                                    allow_dangerous_code=True)
        result = agent.invoke(query,include_run_info = True,handle_parsing_errors=True,allow_dangerous_code=True)
        
        
        return result
    except Exception as error:
        # handle the exception
        st.write("An exception occurred:", type(error).__name__, "–", error)
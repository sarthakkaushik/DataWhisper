import streamlit as st

from langchain_openai import ChatOpenAI


from langchain.agents.agent_types import AgentType
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from langchain_experimental.agents.agent_toolkits import create_csv_agent

from langchain_openai import ChatOpenAI

import os

from langchain_openai import OpenAI
from langchain_openai import AzureChatOpenAI
from langchain_openai import AzureOpenAIEmbeddings
from dotenv import load_dotenv
load_dotenv()

def excel_llm_agent(df_list,query):

    def _run():

        # Azure OpenAI settings
            AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_API_KEY")
            AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
            AZURE_DEPLOYMENT = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")

            llm= AzureChatOpenAI(
                    openai_api_key = os.getenv("AZURE_OPENAI_API_KEY"),
                    openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION"),
                    azure_deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"),
                    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT"),
                    temperature = 0,
                    
                )
            embedding_function = AzureOpenAIEmbeddings(
                    openai_api_type = "azure",
                    openai_api_key = os.getenv("AZURE_OPENAI_API_KEY"),
                    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT"),
                    deployment = "text-embedding-ada-002",
                    model = "text-embedding-ada-002"
                )
            try:
                agent = create_pandas_dataframe_agent(
                    llm,
                    df_list,agent_type=AgentType.OPENAI_FUNCTIONS,
                    verbose=True,return_intermediate_steps = True,
                        number_of_head_rows = 10,
                        handle_parsing_errors=True,
                        allow_dangerous_code=True
                        )

      
            result = agent.invoke(query,include_run_info = True,
                              handle_parsing_errors=True,
                              allow_dangerous_code=True,
                              
                            )
            print("*********HELLOW WORLD*****************")
            return result
            except Exception as error:
            # handle the exception
            st.write("An exception occurred:", type(error).__name__, "–", error)
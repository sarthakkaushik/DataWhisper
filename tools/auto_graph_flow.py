import os
import re
import streamlit as st
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field, validator

def autograph_full_output(user_query,agent_answer,api_key):

    os.environ['OPENAI_API_KEY'] = api_key
    model = ChatOpenAI(temperature=0, model="gpt-4")
    template = """
        Your task is to convert CSV-agent's answer into plotly graph object incapsulated into a function which does not take any variable as input, if possible.
        Using Python version 3.9.12, create a script using the dataframe df to graph the following: Ensure that the code that you are crafting in confined within the function create_plotly_figure(),which takes no postional argument.
        Refer to the following example below where it is showcased how an answer of the agent is first determined if it can be graphed. 
        Just return the function create_plotly_figure() dont call the function, and a Boolean variable True or False depending if a graph can be made.
        Always employ various colors to showcase difference in the plot and when approriate also use "hue" to make the graphs more meaningful                

        Example:

        Input 1: user_question: Give me count of emplyment status within the firm
        Input 2: agent_answer: The count of employment status within the firm is as follows:

        Active: 207 employees
        Voluntarily Terminated: 88 employees
        Terminated for Cause: 16 employees 

        Output 1: True
        Output 2: 
        
        def create_plotly_figure():
            import plotly.graph_objects as go
            import pandas as pd
            import numpy as np
            from plotly.subplots import make_subplots
            
            employment_status = np.array(["Active", "Voluntarily Terminated", "Terminated for Cause"])
            counts = np.array([207, 88, 16])

            # Creating a DataFrame
            df = pd.DataFrame({{'EmploymentStatus': employment_status, 'Count': counts}})

            
            fig = go.Figure(data=[go.Bar(x=df['EmploymentStatus'], y=df['Count'])])
            fig.update_layout(title_text="Count of Employment Status",
                            xaxis_title="Employment Status",
                            yaxis_title="Count") 

            
            return fig 
        Note that in output 2 you only have to give the code snipet nothing else
        
        Current Task: Please refer the the pervious examples and commands to produce a desired output

        Input 1: {agent_question}
        Input 2: {agent_answer}

        Answer:
       
        """
    prompt = PromptTemplate(
    template= template,
    input_variables= ["agent_question", "agent_answer"])

    chain = prompt | model 

    answer = chain.invoke({"agent_question": user_query ,"agent_answer": agent_answer})

    return answer


def extract_output_1(message):
    """
    Extracts 'Output 1' from the message and returns True if it is 'True', otherwise returns False.
    """
    # Find the start of 'Output 1'
    start = message.find('Output 1:')
    if start == -1:
        return False

    # Extract the value after 'Output 1:'
    end = message.find('\n', start)
    output_1_value = message[start:end].strip().split(':')[-1].strip()

    # Return True if 'Output 1' is 'True', otherwise return False
    return output_1_value == 'True'

def extract_output_2_code(message):
    """
    Extracts the code from 'Output 2' and returns it as a string.
    """
    # Find the start of 'Output 2'
    start = message.find('Output 2:')
    if start == -1:
        return ""

    # The code starts immediately after 'Output 2:'
    code_start = start + len('Output 2:')
    
    # Find the end of the message or use the remaining text as code
    code_end = message.find('Output', code_start)  # If there's another 'Output' section

    if code_end == -1:
        code_end = len(message)  # Until the end if there's no other 'Output' section

    # Extract and return the code block
    return message[code_start:code_end].strip()

def extract_plotly_function_code(message):
    """
    Extracts the dynamic code within the 'create_plotly_figure' function.
    """
    # Define a regular expression pattern to match the function code
    pattern = r"(def create_plotly_figure\(\):[\s\S]*?return fig)"
    
    # Search for the pattern in the message
    match = re.search(pattern, message)
    
    if match:
        return match.group(0).strip()  # Return the matched function code
    else:
        return "Function not found"
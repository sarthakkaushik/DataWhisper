import os
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate





def get_first_string_of_last_list(data):
    """
    Takes a list of lists and returns the first string object of the last list in the outer list.
    
    Parameters:
    data (list): A list of lists, where each inner list contains string objects.
    
    Returns:
    str: The first string object of the last list in the outer list, or None if the input is invalid.
    """
    len_list = len(data)
    if len_list == 0:
        return data[len_list]
    else:
        return data[len_list - 1]


def explain_agent_worflow_nl(intermideiate_steps,api_key):
    
    os.environ['OPENAI_API_KEY'] = api_key
    model = ChatOpenAI(temperature=0, model="gpt-4")

    # template = """
    #     Your task is to explain in simple and yet compherehnsive tone about the actions taken by an LLM-CSV Agent to the end buisness user 
    #     Please note that the end buisness user is not from a data science or statistics background. So therefore explain the steps taken by 
    #     the agentic workflow in a manner which is easy to absorb.
    #     Dont use words like "dataframe","df","python".

    #     You can give an answer step by step as that would give the end user more clarity about the action taken by the agent.
    #     Given the answer in concise form with only underlying business logic and in pointers only

    #     Last Action of the Agent: {AgentOutput}

    #     Answer:
    #     """
    template = """
        Your task is to explain in simple and yet compherehnsive tone about the actions taken by an LLM-CSV Agent to the end buisness user 
        Please note that the end buisness user is not from a data science or statistics background. So therefore explain the steps taken by 
        the agentic workflow in a manner which is easy to absorb.
        Dont use words like "dataframe","df","python".

        Given the answer in concise form with only underlying business logic that the agent has taken and in pointers only

        Last Action of the Agent: {AgentOutput}

        Answer:
        """
    agent_output = get_first_string_of_last_list(intermideiate_steps)
    prompt = PromptTemplate(
    template= template,
    input_variables= ["AgentOutput"])

    chain = prompt | model 

    answer = chain.invoke({"AgentOutput": agent_output})

    return answer.content
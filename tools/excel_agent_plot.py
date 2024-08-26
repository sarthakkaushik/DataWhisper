import streamlit as st
from langchain_openai import ChatOpenAI
from langchain.agents.agent_types import AgentType
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def create_visualization(df, plot_type, x_column, y_column, color_column=None, title=None):
    """Create a Plotly visualization based on the specified parameters."""
    if plot_type == 'scatter':
        fig = px.scatter(df, x=x_column, y=y_column, color=color_column, title=title)
    elif plot_type == 'line':
        fig = px.line(df, x=x_column, y=y_column, color=color_column, title=title)
    elif plot_type == 'bar':
        fig = px.bar(df, x=x_column, y=y_column, color=color_column, title=title)
    elif plot_type == 'histogram':
        fig = px.histogram(df, x=x_column, title=title)
    elif plot_type == 'box':
        fig = px.box(df, x=x_column, y=y_column, title=title)
    else:
        raise ValueError(f"Unsupported plot type: {plot_type}")
    return fig

def excel_llm_agent(df_list, query, api_key):
    os.environ['OPENAI_API_KEY'] = api_key
    try:
        # Define custom tools for the agent
        tools = [
            {
                "name": "create_visualization",
                "description": "Create a visualization of the data",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "plot_type": {"type": "string", "enum": ["scatter", "line", "bar", "histogram", "box"]},
                        "x_column": {"type": "string"},
                        "y_column": {"type": "string"},
                        "color_column": {"type": "string"},
                        "title": {"type": "string"}
                    },
                    "required": ["plot_type", "x_column"]
                }
            }
        ]

        agent = create_pandas_dataframe_agent(
            ChatOpenAI(temperature=0, model="gpt-4"),
            df_list,
            agent_type=AgentType.OPENAI_FUNCTIONS,
            verbose=True,
            return_intermediate_steps=True,
            number_of_head_rows=10,
            handle_parsing_errors=True,
            allow_dangerous_code=True,
            extra_tools=tools
        )

        result = agent.invoke(
            query,
            include_run_info=True,
            handle_parsing_errors=True,
            allow_dangerous_code=True
        )

        # Check if visualization is requested in the result
        if 'create_visualization' in str(result):
            for step in result['intermediate_steps']:
                if 'create_visualization' in str(step[0]):
                    vis_params = step[0].args
                    fig = create_visualization(df_list[0], **vis_params)  # Assuming the first dataframe for simplicity
                    st.plotly_chart(fig)

        return result
    except Exception as error:
        st.write("An exception occurred:", type(error).__name__, "–", error)


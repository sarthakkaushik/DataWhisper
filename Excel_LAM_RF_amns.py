import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from streamlit_pandas_profiling import st_profile_report
from ydata_profiling import ProfileReport
from tools.excel_agent_old import excel_llm_agent
from tools.auto_graph_flow import autograph_full_output, extract_plotly_function_code
from tools.agent_steps_explain import explain_agent_worflow_nl
from tools.viz_plotly import get_primer, format_question, run_request
from tools.human_in_loop import nlq_hil_agent
# from tools.auto_bank import query_check_agent
from tools.Query_bank import QuestionProcessor, create_few_shot_prompt, format_examples


st.set_page_config(layout="wide")

# Initialize session state variables
if 'chat_memory' not in st.session_state:
  st.session_state.chat_memory = []
if 'agent_steps' not in st.session_state:
  st.session_state.agent_steps = []
if 'thread_count' not in st.session_state:
  st.session_state.thread_count = 0
if 'thread_count_2' not in st.session_state:
  st.session_state.thread_count_2 = 0
if "messages" not in st.session_state:
  st.session_state.messages = []

def update_chat_memory(user_input, agent_output):
  st.session_state.chat_memory.append({'user_input': user_input, 'agent_output': agent_output})
  if len(st.session_state.chat_memory) > 3:
      st.session_state.chat_memory.pop(0)

def get_chat_memory():
  return st.session_state.chat_memory

def main():
  open_ai_api = "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"
  st.title("Data Explorer")

  with st.sidebar:
      st.image("images\PwC.png")
      chat_on = st.toggle("NLQ")
      visualize = st.toggle("Custom Visualization")
      check_bank = st.toggle("Confidence Score from Query Bank")

  uploaded_files = st.file_uploader("Upload CSV files", accept_multiple_files=True)
  
  dataframes = []  
  file_list = []

  if uploaded_files:
      for file in uploaded_files:
          file_list.append(file.name)
          try:
              dataframe = pd.read_csv(file)
          except Exception:
              dataframe = pd.read_csv(file, encoding='latin1')
          dataframes.append(dataframe)

      selected_files = st.multiselect("Select Tables", file_list)
      
      if chat_on:
          human_loop = st.toggle("Human in Loop")
          prompt = st.chat_input("Chat with your Data")

                 
          system_prompt="""
            ## 1. Data Structure
            The dataset contains the following columns. Use this information to interpret queries and construct appropriate responses:

            | Field Name           | Description                                                                                           |
            |----------------------|-------------------------------------------------------------------------------------------------------|
            | Period               | Indicates Sales Month                                                                                 |
            | Return__Filter       | N --> Material is sold and not returned, Y --> Material is sold but returned back due to issues       |
            | Geography            | Domestic --> domestic sales, Export --> Export sales                                                  |
            | Location             | Location area of sales                                                                                      |
            | SALES_GROUP          | SAP field for channel identification, combination of sales group, customer group, and dist. Channel defines channel |
            | CUSTOMER_GROUP       | Customer pricing group, combination of sales group, customer group, and dist. Channel defines channel |
            | DIST_CHNL            | Distribution channel, combination of sales group, customer group, and dist. Channel defines channel   |
            | PG_PRFIX             | Product                                                                                               |
            | Product__            | Product Name               |
            | MATERIAL_DESCRIPTION | Description of the product i.e. thickness/width/length/grade/coating thickness                        |
            | THICKNESS1           | Thickness of the product, UOM - mm                                                                    |
            | GSM                  | Coating thickness of the coated product, UOM - GSM                                                    |
            | Customer__Name__Group| Customer Name                                                                                         |
            | SALES_ORDER_NO       | SAP Sales order no                                                                                    |
            | SALES_ITEM_NO        | SAP Sales order item no                                                                               |
            | BATCH                | Batch                                                                                                 |
            | SO_CRTD_DT           | Sales order creation date                                                                             |
            | Quantity_MT          | Total Quantity in Metric Tonn                                                                              |
            | DELIVERED_NSR__RS    | Delivered sales value (Billing value excluding tax) in Indian Rupees                                                 |
            | NET_NSR__RS          | Net Sales value in Rupees                    |
            | BEN__RS              | Base Equated Net Sales Realisation in Indian Rupees                                                                   |
            | SHIP_TO_REGION       | State/Country where the material is dispatched                                                        |
            | PLANT                | AM/NS facility location from where the material is dispatched                                         |
            | MARKET_SEGMENT       | Industry segment                                                                                     |
            | SALES_PERSON         | Sales person name                                                                                     |

           ## 2. Query Interpretation Guidelines
            - for keyword like "purchasing" means Net sales
            - For return rate - also need to consider Quantity_MT
       


            ## 2. Data Presentation and Insights
            - Present results clearly, using tables or bullet points as appropriate
            - Provide insights after data presentation, prefixed with "Remark:"

            ## 4. General Guidelines
            - Execute scripts multiple times for accuracy
            - Present only final output or analysis
            - Maintain a professional tone
            - Use appropriate units (MT for quantity, ₹ for financial values)
            - Consider industry-specific context (steel industry) when interpreting data and providing insights
            """
            
      
          
          if prompt:
              if human_loop:
                  st.session_state.thread_count += 1
                  thread = st.session_state.thread_count
                  st.session_state.agent_steps.append({"thread": thread})
                  selected_dataframes = [dataframes[file_list.index(file)] for file in selected_files]
                  current_state, graph = nlq_hil_agent(prompt, open_ai_api, selected_dataframes, thread)
                  
                  if current_state[0]["reframe_needed"]:
                      with st.expander("View Further Query Suggestions"):
                          st.write(current_state[0]["step1_suggestion"])
                      st.error("Incorrect Query: Your query does not match with the database schema, please refer to suggestions and rewrite your query")
                      st.stop()
                  else:
                      with st.expander("View Further Query Suggestions"):
                          st.write(current_state[0]["step1_suggestion"])
                      st.session_state.messages.append({"role": "user", "content": current_state[0]["last_output"], "steps": [], "explain": []})
              else:
                  st.session_state.messages.append({"role": "user", "content": prompt, "steps": [], "explain": []})
              
              if st.session_state.get("messages"):
                  for message in st.session_state.messages:
                      with st.chat_message(message["role"]):
                          if message.get("steps"):
                              with st.expander("View Intermediate Steps"):
                                  message["steps"]
                          st.markdown(message["content"])
                          if message.get("explain"):
                              with st.expander("Agent Thought Process"):
                                  st.markdown(message["explain"])

              chat_memory_list = get_chat_memory()
              if chat_memory_list:
                  latest_memory = chat_memory_list[-1]
                  latest_interaction = f"**Latest Interaction:** User: {latest_memory['user_input']} -> Agent: {latest_memory['agent_output']}"
                  previous_interactions = " ".join([f"User: {memory['user_input']} -> Agent: {memory['agent_output']}" for memory in chat_memory_list[:-1]])
              else:
                  latest_interaction = ""
                  previous_interactions = ""
              
              recent_chat = f"(Chat Memory: This is the latest interaction user had with the agent. If relevant, use this information to enhance your output {latest_interaction})"
              final_prompt = recent_chat + prompt + system_prompt
              selected_dataframes = [dataframes[file_list.index(file)] for file in selected_files]
              result = excel_llm_agent(selected_dataframes, final_prompt, open_ai_api)
              
              with st.chat_message("assistant"):
                  with st.expander("View Intermediate Steps"):
                      result["intermediate_steps"]    
                  
                  st.write(result["output"])
                  
                  with st.expander("Agent Thought Process"):
                      try:
                          explain = explain_agent_worflow_nl(result["intermediate_steps"], open_ai_api)  
                          st.write(explain) 
                      except:
                          st.write("")
              st.session_state.messages.append({"role": "assistant", "content": result["output"], "steps": result["intermediate_steps"], "explain": explain})
              
              update_chat_memory(prompt, result["output"])
              
              auto_graph = autograph_full_output(prompt, result["output"], open_ai_api)
              
              try:
                  auto_graph_code = extract_plotly_function_code(auto_graph.content)
                  
                  with st.expander("View Graph Logic"):
                      st.code(auto_graph_code, language="python", line_numbers=False)
                  
                  plot_area = st.empty()
                  local_vars = {}
                  exec(auto_graph_code, globals(), local_vars)
                  create_plotly_figure = local_vars['create_plotly_figure']
                  fig = create_plotly_figure()                                 

                  plot_area.plotly_chart(fig, use_container_width=True)
              except:
                  st.write(" ")



#   if check_bank:
#         st.session_state.thread_count_2 += 1
#         thread = st.session_state.thread_count_2
#         prompt = st.text_area("check question bank?", height=10)
#         # prompt = st.chat_input("Chat with your Data")
#         q_b = query_check_agent(prompt)

#         with st.expander("Question Bank Confidence Metrics"):
#             st.write(f"Similar Question in the Data Base: {q_b['similar_query']}")
#             st.write(f"Question ID: {q_b['Index_similar_query']}")
#             st.write(f"Confidence to Resolve User Query: {q_b['confidence']}")

if __name__ == "__main__":
  main()
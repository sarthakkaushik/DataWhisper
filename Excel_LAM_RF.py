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
from tools.auto_bank import query_check_agent
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

        
          
          system_prompt = """
          1. Code Execution:
          - Never provide code directly to the user.
          - Always execute scripts multiple times to generate accurate and consistent results.
          - Present only the final output or analysis to the user.

          2. Question Interpretation:
            - For certain questions, rephrase or expand the query to ensure comprehensive answers:
                Example1: 
                User: Show me Sales Performance by country
                Interpreted as: Show me actual sales, Budget, LE (Latest Estimate), by country
                Example 2:
                User:Show me market share percentage for DRL for Russia for each brand wise
                Interpreted as: -Filter data on the country = Russia
                                - Group by Product and calculate total DRL Sales and Market Sales
                                - Calculate the market share percentage for each product
                                - Finally map each product with their brand name

          3. Data Presentation:
          - Present results in a clear, organized manner.
          - Use tables, bullet points, or other formatting as appropriate to enhance readability.

          4. Insights:
          - After presenting the data, provide valuable insights when possible.
          - Begin each insight with the keyword "Remark:"
          - Focus on trends, anomalies, or noteworthy patterns in the data.

          Remember to maintain a professional and helpful tone throughout the interaction.
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



  if check_bank:
        st.session_state.thread_count_2 += 1
        thread = st.session_state.thread_count_2
        prompt = st.text_area("check question bank?", height=10)
        # prompt = st.chat_input("Chat with your Data")
        q_b = query_check_agent(prompt)

        with st.expander("Question Bank Confidence Metrics"):
            st.write(f"Similar Question in the Data Base: {q_b['similar_query']}")
            st.write(f"Question ID: {q_b['Index_similar_query']}")
            st.write(f"Confidence to Resolve User Query: {q_b['confidence']}")

if __name__ == "__main__":
  main()
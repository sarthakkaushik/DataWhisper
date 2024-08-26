import streamlit as st
import time
from tools.sql_agent import run_sql_agent  # Import the run_sql_agent function from your refactored code

# Streamlit app configuration
st.set_page_config(page_title="SQL Agent", page_icon="🤖", layout="wide")

# Custom CSS for better styling
st.markdown("""
    <style>
    .stApp {
        max-width: 800px;
        margin: 0 auto;
    }
    .step-container {
        display: flex;
        justify-content: space-between;
        margin-bottom: 20px;
    }
    .step {
        flex: 1;
        text-align: center;
        padding: 10px;
        border: 1px solid #ddd;
        border-radius: 5px;
        margin: 0 5px;
    }
    .active {
        background-color: #f0f2f6;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# App title and description
st.title("🤖 SQL Agent Assistant")
st.markdown("Ask questions about your database, and let the AI agent find the answers for you!")

# Input for database URI
db_uri = st.text_input("Enter your database URI:", value="sqlite:///your_database.db")

# Input for user query
user_query = st.text_area("Enter your question:", height=100)

# Function to simulate agent progress
def simulate_agent_progress():
    steps = [
        "Analyzing Query",
        "Fetching Schema",
        "Generating SQL",
        "Executing Query",
        "Preparing Answer"
    ]
    progress_bar = st.progress(0)
    status_text = st.empty()
    step_containers = st.container()

    with step_containers:
        step_cols = st.columns(len(steps))
        step_elements = [col.empty() for col in step_cols]

    for i, step in enumerate(steps):
        # Update progress bar
        progress_bar.progress((i + 1) / len(steps))
        
        # Update status text
        status_text.text(f"Step {i + 1}/{len(steps)}: {step}")
        
        # Update step indicators
        for j, element in enumerate(step_elements):
            if j == i:
                element.markdown(f"<div class='step active'>{steps[j]}</div>", unsafe_allow_html=True)
            else:
                element.markdown(f"<div class='step'>{steps[j]}</div>", unsafe_allow_html=True)
        
        # Simulate processing time
        time.sleep(1)

    # Clear progress indicators
    progress_bar.empty()
    status_text.empty()

# Run button
if st.button("Run Query"):
    if db_uri and user_query:
        with st.spinner("Agent is working on your query..."):
            # Simulate agent progress
            simulate_agent_progress()
            
            # Run the actual SQL agent
            try:
                result = run_sql_agent(db_uri, user_query)
                st.success("Query processed successfully!")
                st.subheader("Result:")
                st.write(result)
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
    else:
        st.warning("Please enter both the database URI and your question.")



# Add a section for query history
st.subheader("Query History")
if 'query_history' not in st.session_state:
    st.session_state.query_history = []

for i, (past_query, past_result) in enumerate(st.session_state.query_history):
    with st.expander(f"Query {i+1}: {past_query[:50]}..."):
        st.write("Question:", past_query)
        st.write("Answer:", past_result)

# Footer
st.markdown("---")
st.markdown("Built by Pwc India")
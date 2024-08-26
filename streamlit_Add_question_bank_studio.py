import streamlit as st
import json
from streamlit_ace import st_ace
import pandas as pd
from io import StringIO

# Function to load the question bank
def load_question_bank():
    try:
        with open('./test_nootebooks/question_bank.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return []

# Function to save the question bank
def save_question_bank(question_bank):
    with open('./test_nootebooks/question_bank.json', 'w') as file:
        json.dump(question_bank, file, indent=4)

# Function to parse multiple questions
def parse_multiple_questions(text):
    df = pd.read_csv(StringIO(text), sep='|', header=None, names=['Question', 'Described Steps'])
    return df.to_dict('records')

# Function to parse CSV file
def parse_csv_file(file):
    df = pd.read_csv(file)
    if 'Question' not in df.columns or 'Described Steps' not in df.columns:
        st.error("CSV file must contain 'Question' and 'Described Steps' columns.")
        return None
    return df[['Question', 'Described Steps']].to_dict('records')

# Main function to run the Streamlit app
def main():
    st.set_page_config(page_title="Question Bank Manager", layout="wide")

    # Custom CSS
    st.markdown("""
    <style>
    .main {
        background-color: #f0f2f6;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
    }
    .stTextInput>div>div>input {
        background-color: #ffffff;
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("🗂️ Question Bank Manager")

    # Load the question bank
    question_bank = load_question_bank()

    # Sidebar
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Add Single Question", "Add Multiple Questions", "Upload CSV", "View Questions"])

    if page == "Add Single Question":
        st.header("Add New Question")

        # Input fields
        new_id = len(question_bank) + 1
        new_question = st.text_input("Question:")
        
        st.subheader("Described Steps")
        new_steps = st_ace(
            placeholder="Enter the described steps here...",
            language="markdown",
            theme="github",
            keybinding="vscode",
            min_lines=10,
            max_lines=20
        )

        if st.button("Add Question"):
            if new_question and new_steps:
                new_entry = {
                    "Id": new_id,
                    "Question": new_question,
                    "Described Steps": new_steps
                }
                question_bank.append(new_entry)
                save_question_bank(question_bank)
                st.success("Question added successfully!")
            else:
                st.warning("Please fill in both the question and described steps.")

    elif page == "Add Multiple Questions":
        st.header("Add Multiple Questions")
        
        st.markdown("""
        Enter multiple questions in the following format:
        ```
        Question 1 | Described Steps 1
        Question 2 | Described Steps 2
        ...
        ```
        """)
        
        multiple_questions = st_ace(
            placeholder="Enter multiple questions here...",
            language="text",
            theme="github",
            keybinding="vscode",
            min_lines=10,
            max_lines=20
        )
        
        if st.button("Add Multiple Questions"):
            if multiple_questions:
                new_entries = parse_multiple_questions(multiple_questions)
                start_id = len(question_bank) + 1
                for i, entry in enumerate(new_entries):
                    entry['Id'] = start_id + i
                    question_bank.append(entry)
                save_question_bank(question_bank)
                st.success(f"{len(new_entries)} questions added successfully!")
            else:
                st.warning("Please enter questions in the specified format.")

    elif page == "Upload CSV":
        st.header("Upload Question Bank CSV")
        
        st.markdown("""
        Upload a CSV file containing questions and described steps.
        The CSV should have two columns: 'Question' and 'Described Steps'.
        """)
        
        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
        
        if uploaded_file is not None:
            new_entries = parse_csv_file(uploaded_file)
            if new_entries:
                if st.button("Add Questions from CSV"):
                    start_id = len(question_bank) + 1
                    for i, entry in enumerate(new_entries):
                        entry['Id'] = start_id + i
                        question_bank.append(entry)
                    save_question_bank(question_bank)
                    st.success(f"{len(new_entries)} questions added successfully from CSV!")

    elif page == "View Questions":
        st.header("View Questions")

        for entry in question_bank:
            with st.expander(f"Question {entry['Id']}: {entry['Question']}"):
                st.write("**Described Steps:**")
                st.markdown(entry['Described Steps'])
                st.markdown("---")

if __name__ == "__main__":
    main()
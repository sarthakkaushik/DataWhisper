import streamlit as st
import pandas as pd
import os
from db_operations import create_table, insert_data

def main():
    st.title("Database Connectors")

    option = st.radio(
        "Choose an option:",
        ("Upload CSV files", "Connect to existing database")
    )

    if option == "Upload CSV files":
        upload_csv_files()
    else:
        connect_to_existing_db()

def upload_csv_files():
    st.header("Upload CSV Files")
    
    uploaded_files = st.file_uploader("Choose CSV files", type="csv", accept_multiple_files=True)

    if uploaded_files:
        for uploaded_file in uploaded_files:
            # Read the CSV file
            df = pd.read_csv(uploaded_file)

            # Get the filename without extension to use as table name
            table_name = os.path.splitext(uploaded_file.name)[0]

            # Display the dataframe
            st.write(f"Preview of the uploaded data for {uploaded_file.name}:")
            st.dataframe(df.head())

            # Create the table
            create_table(table_name, df.columns)

            # Insert the data
            insert_data(table_name, df)

            st.success(f"Data from {uploaded_file.name} successfully saved to the database in table '{table_name}'!")

def connect_to_existing_db():
    st.header("Connect to Existing Database")

    db_type = st.selectbox("Database Type", ["MySQL", "PostgreSQL", "SQLite", "SQL Server", "Oracle"])
    
    if db_type != "SQLite":
        host = st.text_input("Host", "localhost")
        port = st.text_input("Port", "3306")
        database = st.text_input("Database Name", "my_database")
        username = st.text_input("Username", "user")
        password = st.text_input("Password", type="password")
    else:
        db_path = st.text_input("SQLite Database Path", "/path/to/your/database.db")

    table_name = st.text_input("Enter the table name:", "my_table")

    if st.button("Connect and View Data"):
        st.success("This is a placeholder success message. In a real application, this would connect to the database and display data.")
        
        # Placeholder for data display
        st.write("Sample Data Preview:")
        df = pd.DataFrame({
            'Column1': [1, 2, 3, 4, 5],
            'Column2': ['A', 'B', 'C', 'D', 'E']
        })
        st.dataframe(df)

if __name__ == "__main__":
    main()
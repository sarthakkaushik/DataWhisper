import streamlit as st
import pandas as pd
import os
from db_operations import create_table, insert_data

def main():
  st.title("Multiple CSV File Uploader and Database Storage")

  # File uploader for multiple files
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

if __name__ == "__main__":
  main()
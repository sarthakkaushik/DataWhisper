import sqlite3
import pandas as pd
import re
import os

def create_connection(db_name):
    # Define the directory where the database will be stored
    db_directory = 'Database'
    
    # Create the directory if it doesn't exist
    os.makedirs(db_directory, exist_ok=True)
    
    # Construct the full path for the database
    db_path = os.path.join(db_directory, db_name)
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    return conn

def sanitize_table_name(table_name):
    # Remove any characters that are not alphanumeric or underscore
    return re.sub(r'\W+', '', table_name)

def create_table(table_name, columns, db_name):
    conn = create_connection(db_name)
    cursor = conn.cursor()

    # Sanitize the table name
    safe_table_name = sanitize_table_name(table_name)

    # Create a string of column names and types
    columns_str = ", ".join([f'"{col}" TEXT' for col in columns])

    # Create the table
    cursor.execute(f'CREATE TABLE IF NOT EXISTS "{safe_table_name}" ({columns_str})')

    conn.commit()
    conn.close()

def insert_data(table_name, df, db_name):
    conn = create_connection(db_name)

    # Sanitize the table name
    safe_table_name = sanitize_table_name(table_name)

    # Insert the dataframe into the table
    df.to_sql(safe_table_name, conn, if_exists='replace', index=False)

    conn.close()

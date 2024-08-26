import sqlite3
import pandas as pd
import re

DATABASE_NAME = "csv_data.db"

def create_connection():
  conn = sqlite3.connect(DATABASE_NAME)
  return conn

def sanitize_table_name(table_name):
  # Remove any characters that are not alphanumeric or underscore
  return re.sub(r'\W+', '', table_name)

def create_table(table_name, columns):
  conn = create_connection()
  cursor = conn.cursor()

  # Sanitize the table name
  safe_table_name = sanitize_table_name(table_name)

  # Create a string of column names and types
  columns_str = ", ".join([f'"{col}" TEXT' for col in columns])

  # Create the table
  cursor.execute(f'CREATE TABLE IF NOT EXISTS "{safe_table_name}" ({columns_str})')

  conn.commit()
  conn.close()

def insert_data(table_name, df):
  conn = create_connection()

  # Sanitize the table name
  safe_table_name = sanitize_table_name(table_name)

  # Insert the dataframe into the table
  df.to_sql(safe_table_name, conn, if_exists='replace', index=False)

  conn.close()
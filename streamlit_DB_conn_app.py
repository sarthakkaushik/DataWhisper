import streamlit as st
import pandas as pd
import os
import sqlite3
from tools.db_operations import create_table, insert_data, create_connection

# Set page configuration
st.set_page_config(page_title="DB Connector Pro", page_icon="🗃️", layout="wide")

# Custom CSS to improve the look and feel
st.markdown("""
<style>
    .reportview-container {
        background: #f0f2f6
    }
    .main {
        background-color: #ffffff;
        padding: 2rem;
        border-radius: 0.5rem;
        box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15) !important;
    }
    .stRadio > div {
        flex-direction: row;
        align-items: center;
    }
    .stRadio label {
        background-color: #f8f9fa;
        padding: 0.5rem 1rem;
        border-radius: 0.25rem;
        margin-right: 0.5rem;
        cursor: pointer;
    }
    .stRadio label:hover {
        background-color: #e9ecef;
    }
    .stButton>button {
        background-color: #4e73df;
        color: #ffffff;
    }
    .stButton>button:hover {
        background-color: #2e59d9;
    }
    h1 {
        color: #5a5c69 !important;
    }
    h2 {
        color: #5a5c69 !important;
        margin-top: 2rem !important;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.title("🗃️ DB Connector Pro")

    st.sidebar.header("Navigation")
    option = st.sidebar.radio(
        "Choose an option:",
        ("📤 Upload CSV files", "👁️ View Database Tables", "🔗 Connect to existing database")
    )

    if "📤 Upload CSV files" in option:
        upload_csv_files()
    elif "👁️ View Database Tables" in option:
        view_database_tables()
    else:
        connect_to_existing_db()

def upload_csv_files():
    st.header("📤 Upload CSV Files")
    
    col1, col2 = st.columns(2)
    with col1:
        db_name = st.text_input("Enter the database name (without .db extension):", "my_database")
        db_name = f"{db_name}.db"
    
    with col2:
        uploaded_files = st.file_uploader("Choose CSV files", type="csv", accept_multiple_files=True)

    if uploaded_files:
        for uploaded_file in uploaded_files:
            df = pd.read_csv(uploaded_file)
            table_name = os.path.splitext(uploaded_file.name)[0]
            
            st.subheader(f"Preview: {uploaded_file.name}")
            st.dataframe(df.head())

            create_table(table_name, df.columns, db_name)
            insert_data(table_name, df, db_name)

            st.success(f"✅ Data from {uploaded_file.name} successfully saved to table '{table_name}'!")
      
    db_path = os.path.join('Database', db_name)
    db_uri = f"sqlite:///{os.path.abspath(db_path)}"
    st.info(f"🔗 Database URI for future connections: {db_uri}")

def get_database_list():
    db_folder = 'Database'
    if not os.path.exists(db_folder):
        return []
    return [f for f in os.listdir(db_folder) if f.endswith('.db')]

def view_database_tables():
    st.header("👁️ View Database Tables")
    
    databases = get_database_list()
    
    if not databases:
        st.warning("⚠️ No databases found in the 'Database' folder. Please upload CSV files first.")
        return
    
    col1, col2 = st.columns(2)
    with col1:
        selected_db = st.selectbox("Select a database:", databases)
    
    db_path = os.path.join('Database', selected_db)
    
    if os.path.exists(db_path):
        conn = create_connection(selected_db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if tables:
            with col2:
                selected_table = st.selectbox("Select a table to view:", [table[0] for table in tables])
            
            if selected_table:
                df = pd.read_sql_query(f"SELECT * FROM {selected_table}", conn)
                
                st.subheader(f"📊 Preview: '{selected_table}' table")
                st.dataframe(df)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Rows", len(df))
                with col2:
                    st.metric("Columns", len(df.columns))
                with col3:
                    st.metric("Data Types", len(df.dtypes.unique()))
                
                st.subheader("📋 Column Details")
                for col in df.columns:
                    st.write(f"**{col}**: {df[col].dtype}")
        else:
            st.warning("⚠️ No tables found in the selected database.")
        
        conn.close()
    else:
        st.error(f"❌ Database '{db_path}' not found. Please check if it exists.")

def connect_to_existing_db():
    st.header("🔗 Connect to Existing Database")

    db_type = st.selectbox("Database Type", ["MySQL", "PostgreSQL", "SQLite", "SQL Server", "Oracle"])
    
    col1, col2 = st.columns(2)
    
    if db_type != "SQLite":
        with col1:
            host = st.text_input("Host", "localhost")
            database = st.text_input("Database Name", "my_database")
        with col2:
            port = st.text_input("Port", "3306")
            username = st.text_input("Username", "user")
        password = st.text_input("Password", type="password")
    else:
        db_path = st.text_input("SQLite Database Path", "Database/my_database.db")

    table_name = st.text_input("Enter the table name:", "my_table")

    if st.button("Connect and View Data"):
        st.success("🎉 Connection successful! (This is a placeholder message)")
        
        st.subheader("📊 Sample Data Preview")
        df = pd.DataFrame({
            'Column1': [1, 2, 3, 4, 5],
            'Column2': ['A', 'B', 'C', 'D', 'E']
        })
        st.dataframe(df)

if __name__ == "__main__":
    main()
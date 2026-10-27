import urllib
import pandas as pd
from sqlalchemy import create_engine, text, literal_column
import streamlit as st

def cnx():
    server = st.secrets['server'] 
    username = st.secrets['username'] 
    password = st.secrets['password']
    database = 'solubility_training'  
    encoded_password = urllib.parse.quote_plus(password)
    connection_url = f"postgresql+psycopg2://{username}:{encoded_password}@{server}:5432/{database}?sslmode=require"
    return connection_url
#=:smiles_val;
def fetch_data(column: str, SMILES: str,  table: str) -> pd.DataFrame:    
    url = cnx()
    try:
        engine = create_engine(url)
        cleaned_smiles = str(SMILES).replace('\r', '').replace('\n', '').strip()
        query_str = f'SELECT * FROM {table} WHERE TRIM("{column}") = :smiles_val'
        query = text(query_str)
        print (query)
        with engine.connect() as connection:
            print("Successfully connected to Azure postgreSQL SQL Server via SQLAlchemy!")
            print (SMILES)
            result = connection.execute(query, {"smiles_val": cleaned_smiles})
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
            if df.empty:
                return None
            else:
                return df
            
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return pd.DataFrame()

def push_data (data: pd.DataFrame, table: str):
    url = cnx()
    try:
        engine = create_engine(url)  

        with engine.connect() as connection:
            print("Successfully connected to Azure postgreSQL SQL Server via SQLAlchemy!")
            data.to_sql(
                name=table.lower(),      # Kept lowercase for Postgres case-insensitivity
                con=connection, 
                if_exists='append',      # Protects your COLLATE "C" configuration
                index=False,
                schema='public',         # Postgres default schema
                method='multi',          
                chunksize=1      
            )
            connection.comit()
                
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return e


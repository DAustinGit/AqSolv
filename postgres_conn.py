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
def fetch_data(column: str, SMILES: str,  table: str, users_table:str) -> pd.DataFrame:    
    url = cnx()
    try:
        engine = create_engine(url)
        cleaned_smiles = str(SMILES).replace('\r', '').replace('\n', '').strip()
        query_1 = f'SELECT * FROM {table} WHERE "{column}" = :smiles_val'
        query_2 = f'SELECT * FROM {users_table} WHERE "{column}" = :smiles_val'
        query1 = text(query_1)
        query2 = text(query_2)
        with engine.connect() as connection:
            print("Successfully connected to Azure postgreSQL SQL Server via SQLAlchemy!")
            print (SMILES)
            
            result = connection.execute(query1, {"smiles_val": cleaned_smiles})
            
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
            if df.empty:
                result = connection.execute(query2, {"smiles_val": cleaned_smiles})
                df = pd.DataFrame(result.fetchall(), columns=result.keys())
                if df.empty:
                    return None
                else:
                    return df
            else:
                return df

                 
            
            
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return pd.DataFrame(),e

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
            connection.commit()
                
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return e


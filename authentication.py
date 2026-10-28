
import urllib
import pandas as pd
from sqlalchemy import create_engine, text, MetaData, Table, Column, String, insert, Integer, select
import streamlit as st
import bcrypt
import re
metadata=MetaData()
users = Table("users", metadata,
                  Column("userid", Integer, primary_key=True, autoincrement=True),
                  Column("username", String),
                  Column("password_hash", String)
                  )
  

def cnx():
    server = st.secrets['server'] 
    username = st.secrets['username'] 
    password = st.secrets['password']
    database = 'solubility_training'  
    encoded_password = urllib.parse.quote_plus(password)
    connection_url = f"postgresql+psycopg2://{username}:{encoded_password}@{server}:5432/{database}?sslmode=require"
    return connection_url
#=:smiles_val;
def password_check(username:str, provided_password):
    url = cnx()
    try:
        engine = create_engine(url)
        with engine.connect() as conn:  
            stmt= select(users.c.password_hash).where(users.c.username == username)
            result = conn.execute(stmt).fetchone()
            stored_hash_string = result[0]
            if result is None:
                print("Login failed: User not found.")
                return False
    except Exception as e:
        return e
    provided_password_bytes = provided_password.encode('utf-8')
    print("password provided:", provided_password_bytes)
 
    try: 
        bcrypt.checkpw(provided_password_bytes, stored_hash_string.encode('utf-8'))
        print("Login successful!")
        return True
    except:
        return False



        

def push_user (username:str, password_hash:str):
    url = cnx()
  

    try:
        stmt = insert(users).values(username=username, password_hash=password_hash)
        engine = create_engine(url)
        

        with engine.begin() as conn:
            metadata.create_all(engine)
            result = conn.execute(stmt)
        print(result.inserted_primary_key[0]) # Output: 1
    
                
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return e








def signup(username, password):
    if isinstance(password, str):
        password_bytes = password.encode('utf-8')
        print ("str")
    else:
        password_bytes = password  
  
    hashed_password = bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=12)).decode('utf-8')
    
    # Save 'username' and 'hashed_password' safely to your SQL/NoSQL database
    push_user(username=username, password_hash=hashed_password)
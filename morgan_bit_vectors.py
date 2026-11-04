import urllib
import pandas as pd
from sqlalchemy import create_engine, text
from rdkit import Chem
from rdkit.Chem import rdFingerprintGenerator 
import streamlit as st
import numpy as np
df = pd.read_csv('AqSolv_data.csv')

def push_data(database: str, table: str, dataframe: pd.DataFrame):
    server = st.secrets['server'] 
    username = st.secrets['username'] 
    password = st.secrets['password']  

    encoded_password = urllib.parse.quote_plus(password)
    connection_url = f"postgresql+psycopg2://{username}:{encoded_password}@{server}:5432/{database}?sslmode=require"
    
    try:
        engine = create_engine(connection_url)
        with engine.connect() as connection:
            print("Successfully connected to Azure postgreSQL SQL Server via SQLAlchemy!")
            df.to_sql(name=table, con=engine, if_exists='replace', index=False)
            return df
            
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return pd.DataFrame()


    """
df = df.drop('ESOL predicted log(solubility:mol/L)',axis=1)
df = df.rename(columns={'Compound ID':'Compound_ID'})
df['num_Rotatable_Bonds'] = df['SMILES'].apply(lambda x: Lipinski.NumRotatableBonds(Chem.MolFromSmiles(x)) if pd.notnull else None)
df['num_H_Bond_Acceptors'] = df['SMILES'].apply(lambda x: Lipinski.NumHAcceptors(Chem.MolFromSmiles(x)) if pd.notnull else None)
df['num_H_Bond_Doners'] = df['SMILES'].apply(lambda x: Lipinski.NumHDonors(Chem.MolFromSmiles(x)) if pd.notnull else None)
df['num_Nitrogen_Oxygen'] = df['SMILES'].apply(lambda x: Lipinski.NOCount(Chem.MolFromSmiles(x)) if pd.notnull else None)
df['mol_weight'] = df['SMILES'].apply(lambda x: Descriptors.MolWt(Chem.MolFromSmiles(x)) if pd.notnull else None)
df['LogP'] = df['SMILES'].apply(lambda x: Descriptors.MolLogP(Chem.MolFromSmiles(x)) if pd.notnull else None)
df['aromatic proportion'] = df['SMILES'].apply(calculate_aromatic_proportion)
df['TPSA'] = df['SMILES'].apply(lambda x: Descriptors.TPSA(Chem.MolFromSmiles(x), includeSandP=True) if pd.notnull else None)
"""
morgan_gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
def smiles_to_fp(smi, generator):
    mol = Chem.MolFromSmiles(smi)
    if mol is None:
        return np.zeros(generator.GetFpSize(), dtype='u1')
    
    # Use the generator's native GetFingerprint method
    bv = generator.GetFingerprint(mol)
    return np.frombuffer(bv.ToBitString().encode(), dtype='u1') - 48


fp_columns = df['SMILES'].apply(lambda x: smiles_to_fp(x,morgan_gen)).tolist()
df_bits = pd.DataFrame(fp_columns, columns=[f"Bit_{i}" for i in range(2048)])
df = pd.concat([df, df_bits], axis=1)
print (df)
#push_data(database='solubility_training', table='mol_properties_exp', dataframe=df)
df.to_csv("AqSolv_morgan_bit_vectors.csv")
#df.to_csv('mol_properties.csv', index=False)
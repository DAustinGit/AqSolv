import urllib
import pandas as pd
from sqlalchemy import create_engine, text
from rdkit import Chem
from rdkit.Chem import Descriptors, Lipinski
import streamlit as st

df = pd.read_csv('https://raw.githubusercontent.com/dataprofessor/data/refs/heads/master/delaney.csv')

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

def calculate_aromatic_proportion(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None  
    aromatic_atoms = sum(1 for atom in mol.GetAtoms() if atom.GetIsAromatic())
    heavy_atoms = Descriptors.HeavyAtomCount(mol)
    
    if heavy_atoms == 0:
        return 0.0
        
    return aromatic_atoms / heavy_atoms

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

print (df)
push_data(database='solubility_training', table='mol_properties_exp', dataframe=df)
df.to_csv('mol_properties.csv', index=False)
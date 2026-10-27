#to run: python -m streamlit run app.py

import streamlit as st
from streamlit_ketcher import st_ketcher
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors, Descriptors, Lipinski
import pandas as pd
import postgres_conn as db
import math
import joblib
st.set_page_config(layout="wide")
st.title("AqSolv V1")

st.subheader("Draw your molecule below and click apply to predict solubility:")
smiles1 = st_ketcher() 
@st.cache_data(ttl=3600)
def fetch(smiles2) -> pd.DataFrame:
    data,e = db.fetch_data(SMILES = smiles2, column = "SMILES", table='mol_properties_exp') 
    st.error(f"SMILES = {smiles2}, lenghth = {len (smiles2)}")
    if data is None or (isinstance(data, pd.DataFrame) and data.empty):
        st.error (e)
        return None
    return data
def push(mol_params):
    db.push_data (mol_params, table='mol_properties_exp')
    print (mol_params)

def calc_properties(mol):
     if mol is not None:
        formula = rdMolDescriptors.CalcMolFormula(mol)
        mol_weight = Descriptors.MolWt(mol)
        mol_logp = Descriptors.MolLogP(mol)
        rotatable_bonds = Lipinski.NumRotatableBonds(mol)        
        heavy_atom_count = Lipinski.HeavyAtomCount(mol)
        
        aromatic_atoms = len([atom for atom in mol.GetAtoms() if atom.GetIsAromatic()])
        aromatic_proportion = (aromatic_atoms / heavy_atom_count) if heavy_atom_count > 0 else 0.0
        H_Acceptors = Lipinski.NumHAcceptors(mol)
        H_Donors = Lipinski.NumHDonors(mol)
        Nitrogen_Oxygen = Lipinski.NOCount(mol)
        tpsa = Descriptors.TPSA(mol, includeSandP=True)
        st.info(f"**Generated SMILES:** `{smiles2}`")
        calc_params = pd.DataFrame([[
                                     rotatable_bonds, H_Acceptors, 
                                    H_Donors, Nitrogen_Oxygen, mol_weight, mol_logp, 
                                    aromatic_proportion, tpsa
                                ]], columns=[
                                    
                                    'num_Rotatable_Bonds','num_H_Bond_Acceptors', 'num_H_Bond_Doners', 
                                    'num_Nitrogen_Oxygen', 'mol_weight', 'LogP', 'aromatic proportion', 'TPSA'
                                ])
      
        fetched_data =  fetch(smiles2)
        
        pipeline = joblib.load("AqSolv_model_v1")
        solubility_prediction = pipeline.predict(calc_params)
        st.info(f"**predicted LogS (at 25°C):** `{solubility_prediction[0]:.2f}, {(pow(10,solubility_prediction[0])*mol_weight):.2f} g/L`")
        if  fetched_data is not None:
            st.success ("molecule found in database")
            st.dataframe(fetched_data)         
        else:
            st.info ("Molecule not in database please add it below")
            with st.form("add molecule"):
                solubility = st.text_input('Add solubility (g/L) at 25°C', value="0.0")
                submit_button = st.form_submit_button("Add to database")
                if submit_button:
                    try: 
                        logS = math.log10((float(solubility)) / mol_weight)
                        mol_params = pd.DataFrame([[
                            formula, logS, smiles2, rotatable_bonds, H_Acceptors, 
                            H_Donors, Nitrogen_Oxygen, mol_weight, mol_logp, 
                            aromatic_proportion, tpsa
                        ]], columns=[
                            'Compound_ID','measured log(solubility:mol/L)','SMILES',
                            'num_Rotatable_Bonds','num_H_Bond_Acceptors', 'num_H_Bond_Doners', 
                            'num_Nitrogen_Oxygen', 'mol_weight', 'LogP', 'aromatic proportion', 'TPSA'
                        ])
                                
                        
                        push(mol_params)
                        st.success("Successfully added to database! Refreshing...")
                        st.cache_data.clear() # Clear cache so it fetches fresh on rerun
                        st.rerun()
                    except ValueError:
                        st.warning("Please enter a valid numeric value for solubility.")
                    except Exception as e:
                        st.error(f"Database Error: {e}")

     else:
        st.error("The drawn structure is not completely recognized yet. Keep drawing!")

if smiles1:
    mol = Chem.MolFromSmiles(smiles1)
    smiles2 = Chem.MolToSmiles(mol, kekuleSmiles=False)
    calc_properties(mol)

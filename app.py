#to run: python -m streamlit run app.py

import streamlit as st
from streamlit_ketcher import st_ketcher
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors, Descriptors, Lipinski
import pandas as pd
import postgres_conn as db
import math
import joblib
import authentication as auth
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

st.set_page_config(layout="wide")
st.title("AqSolv V1")

st.subheader("Draw your molecule below and click apply to predict solubility:")
smiles1 = st_ketcher() 
@st.cache_data(ttl=3600)
def fetch(smiles2) -> pd.DataFrame:
    data = db.fetch_data(SMILES = smiles2, column = "SMILES", table='mol_properties_exp') 
    if data is None or (isinstance(data, pd.DataFrame) and data.empty):
    
        return None
    return data
def push(mol_params):
    db.push_data (mol_params, table='mol_properties_exp')
    print (mol_params)






@st.dialog("please log in")
def login_page():
    message_placeholder = st.empty()

    if "login_error" in st.session_state and st.session_state.login_error:
        message_placeholder.error(st.session_state.login_error)
        # Clear it so it doesn't persist forever
        st.session_state.login_error = None
    st.text_input("User Name", key= "user_name")
    st.text_input("Password", key="password", type="password")
    
    if st.button ("submit"):
        session = auth.details(st.session_state.user_name, st.session_state.password)

        if session.password_check () == True:
                st.session_state.logged_in = True
                st.session_state.login_success_msg = "Log in successful!" 
                st.rerun()
        else:
                st.session_state.login_error = "Incorrect username or password"
                st.rerun()






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
      
        pipeline = joblib.load("AqSolv_model_v1")
        solubility_prediction = pipeline.predict(calc_params)
        fetched_data =  fetch(smiles2)
        col1, col2, col3, col4, col5 = st.columns(5, vertical_alignment="bottom")
        with col1:
            st.metric(label= "number of rotatable bonds", value=rotatable_bonds)
            st.metric(label= "LogP", value=round(mol_logp,2))
        with col2:
            st.metric(label= "number of H Bond donors", value=H_Donors)
            st.metric(label= "number of H Bond donors", value=H_Acceptors)
        with col3:
            st.metric(label= "Total Polar Surface Srea", value=tpsa)
            st.metric(label= "molecular weight", value=str(round(mol_weight,2)) +" g/mol")
            
        if  fetched_data is not None:
            st.success ("molecule found in database")
            experimental_Logs = fetched_data['measured log(solubility:mol/L)'].iloc[0]
            with col4:
                st.metric(label= "predicted LogS", value=round(solubility_prediction[0],2))
                st.metric(label= "predicted solubility", value=str(round(pow(10,solubility_prediction[0])*mol_weight,2))+" g/L")

            with col5:
                st.metric(label= "experimental LogS", value=experimental_Logs)
                st.metric(label= "experimental solubility", value=str(round(pow(10,experimental_Logs)*mol_weight,2))+" g/L")
                


          
        else:
            with col5:
                st.metric(label= "predicted LogS", value=round(solubility_prediction[0],2))
                st.metric(label= "predicted solubility", value=str(round(pow(10,solubility_prediction[0])*mol_weight,2))+" g/L")
            st.info ("Molecule not in database please add it below")
            with st.form("add molecule"):
                if st.session_state.logged_in == False:
                    log_in = st.form_submit_button("Log In")
                    if log_in:
                        login_page()
                else:
                    log_out = st.form_submit_button("Log out")
                    if log_out:
                        st.session_state.logged_in = False
                        st.rerun()
                if st.session_state.logged_in == True:
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



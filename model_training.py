import urllib
import pandas as pd
from sqlalchemy import create_engine, text
import joblib

from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsRegressor
from sklearn import linear_model
from sklearn.linear_model import LassoCV
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.ensemble import StackingRegressor
from sklearn.metrics import mean_squared_error, r2_score
import streamlit as st

def fetch_data(database: str, table: str) -> pd.DataFrame:
    server = st.secrets['server'] 
    username = st.secrets['username'] 
    password = st.secrets['password']  
      # <-- Replace with your actual password
    
    # 1. Safely URL-encode the pyodbc connection string parameters
    # This prevents errors if your password contains special characters (like @, #, or :)

    encoded_password = urllib.parse.quote_plus(password)
    connection_url = f"postgresql+psycopg2://{username}:{encoded_password}@{server}:5432/{database}?sslmode=require"
    
    try:
        engine = create_engine(connection_url)
        query = text(f"SELECT * FROM {table};")
        with engine.connect() as connection:
            print("Successfully connected to AWS SQL Server via SQLAlchemy!")
            df = pd.read_sql(query, con=connection)
            return df
            
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return pd.DataFrame()
df = fetch_data(database='solubility_training', table='mol_properties_exp')
print (df.head)
y = df['measured log(solubility:mol/L)']   # Y is feature used for training
x = df.drop(['measured log(solubility:mol/L)', 'Compound_ID', 'SMILES'], axis=1)     #X is the feature we are predicting drop logS and axis = 1 --> work in coluns

x_train, x_test, y_train, y_test = train_test_split (x, y, test_size= 0.2, random_state = 100) #splits the data for train and test sets testing set is 20% of data
print (x_train)

base_learners = [
    ('lr', linear_model.BayesianRidge()),
    ('knn', KNeighborsRegressor(weights='uniform',n_neighbors=12, algorithm='ball_tree', leaf_size=20))
]

stacking_ensemble = StackingRegressor(
    estimators=base_learners,
    final_estimator=LassoCV(),
    cv = 2                                
)

pipeline = Pipeline([
  ('scaler', StandardScaler()),
  ('stack', stacking_ensemble)  
])

print ("fitting model")
pipeline.fit(x_train, y_train)
print ("testing model")
y_train_pred = pipeline.predict(x_train)
y_test_pred = pipeline.predict(x_test)

joblib.dump(pipeline, "AqSolv_model_v1")

train_score = pipeline.score(x_train, y_train)
train_MSE = mean_squared_error(y_train, y_train_pred)
test_MSE = mean_squared_error(y_test, y_test_pred)
# 2. Calculate the score on the test data
test_score = pipeline.score(x_test, y_test)

print(f"Training R² Score: {train_score:.4f}")
print(f"Test R² Score:     {test_score:.4f}")

gap = train_score - test_score
print(f"Performance Gap:   {gap:.4f}")

bkr_results = pd.DataFrame(['Baysian Ridge + KNN', 'RidgeCV', train_score, test_score, gap, test_MSE, train_MSE]).transpose()
bkr_results.columns = ['Base learners', 'final estimator', 'Training R2', 'testing R2', 'performance gap', 'test MSE', 'train MSE']
print(bkr_results)
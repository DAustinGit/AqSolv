# AqSolv V1

An interactive web app for predicting the **aqueous solubility** of small molecules. Draw a structure in the browser, and AqSolv calculates key physicochemical properties and predicts water solubility using a trained machine learning model.

Built with [Streamlit](https://streamlit.io/), [RDKit](https://www.rdkit.org/), and [Ketcher](https://github.com/epam/ketcher).
[Data](https://github.com/dataprofessor/data/blob/master/delaney_solubility_with_descriptors.csv) inspiration from the [Chanin Nantasenamat](https://github.com/dataprofessor) 

---

## Features

- **Draw molecules** with an embedded Ketcher chemical editor, then click *Apply* to run a prediction.
- **Instant descriptor calculation** using RDKit (molecular weight, LogP, TPSA, H-bond donors/acceptors, rotatable bonds, and more).
- **Solubility prediction** returned as both **LogS** (log10 mol/L) and **g/L**.
- **Experimental lookup**: if the molecule already exists in the database, the measured solubility is shown next to the prediction for easy comparison.
- **User accounts**: log in or sign up to contribute your own experimental solubility measurements for molecules not yet in the database.
- **Caching** of database lookups (1 hour) for a responsive UI.

---

## How it works

1. The structure drawn in Ketcher is returned as a SMILES string.
2. RDKit parses it and converts it to canonical SMILES.
3. Eight descriptors are calculated and passed to a pre-trained scikit-learn pipeline (`model/AqSolv_model_v1`):

   | Descriptor | Column name |
   |---|---|
   | Rotatable bonds | `num_Rotatable_Bonds` |
   | H-bond acceptors | `num_H_Bond_Acceptors` |
   | H-bond donors | `num_H_Bond_Doners` |
   | Nitrogen + oxygen count | `num_Nitrogen_Oxygen` |
   | Molecular weight | `mol_weight` |
   | Crippen LogP | `LogP` |
   | Aromatic proportion (aromatic atoms / heavy atoms) | `aromatic proportion` |
   | Topological polar surface area | `TPSA` |

4. The model predicts **LogS**. Solubility in g/L is derived as:

   ```
   solubility (g/L) = 10^LogS × molecular weight (g/mol)
   ```

5. The canonical SMILES is looked up in the `mol_properties_exp` (reference data) and `user_mols` (user contributed) database tables.
   - **Found:** predicted and experimental values are displayed side by side.
   - **Not found:** the prediction is shown, and logged-in users can add their own measured value.

When a user submits a measurement (in g/L at 25 °C), it is converted to LogS with `log10(solubility / mol_weight)` and stored in `user_mols` along with the calculated descriptors and the user's ID.

---

## Project structure

```
├── data
│    └── AqSolv_data.csv           # copy of data from postgres database
│  
├── data preparation
│    └── chem_properties.py       # generate calculated molecular descriptors from Delaney dataset and push to database
│                                   push to PostgreSQL database 
├── app.py                        # Streamlit application (this file)
├── model/
│   └── AqSolv_model_v1           # Trained model pipeline (joblib, Scikit-learn)
|   └── model_training            # model training script
├── development notebooks          # Jupyter notebooks containing model selection and optimisation
│    ├── AqSolv_ensembles_extended_properties.ipynb   # development and optimisation of ensemble methods using AqSolv_data dataset
│    ├── AqSolv_ensembles.ipynb                       # ensemble methods using Delaney dataset
│    ├── AqSolv_simple_regression.ipynb               # simple linear regression models using Delaney dataset
│                               
└── src/
    ├── postgres_conn.py          # Database access (fetch_data, push_data)
    └── authentication.py         # Login / sign-up logic (password_check, signup)
```

---

## Getting started
 It's easy; just go to <https://aqsolv-a3yekgdj68jxw4ipqoqnjp.streamlit.app/>!

### Prerequisites (local)

- Python 3.9+
- A running PostgreSQL database containing the `mol_properties_exp` and `user_mols` tables
- The trained model file at `model/AqSolv_model_v1`

### Installation

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd <your-repo-folder>

# 2. (Recommended) Create a virtual environment
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install streamlit streamlit-ketcher rdkit pandas joblib scikit-learn psycopg2-binary
```

> RDKit is also available through conda (`conda install -c conda-forge rdkit`) if `pip` gives you trouble.
>
> Make sure the `scikit-learn` version matches the one used to train and save the model, otherwise `joblib` may fail to load it or produce warnings.

### Database configuration

Database connection settings are handled in `src/postgres_conn.py`. Update that file (or the environment variables / secrets it reads from) with your own PostgreSQL credentials before running the app.

The app expects:

- **`mol_properties_exp`**: reference dataset of experimental solubilities. It must include a `SMILES` column and a `measured log(solubility:mol/L)` column.
- **`user_mols`**: user-submitted molecules, with the following columns:

  `Compound_ID`, `measured log(solubility:mol/L)`, `SMILES`, `num_Rotatable_Bonds`, `num_H_Bond_Acceptors`, `num_H_Bond_Doners`, `num_Nitrogen_Oxygen`, `mol_weight`, `LogP`, `aromatic proportion`, `TPSA`, `userid`

> **Security note:** never commit database credentials to version control. Prefer environment variables or Streamlit's `.streamlit/secrets.toml` (and add it to `.gitignore`).

### Run the app

```bash
python -m streamlit run app.py
```

Then open the URL shown in your terminal (usually http://localhost:8501).

---

## Usage

1. **Draw** a molecule in the editor (or paste/import a structure).
2. Click **Apply** in Ketcher.
3. View the calculated properties and the predicted solubility.
4. *(Optional)* **Sign up / log in** using the form at the bottom of the page. If your molecule isn't in the database, enter its experimentally measured solubility (g/L at 25 °C) and click **Add to database** to contribute it.

---

## Limitations

- Predictions are estimates from a model trained on a limited set of descriptors and should not replace experimental measurement.
- Solubility is modelled for **water at 25 °C**.
- Incomplete or invalid structures are not recognised until the drawing forms a valid molecule.
- Accuracy may drop for molecules that are very different from the training data (e.g. salts, organometallics, large natural products).

---

## Tech stack

| Purpose | Library |
|---|---|
| Web UI | Streamlit |
| Molecule editor | streamlit-ketcher |
| Cheminformatics | RDKit |
| Data handling | pandas |
| Model loading | joblib / scikit-learn |
| Database | PostgreSQL |

---

## Author

Daniel Austin
any issues contact me at daniel-austin1996@hotmail.com

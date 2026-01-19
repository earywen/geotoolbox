import pandas as pd
import os

base = os.getcwd()
ref_eaux = os.path.join(base, "ressources", "Eaux souterraines", "Eaux souterraines familles et paramètres et valeurs réglementaires.xlsx")
ref_sols = os.path.join(base, "ressources", "Sols", "Sols - familles et paramètres et valeurs réglementaires.xlsx")

print(f"Reading {ref_eaux}...")
try:
    df_eaux = pd.read_excel(ref_eaux, header=None)
    # Check Agrolab config: code is col 0, name is col 4.
    print("Eaux Reference Data (First 5 rows):")
    print(df_eaux.iloc[0:5, [0, 4, 5]]) # Codes, Names, Units
except Exception as e:
    print(e)
    
print("\nReading {ref_sols}...")
try:
    df_sols = pd.read_excel(ref_sols, header=None)
    print("Sols Reference Data (First 5 rows):")
    print(df_sols.iloc[0:5, :])
except Exception as e:
    print(e)

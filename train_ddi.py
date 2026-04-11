import pandas as pd
import numpy as np
import pickle
import os

# 1. Create a Synthetic Dataset without severity
def generate_synthetic_data():
    data = [
        ["ibuprofen", "aspirin", "Increased risk of GI bleeding"],
        ["warfarin", "ibuprofen", "Serious bleeding risk"],
        ["lisinopril", "ibuprofen", "Reduced kidney function"],
        ["sildenafil", "nitroglycerin", "Dangerous hypotension"],
        ["simvastatin", "amiodarone", "Increased muscle toxicity"],
        ["fluoxetine", "sumatriptan", "Serotonin syndrome risk"]
    ]
    df = pd.DataFrame(data, columns=["drug1", "drug2", "description"])
    df.to_csv("ddi_data.csv", index=False)
    print("Synthetic DDI dataset (3-column) created at ddi_data.csv")

# 2. Simple Lookup Mapping Generator (Replaces the classifier)
class DDITrainer:
    def __init__(self, data_path="ddi_data.csv"):
        self.data_path = data_path
        
    def train(self):
        if not os.path.exists(self.data_path):
            print(f"Error: {self.data_path} not found.")
            return

        df = pd.read_csv(self.data_path)
        
        # Clean header names (strip spaces)
        df.columns = [c.strip() for c in df.columns]

        # Map actual headers to internal names if they exist
        header_map = {
            "Drug 1": "drug1",
            "Drug 2": "drug2",
            "Interaction Description": "description"
        }
        df = df.rename(columns=header_map)
        
        if 'drug1' not in df.columns or 'drug2' not in df.columns:
            print(f"Error: Could not find 'Drug 1' or 'Drug 2' columns. Found: {list(df.columns)}")
            return

        # Create a lookup dictionary where keys are sorted pairs
        df['pair'] = df.apply(lambda x: "-".join(sorted([str(x['drug1']).lower().strip(), str(x['drug2']).lower().strip()])), axis=1)
        
        # Mapping pair -> description
        descriptions = dict(zip(df['pair'], df['description']))
        
        # In this simplified 3-column version, we don't need a numeric classifier,
        # we treat the entire dataset as the "model"
        results = {
            "model_type": "lookup",
            "descriptions": descriptions
        }
        
        with open("ddi_trained_model.pkl", "wb") as f:
            pickle.dump(results, f)
        print("DDI Lookup Mapping generated and saved to ddi_trained_model.pkl")

if __name__ == "__main__":
    # If file doesn't exist, generate example
    if not os.path.exists("ddi_data.csv"):
        generate_synthetic_data()
    
    trainer = DDITrainer()
    trainer.train()

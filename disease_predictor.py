import pandas as pd
import numpy as np
from sklearn.preprocessing import MultiLabelBinarizer, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import accuracy_score
import os


class DiseasePredictor:
    def __init__(self):
        file_name = "disease_symptoms.csv"

        if not os.path.exists(file_name):
            print("Dataset file missing")
            exit()

        self.df = pd.read_csv(file_name)
        print("Dataset loaded")

        symptom_cols = [c for c in self.df.columns if "symptoms__" in c]
        self.df["symptom_list"] = self.df[symptom_cols].values.tolist()
        self.df["symptom_list"] = self.df["symptom_list"].apply(
            lambda x: [str(i).lower().strip() for i in x if pd.notna(i)]
        )

        self.sym_bin = MultiLabelBinarizer()
        sym_matrix = self.sym_bin.fit_transform(self.df["symptom_list"])

        X = sym_matrix

        self.dis_enc = LabelEncoder()
        y = self.dis_enc.fit_transform(self.df["disease"])

        x_train, x_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        self.rf = RandomForestClassifier()
        self.nb = GaussianNB()

        self.rf.fit(x_train, y_train)
        self.nb.fit(x_train, y_train)

#       print("Random Forest acc:", round(
 #           accuracy_score(y_test, self.rf.predict(x_test)), 2))
  #      print("Naive Bayes acc:", round(
   #         accuracy_score(y_test, self.nb.predict(x_test)), 2))

    def predict(self, symptoms, severity, duration, comorbidities):

        import difflib
        
        raw_input = symptoms.lower().strip()
        known_symptoms = list(self.sym_bin.classes_)
        
        sym_list = []
        
        # 1. Broad extraction: Find any known symptoms that appear anywhere in the user's string
        # This fixes the issue where users type "fever and headache" without using commas
        for known in known_symptoms:
            # We enforce a small length limit so short acronyms don't falsely trigger inside other words
            if len(known) > 3 and known in raw_input:
                sym_list.append(known)
                
        # 2. Strict / Typos extraction: Fallback to comma separation and fuzzy matching
        sym_list_raw = [i.strip() for i in raw_input.split(",")]
        for s in sym_list_raw:
            if not s:
                 continue
            # Skip if this chunk already clearly matches an extracted symptom from step 1
            if any(k in s for k in sym_list):
                 continue
                 
            matches = difflib.get_close_matches(s, known_symptoms, n=1, cutoff=0.6)
            if matches:
                sym_list.append(matches[0])
                
        # Clean duplicates
        sym_list = list(set(sym_list))

        if len(sym_list) == 0:
            return "No valid symptoms found in dataset."

        sym_vec = self.sym_bin.transform([sym_list])

        x_input = sym_vec

        pred = self.rf.predict(x_input)[0]
        disease_name = self.dis_enc.inverse_transform([pred])[0]

        return disease_name


if __name__ == "__main__":
    model = DiseasePredictor()

    print("\nEnter patient details")
    symptoms = input("Symptoms (comma separated): ")
    severity = input("Severity: ")
    duration = input("Duration (e.g. 5 days): ")
    comorb = input("Comorbidities (comma separated or none): ")

    result = model.predict(symptoms, severity, duration, comorb)

    print("\nPredicted Disease:")
    print(result)

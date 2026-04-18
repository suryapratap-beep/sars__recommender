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
            raise FileNotFoundError(f"Dataset file {file_name} missing")

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

    def predict(self, symptoms, severity, duration, comorbidities, father_history="", mother_history="", model_type="rf"):

        import difflib
        
        raw_input = symptoms.lower().strip()
        known_symptoms = list(self.sym_bin.classes_)
        
        sym_list = []
        
        # 1. Broad extraction
        for known in known_symptoms:
            if len(known) > 3 and known in raw_input:
                sym_list.append(known)
                
        # 2. Strict / Typos extraction
        sym_list_raw = [i.strip() for i in raw_input.split(",")]
        for s in sym_list_raw:
            if not s:
                 continue
            if any(k in s for k in sym_list):
                 continue
                 
            matches = difflib.get_close_matches(s, known_symptoms, n=1, cutoff=0.6)
            if matches:
                sym_list.append(matches[0])
                
        sym_list = list(set(sym_list))

        if len(sym_list) == 0:
            return "No valid symptoms found in dataset."

        sym_vec = self.sym_bin.transform([sym_list])

        # Model Selection
        if model_type == "nb":
            model = self.nb
            model_name = "Naive Bayes"
        else:
            model = self.rf
            model_name = "Random Forest"

        # Get Probabilities
        probs = model.predict_proba(sym_vec)[0]
        top_idx = np.argsort(probs)[-1]
        
        disease_name = self.dis_enc.inverse_transform([top_idx])[0]
        base_prob = probs[top_idx] * 100
        
        # Parental Factor Assessment
        genetic_boost = 0
        p_history = (str(father_history) + " " + str(mother_history)).lower()
        
        # Heuristic: If the predicted disease or key parts of its name are in parental history
        # we increase the "Genetic Confidence"
        disease_keywords = [disease_name.lower()]
        if "(" in disease_name: # Handle names like "Leprosy (Hansen's Disease)"
             disease_keywords.extend(disease_name.lower().replace("(","").replace(")","").split())
        
        match_found = False
        for kw in disease_keywords:
            if len(kw) > 3 and kw in p_history:
                match_found = True
                break
        
        if match_found:
            # Boost the probability if there's a genetic link
            # We don't want to exceed 99% purely based on heuristics
            genetic_boost = min(25, 99 - base_prob)
            final_prob = base_prob + genetic_boost
            return f"Predicted ({model_name}): {disease_name} | Estimated Probability: {final_prob:.1f}% (Genetic Risk Factor: Elevated)"
        else:
            # Standard probability
            return f"Predicted ({model_name}): {disease_name} | Estimated Probability: {base_prob:.1f}% (Genetic Risk Factor: Low/Unknown)"


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

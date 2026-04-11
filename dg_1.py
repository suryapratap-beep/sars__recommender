import pandas as pd
import numpy as np
from sklearn.preprocessing import MultiLabelBinarizer, LabelEncoder
from sklearn.naive_bayes import GaussianNB
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import os


class MedicineRecommender:
    def __init__(self):
        file_name = "demo6.csv"
        if not os.path.exists(file_name):
            raise FileNotFoundError("demo6.csv missing - get real data")

        self.df = pd.read_csv(file_name)
        print("Dataset loaded:", self.df.shape)

        self.df['Symptom'] = self.df['Symptom'].str.lower()
        self.df['Medicine'] = self.df['Medicine'].str.lower()
        self.df['Symptoms_list'] = self.df['Symptom'].apply(
            lambda x: [i.strip() for i in x.split(',')]
        )

        self.med_enc = LabelEncoder()
        self.df['med_label'] = self.med_enc.fit_transform(self.df['Medicine'])

        self.age_enc = LabelEncoder()
        self.df['age_label'] = self.age_enc.fit_transform(self.df['Age Group'])

        self.sym_bin = MultiLabelBinarizer()
        sym_matrix = self.sym_bin.fit_transform(self.df['Symptoms_list'])

        X = np.hstack((sym_matrix, self.df['age_label'].values.reshape(-1, 1)))
        y = self.df['med_label']

        x_train, x_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        self.models = {
            'nb': GaussianNB(),
            'rf': RandomForestClassifier(random_state=42),
            'knn': KNeighborsClassifier(),
            'mlp': MLPClassifier(hidden_layer_sizes=(100, 50), max_iter=500, random_state=42)
        }

        for name, model in self.models.items():
            model.fit(x_train, y_train)
            acc = accuracy_score(y_test, model.predict(x_test))
            print(f"{name.upper()} acc: {round(acc, 2)}")

    def age_grp(self, age):
        if age <= 1:
            return "Below 1 year"
        elif 1 < age <= 3:
            return "1-3 years"
        elif 4 <= age <= 6:
            return "3-6 years"
        elif 7 <= age <= 15:
            return "6-15 years"
        else:
            return "Above 15 years"

    def dur_to_days(self, d):
        d = d.lower().strip()
        if "day" in d:
            try:
                return int(d.split()[0])
            except:
                return 0
        elif "week" in d:
            try:
                return int(d.split()[0]) * 7
            except:
                return 7
        return 0

    def recommend(self, sym_input, age, gender, preg, feed, dur):
        age_grp = self.age_grp(age)
        dur_days = self.dur_to_days(dur)

        if dur_days > 9:
            return "Symptoms >9 days. See doctor NOW."

        symptoms = [i.strip().lower() for i in sym_input.split(',')]
        results = []

        # ML on full symptom vector first
        sym_list = [symptoms]  # list-of-lists for MultiLabelBinarizer
        sym_vec = self.sym_bin.transform(sym_list)
        age_vec = self.age_enc.transform([age_grp]).reshape(-1, 1)
        x_in = np.hstack((sym_vec, age_vec))

        preds = [model.predict(x_in)[0] for model in self.models.values()]
        final_pred = max(set(preds), key=preds.count)
        model_med = self.med_enc.inverse_transform([final_pred])[0]

        results.append(f"For symptoms '{sym_input}' (age {age_grp}):")
        results.append(f"ML Ensemble+MLP: {model_med}")

        # Fallback exact matches (backup only)
        for s in symptoms:
            match = self.df[
                (self.df['Symptom'].str.contains(s, case=False, na=False)) &
                (self.df['Age Group'].str.lower() == age_grp.lower())
            ]
            if len(match) > 0:
                row = match.iloc[0]
                dose = row.get('Dosage', 'N/A')
                results.append(
                    f"  Exact match '{s}': {row['Medicine']} ({dose})")

        if gender.lower() == "female" and age >= 18:
            if preg.lower() == "yes":
                results.append("PREGNANT: Doctor required.")
            if feed.lower() == "yes":
                results.append("BREASTFEEDING: Doctor required.")

        return "\n".join(results)


if __name__ == "__main__":
    recommender = MedicineRecommender()

    print("\nPatient details:")
    symptoms = input("Symptoms (comma sep): ")
    age = int(input("Age: "))
    gender = input("Gender (m/f): ").strip().lower()
    preg = feed = "no"
    if gender == "female" and age >= 18:
        preg = input("Pregnant? (y/n): ").strip().lower()
        feed = input("Breastfeeding? (y/n): ").strip().lower()
    duration = input("Duration (3 days/1 week): ")

    result = recommender.recommend(symptoms, age, gender, preg, feed, duration)
    print("\n--- RECOMMENDATION ---")
    print(result)

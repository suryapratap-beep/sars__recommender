import pandas as pd
import numpy as np
from xgboost import XGBClassifier
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
            print("demo6.csv file missing")
            exit()

        self.df = pd.read_csv(file_name)
        print("Dataset loaded successfully")

        counts = self.df['Medicine'].value_counts()
        valid_meds = counts[counts >= 2].index
        self.df = self.df[self.df['Medicine'].isin(valid_meds)]

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
        y = self.df['Medicine']   # use original labels first

        x_train, x_test, y_train, y_test = train_test_split(
            X, y,
            test_size=0.2,
            random_state=42,
            stratify=y   # ✅ IMPORTANT
        )
        # NOW encode AFTER split
        self.med_enc = LabelEncoder()

        y_train = self.med_enc.fit_transform(y_train)
        y_test = self.med_enc.transform(y_test)

        # Models
        self.nb = GaussianNB()
        self.rf = RandomForestClassifier()
        self.knn = KNeighborsClassifier()

        # ✅ MLP MODEL (proper config)
        self.mlp = MLPClassifier(
            hidden_layer_sizes=(128, 64),
            max_iter=500,   # increase
            random_state=42
        )

        self.xgb = XGBClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            use_label_encoder=False,
            eval_metric='mlogloss'
        )

        # Training
        self.nb.fit(x_train, y_train)
        self.rf.fit(x_train, y_train)
        self.knn.fit(x_train, y_train)
        self.mlp.fit(x_train, y_train)
        self.xgb.fit(x_train, y_train)

        # Accuracy
        print("Naive Bayes acc:", round(
            accuracy_score(y_test, self.nb.predict(x_test)), 2))
        print("Random Forest acc:", round(
            accuracy_score(y_test, self.rf.predict(x_test)), 2))
        print("KNN acc:", round(
            accuracy_score(y_test, self.knn.predict(x_test)), 2))
        print("MLP acc:", round(
            accuracy_score(y_test, self.mlp.predict(x_test)), 2))
        print("XGBoost acc:", round(
            accuracy_score(y_test, self.xgb.predict(x_test)), 2))

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
            return "Symptoms lasting more than a week. Consult a doctor."

        symptoms = [i.strip().lower() for i in sym_input.split(',')]
        results = []

        for s in symptoms:
            match = self.df[
                (self.df['Symptom'].str.contains(s, case=False, na=False)) &
                (self.df['Age Group'].str.lower() == age_grp.lower())
            ]

            if len(match) > 0:
                results.append(f"\nFor symptom '{s}':")
                row = match.iloc[0]
                dose = row['Dosage'] if 'Dosage' in self.df.columns else 'N/A'
                results.append(f"Medicine: {row['Medicine']}")
                results.append(f"Dosage: {dose}")

            else:
                try:
                    sym_vec = self.sym_bin.transform([[s]])
                    age_vec = self.age_enc.transform([age_grp]).reshape(-1, 1)
                    x_in = np.hstack((sym_vec, age_vec))

                    preds = [
                        self.nb.predict(x_in)[0],
                        self.rf.predict(x_in)[0],
                        self.knn.predict(x_in)[0],
                        self.mlp.predict(x_in)[0],
                        self.xgb.predict(x_in)[0]
                    ]

                    weights = {
                        "nb": 1,
                        "rf": 3,
                        "knn": 1,
                        "mlp": 2,
                        "xgb": 4
                    }

                    preds = [
                        ("nb", self.nb.predict(x_in)[0]),
                        ("rf", self.rf.predict(x_in)[0]),
                        ("knn", self.knn.predict(x_in)[0]),
                        ("mlp", self.mlp.predict(x_in)[0]),
                        ("xgb", self.xgb.predict(x_in)[0])
                    ]

                    vote_count = {}

                    for model, pred in preds:
                        vote_count[pred] = vote_count.get(
                            pred, 0) + weights[model]

                    final_pred = max(vote_count, key=vote_count.get)

                    final_pred = max(set(preds), key=preds.count)
                    model_med = self.med_enc.inverse_transform([final_pred])[0]

                    results.append(f"\nFor symptom '{s}':")
                    results.append(f"Predicted (Ensemble): {model_med}")

                except:
                    results.append(f"\nFor symptom '{s}': Prediction failed")

        if gender.lower() == "female" and age >= 18:
            if preg.lower() == "yes":
                results.append("Note: Pregnant. Consult doctor.")
            if feed.lower() == "yes":
                results.append("Note: Breastfeeding. Consult doctor.")

        return "\n".join(results)


if __name__ == "__main__":
    recommender = MedicineRecommender()

    print("\nEnter patient details:")
    symptoms = input("Symptoms (comma separated): ")
    age = int(input("Age: "))
    gender = input("Gender (male/female): ").strip().lower()

    preg = "no"
    feed = "no"

    if gender == "female" and age >= 18:
        preg = input("Pregnant? (yes/no): ").strip().lower()
        feed = input("Breastfeeding? (yes/no): ").strip().lower()

    duration = input("Duration (e.g. 3 days, 1 week): ")

    result = recommender.recommend(symptoms, age, gender, preg, feed, duration)

    print("\n--- Recommendation ---")
    print(result)

import pandas as pd
import re

#  LOAD DATA
df = pd.read_csv("disease_dataset.csv")
df.columns = df.columns.str.strip()  # clean column names
df.fillna("", inplace=True)  # replace missing values

#  GET LIST OF SYMPTOM COLUMNS
symptom_cols = [col for col in df.columns if "symptoms__" in col.lower()]

print("=== Symptom-Based Disease Matching System ===")
print("NOTE: This is NOT a real medical diagnosis.\n")

while True:
    choice = input(
        "Do you want to enter symptoms? (yes/exit): ").strip().lower()
    if choice == "exit":
        print("Exiting...")
        break
    if choice != "yes":
        continue

    #  ASK HOW MANY SYMPTOMS
    while True:
        num_input = input("How many symptoms do you want to enter? ").strip()
        if num_input.isdigit() and int(num_input) > 0:
            num_symptoms = int(num_input)
            break
        else:
            print("Please enter a valid number greater than 0.")

    # COLLECT SYMPTOMS
    user_symptoms = []
    for i in range(1, num_symptoms + 1):
        s = input(f"Enter symptom {i}: ").strip().lower()
        s = re.sub(r"[^a-z0-9\s]", " ", s)
        s = re.sub(r"\s+", " ", s).strip()
        if s != "":
            user_symptoms.append(s)

    if len(user_symptoms) < 1:
        print("\nNo valid symptoms entered. Try again.\n")
        continue

    user_symptoms = list(set(user_symptoms))  # remove duplicates

    #  CALCULATE MATCH SCORES
    results = []
    for i in range(len(df)):
        row = df.iloc[i]
        # Collect all disease symptoms
        disease_symptoms = []
        for col in symptom_cols:
            val = str(row[col]).lower().strip()
            if val != "":
                # split by "and" just in case multiple symptoms in one cell
                if " and " in val:
                    disease_symptoms.extend(
                        [x.strip() for x in val.split(" and ") if x.strip()])
                else:
                    disease_symptoms.append(val)

        disease_symptoms = list(set(disease_symptoms))  # remove duplicates

        # Compute match score (1 point per match)
        score = 0
        for s in user_symptoms:
            if s in disease_symptoms:
                score += 1

        if score > 0:
            results.append((i, score))

    # SHOW TOP MATCHES
    results.sort(key=lambda x: x[1], reverse=True)
    top_results = results[:5]

    if not top_results:
        print("\nNo matching disease found. Try different symptoms.\n")
        continue

    print("\nTop possible matches based on symptoms:\n")
    for rank, (idx, score) in enumerate(top_results, 1):
        print(f"{rank}. {df.loc[idx, 'disease']}  (match score: {score})")

    choice = input(
        "\nSelect a disease number to see details (1-5), or type 'restart': ").strip()
    if choice.lower() == "restart":
        continue
    if not choice.isdigit() or int(choice) < 1 or int(choice) > len(top_results):
        print("\nInvalid selection.\n")
        continue

    selected_idx = top_results[int(choice)-1][0]
    selected_row = df.iloc[selected_idx]

    print(f"\nYou selected: {selected_row['disease']}")

    #  SHOW AVAILABLE FIELDS
    print("\nAvailable fields you can ask for:\n")
    for i, col in enumerate(df.columns, 1):
        print(f"{i}. {col}")

    wanted = input(
        "\nEnter fields you want (comma separated) OR type 'all': ").strip()
    if wanted.lower() == "all":
        fields = list(df.columns)
    else:
        fields = [x.strip() for x in wanted.split(",")]

    print("\n" + "=" * 60)
    print("DISEASE DETAILS")
    print("=" * 60)
    for field in fields:
        if field in selected_row.index:
            print(f"\n{field}:")
            print(selected_row[field])
        else:
            print(f"\n{field}: Not found")

    print("\n" + "-" * 60 + "\n")

import difflib

sym_list_raw = ["fever", "headache", "chest pain"]
known_symptoms = {"fever", "headache", "chest pain", "cough", "chills"}

sym_list = []
for s in sym_list_raw:
    if s in known_symptoms:
        sym_list.append(s)
    else:
        matches = difflib.get_close_matches(s, known_symptoms, n=1, cutoff=0.6)
        if matches:
            sym_list.append(matches[0])
            
print(sym_list)

from disease_predictor import DiseasePredictor
import numpy as np

dp = DiseasePredictor()

def check_symptoms(inputs):
    import difflib
    sym_list_raw = [i.strip().lower() for i in inputs.split(",")]
    known_symptoms = list(dp.sym_bin.classes_)
    sym_list = []
    for s in sym_list_raw:
        if s in known_symptoms:
            sym_list.append(s)
        else:
            matches = difflib.get_close_matches(s, known_symptoms, n=1, cutoff=0.6)
            if matches:
                 sym_list.append(matches[0])
    
    vec = dp.sym_bin.transform([sym_list])
    print(f"Inputs: '{inputs}'")
    print("Mapped to:", sym_list)
    print("Num ones in vector:", np.sum(vec))
    print("Prediction:", dp.dis_enc.inverse_transform([dp.rf.predict(vec)[0]])[0])
    print()

check_symptoms("Sudden muscle weakness")
check_symptoms("Sudden muscle weakness, Loss of muscle tone")

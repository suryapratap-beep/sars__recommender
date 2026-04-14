from disease_predictor import DiseasePredictor
dp = DiseasePredictor()

# Test 1
res1 = dp.predict("Fatigue", "", "", "")
print("Fatigue only:", res1)

# Test 2
res2 = dp.predict("Fatigue, Weight loss", "", "", "")
print("Fatigue + Weight loss:", res2)

# Test 3
res3 = dp.predict("Weight loss", "", "", "")
print("Weight loss only:", res3)

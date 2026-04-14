from disease_predictor import DiseasePredictor
from dg_2 import MedicineRecommender

dp = DiseasePredictor()
mr = MedicineRecommender()

print("Disease Output:", dp.predict("fever, headache", "high", "5 days", "none"))
print("Medicine Output:", mr.recommend("fever", 25, "male", "no", "no", "3 days"))

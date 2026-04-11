from flask import Flask, request, jsonify, send_from_directory
import os

app = Flask(__name__, static_folder='.', static_url_path='')


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


# Disease Prediction Endpoint
@app.route('/predict-disease', methods=['POST'])
def predict_disease():
    data = request.get_json() or {}
    symptoms = (data.get('symptoms', '') or '').lower()
    
    # Simple disease prediction logic
    diseases = []
    
    # Common symptom-disease mappings
    symptom_disease_map = {
        'fever': 'Flu/Common Cold',
        'cough': 'Bronchitis/Asthma',
        'headache': 'Migraine/Tension Headache',
        'chest pain': 'Angina/Heart Disease',
        'shortness of breath': 'Asthma/COPD',
        'dizziness': 'Vertigo/Anemia',
        'nausea': 'Gastroenteritis/Food Poisoning',
        'fatigue': 'Anemia/Thyroid Disease',
        'body ache': 'Flu/Viral Infection',
        'sore throat': 'Strep Throat/Pharyngitis',
        'rash': 'Dermatitis/Measles',
        'joint pain': 'Arthritis/Lupus'
    }
    
    for symptom, disease in symptom_disease_map.items():
        if symptom in symptoms:
            diseases.append(disease)
    
    if not diseases:
        diseases = ['Unknown - Please consult a physician for proper diagnosis']
    
    return jsonify({'diseases': diseases})


# Medicine Recommendation Endpoint
@app.route('/get-drugs', methods=['POST'])
def get_drugs():
    data = request.get_json() or {}
    symptoms = (data.get('symptoms', '') or '').lower()
    history = (data.get('history', '') or '').lower()

    drugs = set()
    
    # Disease-to-drug recommendations
    disease_drug_map = {
        'flu': ['Paracetamol', 'Ibuprofen', 'Rest and hydration'],
        'common cold': ['Paracetamol', 'Vitamin C supplements'],
        'bronchitis': ['Dextromethorphan', 'Guaifenesin', 'Albuterol (if asthma-like)'],
        'asthma': ['Albuterol', 'Ipratropium', 'Corticosteroids'],
        'copd': ['Albuterol', 'Tiotropium', 'Corticosteroids'],
        'migraine': ['Ibuprofen', 'Sumatriptan', 'Aspirin'],
        'tension headache': ['Ibuprofen', 'Paracetamol', 'Relaxation techniques'],
        'angina': ['Nitroglycerin', 'Aspirin', 'Beta-blockers - Consult physician'],
        'heart disease': ['Aspirin', 'ACE inhibitors', 'Statins - Consult physician'],
        'vertigo': ['Meclizine', 'Promethazine', 'Physical therapy'],
        'anemia': ['Iron supplements', 'Vitamin B12', 'Folic acid'],
        'thyroid disease': ['Levothyroxine (Hypothyroidism)', 'Propranolol (Hyperthyroidism) - Consult physician'],
        'gastroenteritis': ['Ondansetron', 'Loperamide', 'Oral rehydration solution'],
        'food poisoning': ['Bismuth subsalicylate', 'Oral rehydration', 'Avoid dairy'],
        'strep throat': ['Amoxicillin', 'Penicillin', 'Throat lozenges'],
        'pharyngitis': ['Paracetamol', 'Ibuprofen', 'Throat lozenges'],
        'dermatitis': ['Hydrocortisone cream', 'Moisturizers', 'Antihistamines'],
        'measles': ['Vitamin A', 'Paracetamol', 'Rest'],
        'arthritis': ['Ibuprofen', 'Naproxen', 'Physical therapy'],
        'lupus': ['Hydroxychloroquine', 'Corticosteroids', 'NSAIDs - Consult physician']
    }
    
    # Check for disease matches in symptoms
    for disease, drug_list in disease_drug_map.items():
        if disease in symptoms:
            drugs.update(drug_list)
    
    # If no disease matched, check for symptom-based recommendations
    if not drugs:
        if 'fever' in symptoms:
            drugs.add('Paracetamol')
        if 'cough' in symptoms:
            drugs.add('Dextromethorphan')
        if 'headache' in symptoms:
            drugs.add('Ibuprofen')

    # Medical history considerations
    if 'diabetes' in history:
        drugs.add('⚠️ Avoid NSAIDs - consult physician for alternatives')
    if 'hypertension' in history:
        drugs.add('⚠️ Check medication interactions - consult physician')
    if 'heart' in history or 'cardiac' in history:
        drugs.add('⚠️ Consult physician before taking any medication')

    if not drugs:
        drugs.add('Consult your physician for a proper diagnosis')

    return jsonify(list(drugs))


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)

import pickle
import os
import difflib

class DDIModel:
    def __init__(self, model_path="ddi_trained_model.pkl", groq_client=None):
        self.groq_client = groq_client
        self.cache = {} # Shared cache for all users
        self.groups = {
            "nsaids": ["ibuprofen", "naproxen", "diclofenac", "aspirin", "celecoxib", "meloxicam", "mefenamic acid"],
            "ace_inhibitors": ["lisinopril", "enalapril", "ramipril", "benazepril", "captopril"],
            "ssris": ["fluoxetine", "sertraline", "paroxetine", "citalopram", "escitalopram"],
            "anticoagulants": ["warfarin", "rivaroxaban", "apixaban", "dabigatran", "heparin"],
            "triptans": ["sumatriptan", "rizatriptan", "zolmitriptan"]
        }

        self.rule_based_interactions = [
            {"group_pair": ["nsaids", "anticoagulants"], "severity": 3, "effect": "Major bleed risk."},
            {"group_pair": ["ssris", "triptans"], "severity": 3, "effect": "Serotonin syndrome risk."},
            {"drugs": ["sildenafil", "nitroglycerin"], "severity": 3, "effect": "Extreme hypotension."},
            {"drugs": ["alcohol", "paracetamol"], "severity": 2, "effect": "Increased liver toxicity risk."}
        ]

        self.ml_descriptions = {}
        self.all_drugs = set()
        if os.path.exists(model_path):
            try:
                with open(model_path, "rb") as f:
                    data = pickle.load(f)
                    self.ml_descriptions = data.get("descriptions", {})
                    # Collect all unique drugs for fuzzy matching
                    for pair in self.ml_descriptions.keys():
                        self.all_drugs.update(pair.split("-"))
                print(f"DDI Lookup data loaded: {len(self.ml_descriptions)} interactions, {len(self.all_drugs)} drugs")
            except Exception as e:
                print(f"Failed to load DDI data: {e}")

    def find_closest_drug(self, name):
        """Fuzzy match for drug names to handle typos."""
        name = name.strip().lower()
        if not self.all_drugs:
            return name
        matches = difflib.get_close_matches(name, list(self.all_drugs), n=1, cutoff=0.8)
        return matches[0] if matches else name

    def predict_with_ai(self, d1, d2):
        """Use Groq AI to reason about drug interactions."""
        if not self.groq_client:
            return None
        
        try:
            prompt = f"Analyze the potential drug-drug interaction between '{d1}' and '{d2}'. Provide a concise one-sentence description of the interaction and a severity level (1=Minor, 2=Moderate, 3=Major). Format: [Severity] Interaction. If no interaction exists, say 'No significant interaction'."
            chat_completion = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
            )
            response = chat_completion.choices[0].message.content.strip()
            
            # Basic parsing of severity if AI follows format
            severity = 2
            if "[3]" in response or "Major" in response: severity = 3
            if "[1]" in response or "Minor" in response: severity = 1
            
            return {
                "pair": [d1, d2],
                "severity": severity,
                "effect": response + " (AI Analysis)"
            }
        except Exception as e:
            print(f"Groq DDI Error: {e}")
            return None

    def get_group(self, drug_name):
        drug_name = drug_name.strip().lower()
        for g, drugs in self.groups.items():
            if drug_name in drugs:
                return g
        return None

    def check_interaction(self, drug_list):
        # 1. Clean and fuzzy-match input names
        checked_list = [self.find_closest_drug(d) for d in drug_list]
        found = []

        for i in range(len(checked_list)):
            for j in range(i + 1, len(checked_list)):
                d1 = checked_list[i]
                d2 = checked_list[j]
                pair_str = "-".join(sorted([d1, d2]))
                
                # ── 1. Check Shared Cache First ──
                if pair_str in self.cache:
                    if self.cache[pair_str]: # If an interaction was found
                        found.append(self.cache[pair_str])
                    continue
                
                res = None
                # ── 2. Check Expert Dataset (Lookup) ──
                if pair_str in self.ml_descriptions:
                    res = {
                        "pair": [d1, d2],
                        "severity": 2, 
                        "effect": self.ml_descriptions[pair_str] + " (Source: Medical Dataset)"
                    }
                
                # ── 3. Check Expert Rule Fallback ──
                if not res:
                    g1 = self.get_group(d1)
                    g2 = self.get_group(d2)
                    res = self._check_rules(d1, d2, g1, g2)
                
                # ── 4. AI Predictive Analysis (Groq) ──
                if not res:
                    ai_res = self.predict_with_ai(d1, d2)
                    if ai_res and "no significant interaction" not in ai_res["effect"].lower():
                        res = ai_res

                # Save to cache (even if None, to avoid re-calculating "no interaction")
                self.cache[pair_str] = res
                if res:
                    found.append(res)
        
        return found

    def _check_rules(self, d1, d2, g1, g2):
        for inter in self.rule_based_interactions:
            if "drugs" in inter:
                if (d1 in inter["drugs"] and d2 in inter["drugs"]):
                    return {"pair": [d1, d2], "severity": inter["severity"], "effect": inter["effect"]}
            if "group_pair" in inter:
                if g1 and g2 and (g1 in inter["group_pair"] and g2 in inter["group_pair"]):
                    return {"pair": [d1, d2], "severity": inter["severity"], "effect": inter["effect"]}
        return None


# Mathematical Algorithm: SARS Recommender System

### Algorithm: Clinical Decision Support & Medication Safety

**Input:** Dataset $D$, user input $X_{user} = (S, A, G, Sev, t, C, P)$  
**Output:** Predicted disease $\hat{y}$, safe medicine set $R$ along with safety measures

---

1) **Preprocess dataset $D$ and encode features:**
   - Map raw symptoms to binary feature space: $X_S \leftarrow MultiLabelBinarizer(D_{symptoms})$
   - Encode categorical inputs: $\hat{A} = LE(A)$, $\hat{G} = LE(G)$
   - Feature Transformation:
     $$X \rightarrow \hat{X}$$

2) **Train models $M = \{M_1, M_2, M_3\}$ and select best model:**
   - $M_1 = \text{Random Forest}$, $M_2 = \text{Naive Bayes}$, $M_3 = \text{K-Nearest Neighbors}$
   - Selection criteria for Disease Predictor:
     $$M^* = \arg \max_{M} (F1-score)$$

3) **Extract and align user inputs:**
   - Case-specific feature vectors:
     $$X_{dp} = (S, Sev, C)$$
     $$X_{dr} = (S, A, G, Sev, t)$$

4) **If user selects Disease Prediction:**
   - **Predict disease:**
     $$\hat{y} = M^*(X_{dp})$$
   - **Retrieve guidelines-based medicines:**
     $$Med = f(\hat{y})$$

5) **Else if user selects Direct Medicine Recommendation:**
   - **Retrieve symptoms-based medicines:**
     $$Med = g(X_{dr})$$
   - **Evaluate chronicity and clinical weight:**
     $$If \ t > T_{threshold} \Rightarrow \text{chronic condition detected}$$
   - **If chronic:**
     - **Predict formal disease:** $\hat{y} = M^*(X_{dp})$
     - **Synchronize recommendation:** $Med = f(\hat{y})$

6) **Perform safety filtering and constraint validation:**
   - **Apply Drug-Drug Interaction (DDI) exclusion:**
     $$Med = Med \setminus DDI(Med, C)$$
   - **Validate physiological safety (Gender/Pregnancy/Age):**
     $$R = Med \cap C_{safe}(G, P, A)$$

7) **Return clinical output:**
   - Final Recommendation Set:
     $$O = (\hat{y}, R)$$

---

**Note:** The algorithm utilizes a hybrid approach: Step 4 prioritizes diagnostic certainty (Disease $\rightarrow$ Meds), while Step 5 prioritizes symptomatic relief with an automated fallback to diagnostics if the duration $t$ exceeds 7 days.

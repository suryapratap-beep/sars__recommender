document.addEventListener("DOMContentLoaded", () => {
    // DASHBOARD & STATE LOGIC
    const isSubscribed = sessionStorage.getItem('isSubscribed') === 'true';
    const userName = sessionStorage.getItem('userName');
    const attemptsCountSpan = document.getElementById('attempts-count');
    const attemptsMessage = document.getElementById('attempts-message');
    const welcomeMessage = document.getElementById('welcome-message');

    if (isSubscribed) {
        if (welcomeMessage) welcomeMessage.textContent = `Welcome, ${userName || 'Subscriber'}!`;
        if (attemptsMessage) attemptsMessage.style.display = 'none';
    } else {
        if (welcomeMessage) welcomeMessage.textContent = `Welcome, Guest!`;
        let attempts = parseInt(sessionStorage.getItem('free_attempts'));
        if (isNaN(attempts)) {
            attempts = 3;
            sessionStorage.setItem('free_attempts', '3');
        }
    }
    
    // Server-sync subscription status for reliability
    async function syncSubscription() {
        try {
            const res = await fetch('/api/is-subscribed');
            const data = await res.json();
            sessionStorage.setItem('isSubscribed', data.is_subscribed);
            const chatbotToggle = document.getElementById('chatbot-toggle');
            if (data.is_subscribed && chatbotToggle) {
                chatbotToggle.style.display = 'block';
            } else if (chatbotToggle) {
                chatbotToggle.style.display = 'none';
            }
        } catch(e) { console.warn("Could not sync sub status", e); }
    }
    syncSubscription();

    function checkAttempts() {
        if (isSubscribed) return true;
        let attempts = parseInt(sessionStorage.getItem('free_attempts') || '0');
        if (attempts <= 0) {
            alert('Your free attempts are exhausted. Please subscribe to continue using SARS_RECOMMENDER.');
            window.location.href = '/'; 
            return false;
        }
        attempts -= 1;
        sessionStorage.setItem('free_attempts', attempts);
        if (attemptsCountSpan) attemptsCountSpan.textContent = attempts;
        return true;
    }

    const homePage = document.getElementById("home-page");
    const diseasePage = document.getElementById("disease-page");
    const medicinePage = document.getElementById("medicine-page");

    const btnDiseasePredictor = document.getElementById("btn-disease-predictor");
    const btnMedicineRecommender = document.getElementById("btn-medicine-recommender");

    // Global Nav
    const navHomeBtn = document.getElementById("nav-home-btn");
    const navSubscribeBtn = document.getElementById("nav-subscribe-btn");

    if (isSubscribed && navSubscribeBtn) {
        navSubscribeBtn.textContent = '✓ Subscribed';
        navSubscribeBtn.style.background = '#64748b';
        navSubscribeBtn.style.cursor = 'default';
        navSubscribeBtn.disabled = true;
    } else if (navSubscribeBtn) {
        navSubscribeBtn.addEventListener("click", () => {
            window.location.href = '/payment'; 
        });
    }

    if (navHomeBtn) {
        navHomeBtn.addEventListener("click", () => {
             window.location.href = '/dashboard'; 
        });
    }

    // Back Home buttons
    const backHomeDiseaseResultBtn = document.getElementById("back-home-disease-result");
    const backHomeMedicineBtn = document.getElementById("back-home-medicine");
    
    // Navigation between pages
    const diseaseToMedicineBtn = document.getElementById("disease-to-medicine");
    const medicineToDiseaseBtn = document.getElementById("medicine-to-disease");

    // Storage for last disease predicted
    let lastPredictedDiseases = [];

    // Page navigation function
    function showPage(page) {
        if(homePage) homePage.style.display = page === 'home' ? 'block' : 'none';
        if(diseasePage) diseasePage.style.display = page === 'disease' ? 'block' : 'none';
        if(medicinePage) medicinePage.style.display = page === 'medicine' ? 'block' : 'none';
    }

    // Process auto-routing from Dashboard Links
    const urlParams = new URLSearchParams(window.location.search);
    const activeTab = urlParams.get('tab');
    if (activeTab === 'disease') {
        showPage('disease');
        // Initial setup for disease step handled intrinsically 
    } else if (activeTab === 'medicine') {
        showPage('medicine');
    } else {
        showPage('home');
    }

    // Home page button handlers
    if(btnDiseasePredictor) btnDiseasePredictor.addEventListener("click", () => {
        showPage('disease');
        showDiseaseStep(0);
    });
    if(btnMedicineRecommender) btnMedicineRecommender.addEventListener("click", () => {
        showPage('medicine');
        showStep(0);
    });

    // Back to home handlers
    if(backHomeDiseaseResultBtn) backHomeDiseaseResultBtn.addEventListener("click", () => window.location.href = "/dashboard");
    if(backHomeMedicineBtn) backHomeMedicineBtn.addEventListener("click", () => window.location.href = "/dashboard");
    
    // Navigation between disease and medicine pages
    if(diseaseToMedicineBtn) diseaseToMedicineBtn.addEventListener("click", () => {
        const diseaseName = lastPredictedDiseases.length > 0 ? lastPredictedDiseases[0] : '';
        const symptomsField = document.getElementById("symptoms");
        if (symptomsField && diseaseName) {
            symptomsField.value = diseaseName;
        }
        showPage('medicine');
        showStep(0);
    });
    
    if(medicineToDiseaseBtn) medicineToDiseaseBtn.addEventListener("click", () => {
        showPage('disease');
        showDiseaseStep(0);
        document.getElementById("diseaseForm")?.reset();
    });

    const checkSafetyBtn = document.getElementById("check-safety-btn");
    if (checkSafetyBtn) {
        checkSafetyBtn.addEventListener("click", () => {
             const drugItems = document.querySelectorAll("#drugList li");
             const medicines = Array.from(drugItems).map(li => li.textContent.trim());
             if (medicines.length > 0) {
                 window.location.href = `/ddi?medicines=${encodeURIComponent(medicines.join(','))}`;
             } else {
                 alert("No medicines to check.");
             }
        });
    }

    // ===== DISEASE PREDICTOR LOGIC =====
    const diseaseSteps = ["disease-symptoms", "disease-duration", "disease-severity", "disease-history", "disease-father", "disease-mother", "disease-medicines"];
    let currentDiseaseStep = 0;

    // Load dataset medicines and symptoms into the UI
    async function loadDatasetData() {
        try {
            const medsResp = await fetch("/get-all-medicines");
            const meds = await medsResp.json();
            const selectMeds = document.getElementById("disease-medicines");
            if (selectMeds && meds.length > 0) {
                selectMeds.innerHTML = '';
                meds.forEach(med => {
                    const option = document.createElement("option");
                    option.value = med;
                    option.textContent = med;
                    selectMeds.appendChild(option);
                });
            }

            const sympResp = await fetch("/get-all-symptoms");
            const symptomsList = await sympResp.json();
            const diseaseDatalist = document.getElementById("symptomsList");
            const medDatalist = document.getElementById("medicineSymptomsListl");

            symptomsList.forEach(symp => {
                if (diseaseDatalist) {
                    const opt1 = document.createElement("option");
                    opt1.value = symp;
                    diseaseDatalist.appendChild(opt1);
                }

                if (medDatalist) {
                    const opt2 = document.createElement("option");
                    opt2.value = symp;
                    medDatalist.appendChild(opt2);
                }
            });
            
        } catch (err) {
            console.error("Failed to load dataset collections", err);
        }
    }
    loadDatasetData();

    function showDiseaseStep(index) {
        if (index < 0 || index >= diseaseSteps.length) return;
        diseaseSteps.forEach((step, i) => {
            const el = document.getElementById(`step-${step}`);
            if (!el) return;
            el.classList.toggle('active', i === index);
        });
        currentDiseaseStep = index;
    }

    showDiseaseStep(0);

    document.querySelectorAll(".disease-next").forEach((btn) => {
        btn.addEventListener("click", () => {
            const parent = btn.closest(".field-step");
            if (!parent) return;
            const stepName = parent.id.replace(/^step-/, "");
            const idx = diseaseSteps.indexOf(stepName);

            const field = document.getElementById(stepName);
            if (field) {
                const tag = field.tagName;
                const value = (field.value || "").toString().trim();
                if ((tag === "TEXTAREA" || tag === "INPUT") && value === "") {
                    alert("Please fill this field before proceeding.");
                    return;
                }
                if (tag === "SELECT" && value === "") {
                    alert("Please select an option before proceeding.");
                    return;
                }
            }
            showDiseaseStep(idx + 1);
        });
    });

    document.querySelectorAll(".disease-back").forEach((btn) => {
        btn.addEventListener("click", () => {
            const parent = btn.closest(".field-step");
            if (!parent) return;
            const stepName = parent.id.replace(/^step-/, "");
            const idx = diseaseSteps.indexOf(stepName);
            if (idx === 0) {
                window.location.href = '/dashboard';
            } else {
                showDiseaseStep(Math.max(0, idx - 1));
            }
        });
    });

    const diseaseForm = document.getElementById("diseaseForm");
    const diseaseLoading = document.getElementById("disease-loading");
    const diseaseResult = document.getElementById("disease-result");
    const diseaseList = document.getElementById("diseaseList");
    const diseaseChatbotRedirect = document.getElementById("disease-chatbot-redirect");
    const medicineChatbotRedirect = document.getElementById("medicine-chatbot-redirect");

    if (diseaseForm) {
        diseaseForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            if (!checkAttempts()) return;

            const symptoms = document.getElementById("disease-symptoms")?.value.trim() || "";
            const duration = document.getElementById("disease-duration")?.value || "";
            const severity = document.getElementById("disease-severity")?.value || "";
            let history = document.getElementById("disease-history")?.value.trim() || "";
            const father_history = document.getElementById("disease-father")?.value.trim() || "";
            const mother_history = document.getElementById("disease-mother")?.value.trim() || "";
            const model_type = document.getElementById("disease-model-type")?.value || "rf";
            
            const medsSelect = document.getElementById("disease-medicines");
            if (medsSelect) {
                const selectedMeds = Array.from(medsSelect.selectedOptions).map(opt => opt.value);
                if (selectedMeds.length > 0) {
                    history += " | Current meds: " + selectedMeds.join(", ");
                }
            }

            if (diseaseLoading) diseaseLoading.classList.remove("hidden");
            if (diseaseResult) { diseaseResult.classList.add("hidden"); diseaseResult.classList.remove('visible'); }
            if (diseaseList) diseaseList.innerHTML = "";
            if (diseaseChatbotRedirect) diseaseChatbotRedirect.classList.add("hidden");

            try {
                const response = await fetch("/predict-disease", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ symptoms, duration, severity, history, father_history, mother_history, model_type })
                });

                if (!response.ok) throw new Error(`Server returned ${response.status}`);

                const data = await response.json();
                const diseases = data.diseases || [];
                lastPredictedDiseases = diseases;

                if (Array.isArray(diseases) && diseases.length > 0) {
                    diseases.forEach(disease => {
                        const li = document.createElement("li");
                        li.textContent = disease;
                        diseaseList.appendChild(li);
                    });
                } else {
                    const li = document.createElement("li");
                    li.textContent = "No matching diseases found.";
                    diseaseList.appendChild(li);
                    if (diseaseChatbotRedirect) diseaseChatbotRedirect.classList.remove("hidden");
                }

                // Check for the specific "No valid symptoms" message from the logic
                if (diseases.length === 1 && diseases[0].includes("No valid symptoms")) {
                    if (diseaseChatbotRedirect) diseaseChatbotRedirect.classList.remove("hidden");
                }

                if (diseaseResult) { 
                    diseaseResult.classList.remove("hidden"); 
                    setTimeout(() => diseaseResult.classList.add('visible'), 20); 
                }
                if (diseaseChatbotRedirect) diseaseChatbotRedirect.classList.remove("hidden");
            } catch (error) {
                alert("Error predicting disease. Please try again.");
                console.error(error);
            } finally {
                if (diseaseLoading) diseaseLoading.classList.add("hidden");
            }
        });
    }

    // ===== MEDICINE RECOMMENDER LOGIC =====
    const steps = ["symptoms", "gender", "age", "pregnancy", "breastfeeding", "history"];
    let currentStep = 0;

    function showStep(index) {
        if (index < 0 || index >= steps.length) return;
        steps.forEach((step, i) => {
            const el = document.getElementById(`step-${step}`);
            if (!el) return;
            el.classList.toggle('active', i === index);
        });
        currentStep = index;
    }
 
    showStep(0);

    document.querySelectorAll(".next").forEach((btn) => {
        btn.addEventListener("click", () => {
            const parent = btn.closest(".field-step");
            if (!parent) return;
            const stepName = parent.id.replace(/^step-/, "");
            const idx = steps.indexOf(stepName);

            const field = document.getElementById(stepName);
            if (field) {
                const tag = field.tagName;
                const value = (field.value || "").toString().trim();
                if ((tag === "TEXTAREA" || tag === "INPUT") && value === "") {
                    alert("Please fill this field before proceeding.");
                    return;
                }
                if (tag === "SELECT" && value === "") {
                    alert("Please select an option before proceeding.");
                    return;
                }
            }
            let nextIdx = idx + 1;
            const genderValue = (document.getElementById("gender")?.value || "").toLowerCase();
            const ageValue = parseInt(document.getElementById("age")?.value || "0");

            if (steps[idx] === "age" && (genderValue !== "female" || ageValue < 18)) {
                nextIdx = steps.indexOf("history");
            }
            showStep(nextIdx);
        });
    });

    document.querySelectorAll(".back").forEach((btn) => {
        btn.addEventListener("click", () => {
            const parent = btn.closest(".field-step");
            if (!parent) return;
            const stepName = parent.id.replace(/^step-/, "");
            const idx = steps.indexOf(stepName);
            if (idx === 0) {
                window.location.href = '/dashboard';
            } else {
                let prevIdx = idx - 1;
                const genderValue = (document.getElementById("gender")?.value || "").toLowerCase();
                const ageValue = parseInt(document.getElementById("age")?.value || "0");

                if (steps[idx] === "history" && (genderValue !== "female" || ageValue < 18)) {
                    prevIdx = steps.indexOf("age");
                }
                showStep(Math.max(0, prevIdx));
            }
        });
    });

    const form = document.getElementById("drugForm");
    const loading = document.getElementById("loading");
    const result = document.getElementById("result");
    const drugList = document.getElementById("drugList");

    if (form) {
        form.addEventListener("submit", async (e) => {
            e.preventDefault();
            if (!checkAttempts()) return;

            if (loading) loading.classList.remove("hidden");
            if (result) { result.classList.add("hidden"); result.classList.remove('visible'); }
            if (drugList) drugList.innerHTML = "";
            if (medicineChatbotRedirect) medicineChatbotRedirect.classList.add("hidden");

            const data = {
                symptoms: document.getElementById("symptoms")?.value.trim() || "",
                gender: document.getElementById("gender")?.value || "",
                age: document.getElementById("age")?.value || "",
                pregnancy: document.getElementById("pregnancy")?.value || "no",
                breastfeeding: document.getElementById("breastfeeding")?.value || "no",
                history: document.getElementById("history")?.value.trim() || ""
            };

            try {
                const response = await fetch("/get-drugs", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(data)
                });

                if (!response.ok) throw new Error(`Server returned ${response.status}`);
                const drugs = await response.json();

                if (Array.isArray(drugs) && drugs.length > 0) {
                    drugs.forEach(drug => {
                        const li = document.createElement("li");
                        li.textContent = drug;
                        drugList.appendChild(li);
                    });
                } else {
                    const li = document.createElement("li");
                    li.textContent = "No drugs found for the given input.";
                    drugList.appendChild(li);
                    if (medicineChatbotRedirect) medicineChatbotRedirect.classList.remove("hidden");
                }

                // Check for specific "No valid symptoms" message from medicine logic
                if (drugs.length === 1 && drugs[0].includes("No valid symptoms")) {
                    if (medicineChatbotRedirect) medicineChatbotRedirect.classList.remove("hidden");
                }

                if (result) { 
                    result.classList.remove("hidden"); 
                    setTimeout(()=>result.classList.add('visible'), 20); 
                }
                if (medicineChatbotRedirect) medicineChatbotRedirect.classList.remove("hidden");
            } catch (error) {
                alert("Error fetching drug list. Please check the backend or open the console for details.");
                console.error(error);
            } finally {
                if (loading) loading.classList.add("hidden");
            }
        });
    }

    // ===== CHATBOT LOGIC =====
    const chatbotToggle = document.getElementById('chatbot-toggle');
    const chatbotWindow = document.getElementById('chatbot-window');
    const chatbotClose = document.getElementById('chatbot-close');
    const chatInput = document.getElementById('chat-input');
    const chatSend = document.getElementById('chat-send');
    const chatMessages = document.getElementById('chat-messages');

    if (isSubscribed && chatbotToggle) {
        chatbotToggle.style.display = 'block';
    }

    if (chatbotToggle) {
        chatbotToggle.addEventListener('click', () => {
            chatbotWindow.style.display = chatbotWindow.style.display === 'flex' ? 'none' : 'flex';
            if (chatbotWindow.style.display === 'flex') chatInput.focus();
        });
    }

    if (chatbotClose) {
        chatbotClose.addEventListener('click', () => {
            chatbotWindow.style.display = 'none';
        });
    }

    function addMessage(text, isUser) {
        const msgDiv = document.createElement('div');
        msgDiv.style.padding = '10px 14px';
        msgDiv.style.maxWidth = '85%';
        msgDiv.style.fontSize = '14px';
        msgDiv.style.lineHeight = '1.4';
        
        if (isUser) {
            msgDiv.style.background = '#6366f1';
            msgDiv.style.color = 'white';
            msgDiv.style.borderRadius = '14px 14px 0 14px';
            msgDiv.style.alignSelf = 'flex-end';
        } else {
            msgDiv.style.background = '#e2e8f0';
            msgDiv.style.color = '#0f172a';
            msgDiv.style.borderRadius = '14px 14px 14px 0';
            msgDiv.style.alignSelf = 'flex-start';
        }
        
        let htmlText = text.replace(/\n/g, '<br>');
        htmlText = htmlText.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        msgDiv.innerHTML = htmlText;
        
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    if (chatSend) {
        chatSend.addEventListener('click', async () => {
            const text = chatInput.value.trim();
            if (!text) return;
            
            addMessage(text, true);
            chatInput.value = '';
            
            const quickActions = document.querySelector(".quick-actions");
            if(quickActions) quickActions.style.display = 'none';

            const typingEl = document.createElement("div");
            typingEl.id = "typing-indicator-ui";
            typingEl.className = "typing-indicator";
            typingEl.innerHTML = "<span></span><span></span><span></span>";
            typingEl.style.alignSelf = "flex-start";
            chatMessages.appendChild(typingEl);
            chatMessages.scrollTop = chatMessages.scrollHeight;

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: text })
                });
                const data = await response.json();
                
                setTimeout(() => {
                    const typed = document.getElementById("typing-indicator-ui");
                    if(typed) typed.remove();
                    addMessage(data.reply, false);
                }, 750);
                
            } catch (err) {
                const typed = document.getElementById("typing-indicator-ui");
                if(typed) typed.remove();
                addMessage('Oops, I am having trouble connecting to the medical server.', false);
            }
        });
    }

    if (chatInput) {
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') chatSend.click();
        });
    }

    // REDIRECT LOGIC
    function sendToChatbot(message) {
        // Store message for full-page chatbot
        sessionStorage.setItem('pending_medical_query', message);
        window.location.href = '/chat';
    }

    if (diseaseChatbotRedirect) {
        diseaseChatbotRedirect.addEventListener("click", () => {
            const sym = document.getElementById("disease-symptoms")?.value || "";
            const dur = document.getElementById("disease-duration")?.value || "";
            const sev = document.getElementById("disease-severity")?.value || "";
            let hist = document.getElementById("disease-history")?.value || "";
            const father = document.getElementById("disease-father")?.value || "";
            const mother = document.getElementById("disease-mother")?.value || "";
            
            const medsSelect = document.getElementById("disease-medicines");
            if (medsSelect) {
                const selectedMeds = Array.from(medsSelect.selectedOptions).map(opt => opt.value);
                if (selectedMeds.length > 0) {
                    hist += " | Currently taking: " + selectedMeds.join(", ");
                }
            }
            
            const msg = `I am experiencing these symptoms: ${sym}. It has been going on for ${dur} and the severity is ${sev}. Medical history: ${hist}. Father's history: ${father}. Mother's history: ${mother}. The disease predictor didn't find a satisfactory match, can you help analyze this?`;
            sendToChatbot(msg);
        });
    }

    if (medicineChatbotRedirect) {
        medicineChatbotRedirect.addEventListener("click", () => {
            const sym = document.getElementById("symptoms")?.value || "";
            const age = document.getElementById("age")?.value || "";
            const gender = document.getElementById("gender")?.value || "";
            const preg = document.getElementById("pregnancy")?.value || "";
            const feed = document.getElementById("breastfeeding")?.value || "";
            const hist = document.getElementById("history")?.value || "";
            
            const msg = `I need medicine recommendations for these symptoms: ${sym}. Age: ${age}, Gender: ${gender}, Pregnant: ${preg}, Breastfeeding: ${feed}. Medical history: ${hist}. The recommender didn't have enough data, what do you suggest?`;
            sendToChatbot(msg);
        });
    }
});

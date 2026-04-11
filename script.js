const UPI_ID = "9398167985@ybl"; // CHANGE TO YOURS
const NAME = "SARS_ACCOUNT";

let selectedAmount = null;
let selectedPlan = null;

const paymentSection = document.getElementById('paymentSection');
const amountText = document.getElementById('amountText');
const status = document.getElementById('status');
const showQRBtn = document.getElementById('showQR');
const planAmountSpan = document.getElementById('planAmount');

// Input validation
function validateInputs() {
    const phoneValid = /^\d{10}$/.test(document.getElementById('phone').value);
    const nameValid = document.getElementById('userName').value.trim().length > 0;
    const emailValid = /^\S+@\S+\.\S+$/.test(document.getElementById('userEmail').value.trim());

    const isValid = phoneValid && nameValid && emailValid;
    document.getElementById('showPlans').disabled = !isValid;

    if (!nameValid) {
        status.textContent = 'Enter your name';
    } else if (!emailValid) {
        status.textContent = 'Enter a valid email address';
    } else if (!phoneValid) {
        status.textContent = 'Enter 10-digit phone number';
    } else {
        status.textContent = '✓ Ready to continue';
    }

    sessionStorage.setItem('phone', document.getElementById('phone').value);
    sessionStorage.setItem('userName', document.getElementById('userName').value);
    sessionStorage.setItem('userEmail', document.getElementById('userEmail').value);
}

document.getElementById('phone').addEventListener('input', validateInputs);
document.getElementById('userName').addEventListener('input', validateInputs);
document.getElementById('userEmail').addEventListener('input', validateInputs);

// Skip Subscription
function skipSubscription() {
    sessionStorage.setItem('isSubscribed', 'false');
    if (!sessionStorage.getItem('free_attempts')) {
        sessionStorage.setItem('free_attempts', '3');
    }
    // Retain name if entered, otherwise Guest
    if (!document.getElementById('userName').value.trim()) {
        sessionStorage.removeItem('userName');
    }
    window.location.href = '/dashboard';
}

// Show plans
function showPlans() {
    document.getElementById('plans').classList.remove('hidden');
    status.textContent = 'Select plan → Pay → QR';
    sessionStorage.setItem('step', 'plans');
}

// Plan select
document.querySelectorAll('.plan-card').forEach(card => {
    card.onclick = () => {
        document.querySelectorAll('.plan-card').forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');
        selectedAmount = parseInt(card.dataset.amount);
        selectedPlan = card.dataset.plan;
        showQRBtn.disabled = false;
        planAmountSpan.textContent = selectedAmount;
        status.textContent = `${selectedPlan} selected`;

        sessionStorage.setItem('selectedPlan', selectedPlan);
        sessionStorage.setItem('selectedAmount', selectedAmount);
    };
});

// Pay → Show QR + PNG
function showQR(isRestore = false) {
    if (!selectedAmount) return status.textContent = '❌ Select plan';

    const phone = document.getElementById('phone').value;
    const userName = document.getElementById('userName').value.trim();
    const userEmail = document.getElementById('userEmail').value.trim();

    // DYNAMIC UPI URL - YOUR ACCOUNT + PLAN AMOUNT
    const upiUrl = `upi://pay?pa=${UPI_ID}&pn=${NAME}&am=${selectedAmount}&cu=INR&tn=AI-Sub-${selectedPlan}-${phone}`;

    if (!isRestore) {
        // Store Supabase
        fetch('/store-sub', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: userName, email: userEmail, phone, plan: selectedPlan, amount: selectedAmount, status: 'pending' })
        });
        sessionStorage.setItem('step', 'payment');
        sessionStorage.setItem('paymentTime', Date.now());
    }

    paymentSection.classList.remove('hidden');
    paymentSection.scrollIntoView();
    amountText.innerHTML = `₹${selectedAmount} → ${NAME}<br><small>${UPI_ID}</small>`;

    // 5min timer
    let timeLeft = 300; // 5 minutes

    if (isRestore) {
        const pTime = parseInt(sessionStorage.getItem('paymentTime') || Date.now());
        timeLeft = 300 - Math.floor((Date.now() - pTime) / 1000);
    }
    status.innerHTML = `⏱️ Pay within <strong>${timeLeft}s</strong> - Scan QR`;

    const timer = setInterval(() => {
        timeLeft--;
        status.innerHTML = `⏱️ Pay within <strong>${timeLeft}s</strong> - Scan QR`;

        if (timeLeft <= 0) {
            clearInterval(timer);
            status.innerHTML = '⏰ Expired';
            return;
        }

        // Poll every 3s (not every 1s)
        if (timeLeft % 3 === 0) {  // Every 3 ticks
            fetch(`/check-status/${phone}`)
                .then(res => res.json())
                .then(data => {
                    if (data.paid) {
                        clearInterval(timer);
                        status.innerHTML = '✅ <strong>Payment CONFIRMED!</strong><br>Subscription active.';
                        showQRBtn.innerHTML = 'Go to Home';
                        showQRBtn.disabled = false;
                        showQRBtn.onclick = () => {
                            const uName = sessionStorage.getItem('userName');
                            sessionStorage.clear();
                            if (uName) sessionStorage.setItem('userName', uName);
                            sessionStorage.setItem('isSubscribed', 'true');
                            window.location.href = '/dashboard';
                        };
                    }
                });
        }
    }, 1000); // 1s timer tick

    showQRBtn.disabled = true;
    showQRBtn.innerHTML = '⏳ Waiting...';
}

// RESTORE STATE ON REFRESH
window.onload = () => {
    if (sessionStorage.getItem('userName')) {
        document.getElementById('userName').value = sessionStorage.getItem('userName');
    }
    if (sessionStorage.getItem('userEmail')) {
        document.getElementById('userEmail').value = sessionStorage.getItem('userEmail');
    }
    if (sessionStorage.getItem('phone')) {
        document.getElementById('phone').value = sessionStorage.getItem('phone');
        validateInputs();
    }

    const step = sessionStorage.getItem('step');
    if (step === 'plans' || step === 'payment') {
        showPlans();
        const plan = sessionStorage.getItem('selectedPlan');
        if (plan) {
            const card = document.querySelector(`.plan-card[data-plan="${plan}"]`);
            if (card) card.click();
        }
    }

    if (step === 'payment') {
        showQR(true);
    }
};
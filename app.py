from flask import Flask, request, jsonify, send_from_directory, render_template, redirect, session, url_for
from flask_cors import CORS
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from supabase import create_client
import sqlite3
import random
import time
import os
import sys
import warnings
import io
import base64
import string
import re
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
from disease_predictor import DiseasePredictor
from dg_2 import MedicineRecommender
from ddi_model import DDIModel
from groq import Groq

# Initialize Groq Client
client = Groq(api_key=os.environ.get("GROQ_API_KEY", "gsk_placeholder_key"))

warnings.filterwarnings('ignore', category=UserWarning)

# ----- Global ML Init & Supabase -----
try:
    disease_desc_df = pd.read_csv('disease_description.csv')
    disease_dict = {str(row['disease']).lower(): str(
        row['description']) for _, row in disease_desc_df.iterrows()}
except Exception as e:
    disease_dict = {}

try:
    disease_model = DiseasePredictor()
    medicine_model = MedicineRecommender()
    ddi_model = DDIModel(groq_client=client)
except Exception as e:
    disease_model = None
    medicine_model = None
    ddi_model = None

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://lzlilmxegsrmnqcxlszs.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "placeholder_supabase_key")
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except:
    supabase = None

# ----- Flask Init -----
app = Flask(__name__, static_folder='.', static_url_path='')
app.secret_key = "securekey123"
CORS(app)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'suryapratapsp292@gmail.com'
app.config['MAIL_PASSWORD'] = 'okax zdhx enqn wliz'
mail = Mail(app)

@app.route('/set_language', methods=['POST'])
def set_language():
    data = request.json
    if not data or 'lang' not in data:
        return jsonify({"status": "error", "message": "No language provided"}), 400
    
    session['lang'] = data['lang']
    return jsonify({"status": "success", "language": data['lang']})

# ----- Auth Helpers -----


def get_db():
    # check_same_thread=False allows multiple users to access the DB simultaneously
    return sqlite3.connect("users.db", check_same_thread=False)

def is_subscribed_user():
    email = session.get("email")
    if not email: return False
    try:
        # Check by email in Supabase
        data = supabase.table('subscriptions_requests').select('status').eq('email', email).execute().data or []
        return any(str(row.get('status')).strip().lower() in ['paid', 'successful', 'success', 'completed'] for row in data)
    except:
        return False

# Simple in-memory cache to prevent overloading AI
ai_cache = {}


def is_valid_password(password):
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[!@#$%^&*]", password):
        return False, "Password must contain at least one special character (!@#$%^&*)."
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one number."
    return True, ""


def generate_strong_password(length=8):
    uppercase = random.choice(string.ascii_uppercase)
    digit = random.choice(string.digits)
    special = random.choice("!@#$%^&*")
    remaining = ''.join(random.choice(
        string.ascii_letters + string.digits + "!@#$%^&*") for _ in range(length - 3))
    password_list = list(uppercase + digit + special + remaining)
    random.shuffle(password_list)
    return ''.join(password_list)


IMAGE_POOL = [
    {"url": "https://picsum.photos/id/1011/400/300", "label": "river"},
    {"url": "https://picsum.photos/id/1015/400/300", "label": "river"},
    {"url": "https://picsum.photos/id/1020/400/300", "label": "bear"},
    {"url": "https://picsum.photos/id/1043/400/300", "label": "trees"},
    {"url": "https://picsum.photos/id/1024/400/300", "label": "eagle"},
    {"url": "https://picsum.photos/id/1035/400/300", "label": "waterfall"},
    {"url": "https://picsum.photos/id/1084/400/300", "label": "walrus"},
    {"url": "https://picsum.photos/id/237/400/300",  "label": "dog"}
]


def generate_captcha():
    letters = string.ascii_uppercase + string.digits
    captcha_text = ''.join(random.choices(letters, k=5))
    img = Image.new('RGB', (150, 50), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    draw.text((20, 10), captcha_text, font=font, fill=(0, 0, 0))
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return captcha_text, base64.b64encode(buffer.getvalue()).decode()


def generate_image_captcha():
    captcha_label = random.choice(
        ["river", "bear", "eagle", "waterfall", "trees", "walrus", "dog"])
    matching = [img for img in IMAGE_POOL if img["label"] == captcha_label]
    non_matching = [img for img in IMAGE_POOL if img["label"] != captcha_label]
    selected_images = random.sample(matching, 1) if matching else []
    remaining = random.sample(non_matching, min(5, len(non_matching)))
    final_images = selected_images + remaining
    random.shuffle(final_images)
    return captcha_label, final_images


def is_valid_email(email):
    return re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.(com|in|org|net)$", email)


@app.context_processor
def inject_user():
    if "email" in session:
        try:
            db = get_db()
            cur = db.cursor()
            cur.execute("SELECT profile_pic FROM users WHERE email=?",
                        (session["email"],))
            user = cur.fetchone()
            db.close()
            return dict(profile_pic=user[0] if user else None)
        except:
            pass
    return dict(profile_pic=None)


# ----- ROUTES -----
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form['email']
        plain_password = request.form['password']
        user_captcha = request.form['captcha']
        real_captcha = session.get('captcha')

        if not is_valid_email(email):
            captcha_text, captcha_img = generate_captcha()
            session['captcha'] = captcha_text
            return render_template("login.html", captcha=captcha_img, error="Invalid email format!")

        if user_captcha != real_captcha:
            captcha_text, captcha_img = generate_captcha()
            session['captcha'] = captcha_text
            return render_template("login.html", captcha=captcha_img, error="Invalid CAPTCHA")

        valid, message = is_valid_password(plain_password)
        if not valid:
            captcha_text, captcha_img = generate_captcha()
            session['captcha'] = captcha_text
            return render_template("login.html", captcha=captcha_img, error=message)

        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM users WHERE email=?", (email,))
        user = cur.fetchone()
        db.close()

        if user and check_password_hash(user[3], plain_password):
            otp = random.randint(100000, 999999)
            session['otp'] = otp
            session['email'] = email
            session['username'] = user[1]
            session['otp_time'] = time.time()
            msg = Message(
                "Your OTP", sender=app.config['MAIL_USERNAME'], recipients=[email])
            msg.body = f"Your OTP is {otp} , It is valid for 50 seconds."
            mail.send(msg)
            return redirect("/otp")

        captcha_text, captcha_img = generate_captcha()
        session['captcha'] = captcha_text
        return render_template("login.html", captcha=captcha_img, error="Invalid email or password.")

    captcha_text, captcha_img = generate_captcha()
    session['captcha'] = captcha_text
    return render_template("login.html", captcha=captcha_img)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form['username']
        email = request.form['email']
        plain_password = request.form['password']

        if not is_valid_email(email):
            return render_template("register.html", error="Invalid email format!")

        valid, message = is_valid_password(plain_password)
        if not valid:
            return render_template("register.html", error=message)

        if not session.get("captcha_verified"):
            return "Please complete Image CAPTCHA first."

        hashed_password = generate_password_hash(plain_password)
        db = get_db()
        cur = db.cursor()
        try:
            cur.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                        (username, email, hashed_password))
            db.commit()
        except:
            pass
        db.close()
        session["captcha_verified"] = False
        return redirect("/")
    return render_template("register.html")


@app.route("/forgot", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form['email']
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM users WHERE email=?", (email,))
        user = cur.fetchone()
        if user:
            new_password = generate_strong_password()
            hashed_password = generate_password_hash(new_password)
            cur.execute("UPDATE users SET password=? WHERE email=?",
                        (hashed_password, email))
            db.commit()
            db.close()
            msg = Message(
                "Password Reset", sender=app.config['MAIL_USERNAME'], recipients=[email])
            msg.body = f"Your password has been reset successfully.\n\nNew Password: {new_password}\n\nPlease login and change your password."
            mail.send(msg)
            return "New password has been sent to your email."
        return "Email not found"
    return render_template("forgot.html")


@app.route("/otp", methods=["GET", "POST"])
def otp():
    if request.method == "POST":
        user_otp = request.form['otp']
        saved_otp = session.get("otp")
        otp_time = session.get("otp_time", 0)
        if time.time() - otp_time > 50:
            return render_template("otp.html", error="OTP expired.", expired=True)
        if str(user_otp).strip() == str(saved_otp).strip():
            # Check subscription on login
            session['is_subscribed'] = is_subscribed_user()
            return redirect("/dashboard")
        else:
            return render_template("otp.html", error="Invalid OTP")
    return render_template("otp.html")


@app.route("/resend_otp", methods=["POST"])
def resend_otp():
    email = session.get('email')
    if not email:
        return redirect("/")

    otp_code = random.randint(100000, 999999)
    session['otp'] = otp_code
    session['otp_time'] = time.time()

    msg = Message(
        "Your OTP", sender=app.config['MAIL_USERNAME'], recipients=[email])
    msg.body = f"Your new OTP is {otp_code} , It is valid for 50 seconds."
    mail.send(msg)

    return render_template("otp.html", success="A new OTP has been sent!")


@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect("/")
    return render_template("dashboard.html", username=session["username"], email=session["email"], is_subscribed=session.get('is_subscribed', False))


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/reload_captcha")
def reload_captcha():
    captcha_text, captcha_img = generate_captcha()
    session['captcha'] = captcha_text
    return {"captcha": captcha_img}


@app.route("/image_captcha", methods=["GET", "POST"])
def image_captcha():
    if request.method == "POST":
        selected = request.form.getlist("captcha_images")
        label = session.get("captcha_label")
        images = session.get("captcha_images")
        if not label or not images:
            return redirect("/image_captcha")
        correct = [img["url"] for img in images if img["label"] == label]
        if selected and all(url in correct for url in selected):
            session["captcha_verified"] = True
            return "<script>alert('Image CAPTCHA verified successfully!'); window.close();</script>"
        return redirect("/image_captcha")
    captcha_label, images = generate_image_captcha()
    session["captcha_label"] = captcha_label
    session["captcha_images"] = images
    session["captcha_verified"] = False
    return render_template("image_captcha.html", captcha_label=captcha_label, images=images)

# Routes linking to main app AI logic seamlessly.


@app.route("/predict_disease", methods=["GET", "POST"])
def disease_predictor():
    return redirect('/ai-assistant?tab=disease')


@app.route("/medicine_recommend")
def recommend_medicine():
    return redirect('/ai-assistant?tab=medicine')


@app.route("/health-records")
def health_records():
    if "username" not in session:
        return redirect("/")
    return render_template("health-records.html", username=session["username"], email=session["email"])


@app.route("/settings")
def settings():
    if "username" not in session:
        return redirect("/")
    return render_template("settings.html", username=session["username"], email=session["email"])


@app.route("/medicine")
def medicine():
    if "username" not in session:
        return redirect("/")
    return render_template("medicine.html", username=session["username"], email=session["email"])


@app.route("/ddi")
def ddi():
    if "username" not in session:
        return redirect("/")
    return render_template("ddi.html", username=session["username"], email=session["email"])


@app.route("/chat")
def chatbot():
    if "username" not in session:
        return redirect("/")
    if not is_subscribed_user():
        return render_template("subscription_required.html", username=session["username"], email=session["email"])
    return render_template("chatbot.html", username=session["username"], email=session["email"])


@app.route("/api/chat", methods=["POST"])
def chat_api():
    if not is_subscribed_user():
        return jsonify({"response": "This is a premium feature. Please subscribe to use the AI medical assistant."})
    
    data = request.get_json() or {}
    user_msg = data.get("message", "")
    
    # Check cache first to avoid overloading Groq
    cache_key = f"chat_{user_msg}"
    if cache_key in ai_cache:
        return jsonify({"response": ai_cache[cache_key]})

    try:
        # Calling Groq with Llama 3
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional medical assistant. Provide clear, empathetic health advice but always include a disclaimer to consult a doctor."
                },
                {
                    "role": "user",
                    "content": user_msg,
                }
            ],
            model="llama-3.3-70b-versatile",
        )
        response = chat_completion.choices[0].message.content
        ai_cache[cache_key] = response # Save to cache
        return jsonify({"response": response})
    except Exception as e:
        print(f"Groq Error: {e}")
        return jsonify({"response": "I'm having trouble connecting to Groq AI. Please check your API key!"})



@app.route("/api/ddi", methods=["POST"])
def run_ddi():
    data = request.get_json() or {}
    medicines = data.get('medicines', [])
    if not ddi_model:
        return jsonify([])
    try:
        results = ddi_model.check_interaction(medicines)
        return jsonify(results)
    except:
        return jsonify([])

# ----- AI Assistant SPA routes -----


@app.route('/payment')
def payment_page():
    return app.send_static_file('index.html')


@app.route('/ai-assistant')
def ai_assistant():
    return app.send_static_file('frontend_files/index.html')


# Static file resolver (matches standard static_folder behavior + arbitrary paths used before)
@app.route('/<path:path>')
def serve_static(path):
    return app.send_static_file(path)


# ----- APIs -----
@app.route('/predict-disease', methods=['POST'])
def run_predict_disease():
    data = request.get_json() or {}
    symptoms, severity, duration, history = data.get('symptoms', '').lower(), data.get(
        'severity', '').lower(), data.get('duration', '').lower(), data.get('history', '').lower()
    if not disease_model:
        return jsonify({'diseases': ['Model not initialized']})
    try:
        return jsonify({'diseases': [disease_model.predict(symptoms, severity, duration, history)]})
    except:
        return jsonify({'diseases': ['Error processing prediction']})


@app.route('/get-drugs', methods=['POST'])
def run_get_drugs():
    data = request.get_json() or {}
    symptoms, gender = data.get(
        'symptoms', '').lower(), data.get('gender', '').lower()
    age = int(data.get('age', 0)) if str(data.get('age')).isdigit() else 0
    if not medicine_model:
        return jsonify(['Model not initialized'])
    try:
        lines = [line.strip() for line in medicine_model.recommend(
            symptoms, age, gender, "no", "no", "1 day").split('\n') if line.strip()]
        return jsonify(lines if lines else ["No medication found"])
    except:
        return jsonify(["Error retrieving medication recommendation"])


@app.route('/chat', methods=['POST'])
def run_chat():
    data = request.get_json() or {}
    message = data.get('message', '').lower()
    # Add simple interactive fallback matching our specific AI upgrades
    reply = "I am your SARS_RECOMMENDER Assistant. I can provide descriptions and general precautions for diseases. Try asking me about 'Malaria', 'Dengue Fever', or 'Typhoid'."
    for disease, desc in disease_dict.items():
        if disease in message:
            reply = f"**{disease.title()}**\n{desc}\n\n*Health Guidelines:*\n• Rest and properly hydrate.\n• Maintain solid hygiene practices.\n• Consult a real healthcare professional immediately if symptoms get worse!"
            break
    return jsonify({'reply': reply})


@app.route('/get-all-medicines', methods=['GET'])
def run_get_all_medicines():
    try:
        return jsonify(sorted(list(set(pd.read_csv('demo6.csv')['Medicine'].dropna().astype(str).tolist()))))
    except:
        return jsonify([])


@app.route('/get-all-symptoms', methods=['GET'])
def run_get_all_symptoms():
    try:
        df1 = pd.read_csv('disease_symptoms.csv')
        symptoms = set([x for col in df1.columns if col.startswith('symptoms')
                       for x in df1[col].dropna().astype(str).str.strip().tolist()])
        try:
            df2 = pd.read_csv('demo6.csv')
            if 'Symptom' in df2.columns:
                symptoms.update(df2['Symptom'].dropna().astype(
                    str).str.strip().tolist())
        except:
            pass
        return jsonify(sorted(list(filter(None, symptoms))))
    except:
        return jsonify([])


@app.route('/store-sub', methods=['POST'])
def store_sub():
    data = request.json
    try:
        if supabase.table('subscriptions_requests').select('phone').eq('phone', data.get('phone')).execute().data:
            supabase.table('subscriptions_requests').update(
                data).eq('phone', data.get('phone')).execute()
        else:
            supabase.table('subscriptions_requests').insert(data).execute()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/check-status/<phone>')
def check_status(phone):
    try:
        data = supabase.table('subscriptions_requests').select(
            'status').eq('phone', phone).execute().data or []
        paid = any(str(row.get('status')).strip().lower() in [
                   'paid', 'successful', 'success', 'completed'] for row in data)
        return jsonify({'paid': paid})
    except:
        return jsonify({'paid': False})


@app.route('/api/is-subscribed')
def check_my_sub_status():
    if "email" not in session:
        return jsonify({'is_subscribed': False})
    return jsonify({'is_subscribed': is_subscribed_user()})


if __name__ == '__main__':
    # threaded=True allows multiple simultaneous users
    app.run(debug=True, port=5000, threaded=True)

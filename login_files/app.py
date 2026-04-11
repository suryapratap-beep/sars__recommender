from flask import Flask, render_template, request, redirect, session,url_for
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, random, time
from PIL import Image, ImageDraw, ImageFont
import io
import base64
import string
import random

import re


# PASSWORD POLICY
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



# GENERATE CAPTCHA (EVERY LOAD)
IMAGE_POOL = [
    {"url": "https://picsum.photos/id/1011/400/300", "label": "river"},
    {"url": "https://picsum.photos/id/1015/400/300", "label": "river"},
    {"url": "https://picsum.photos/id/1020/400/300", "label": "bear"},
    {"url": "https://picsum.photos/id/1043/400/300", "label": "trees"},
    {"url": "https://picsum.photos/id/1024/400/300", "label": "eagle"},
    {"url": "https://picsum.photos/id/1035/400/300", "label": "waterfall"},
    {"url": "https://picsum.photos/id/1035/400/300", "label": "walrus"},
    {"url": "https://picsum.photos/id/1084/400/300", "label": "walrus"},
    {"url": "https://picsum.photos/id/1024/400/300", "label": "dog"},
    {"url": "https://picsum.photos/id/1062/400/300", "label": "dog"},
    {"url": "https://picsum.photos/id/237/400/300",  "label": "dog"},
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
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return captcha_text, img_str

def generate_strong_password(length=8):
    if length < 6:
        length = 6

    uppercase = random.choice(string.ascii_uppercase)
    digit = random.choice(string.digits)
    special = random.choice("!@#$%^&*")
    remaining = ''.join(random.choice(string.ascii_letters + string.digits + "!@#$%^&*")
                        for _ in range(length - 3))

    password_list = list(uppercase + digit + special + remaining)
    random.shuffle(password_list)

    return ''.join(password_list)

def generate_image_captcha():

    captcha_label = random.choice(["river", "bear", "eagle", "waterfall","trees","walrus","dog"])

    matching = [img for img in IMAGE_POOL if img["label"] == captcha_label]

    unique_pool = {img["url"]: img for img in IMAGE_POOL}.values()

    non_matching = [img for img in IMAGE_POOL if img["label"] != captcha_label]

    selected_images = random.sample(matching, 1)

    remaining = random.sample(non_matching, 5)

    final_images = selected_images + remaining
    random.shuffle(final_images)

    return captcha_label, final_images

def is_valid_email(email):
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.(com|in|org|net)$"
    return re.match(pattern, email)


app = Flask(__name__)
app.secret_key = "securekey123"

# ---------------- EMAIL CONFIG ----------------
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'suryapratapsp292@gmail.com'
app.config['MAIL_PASSWORD'] = 'okax zdhx enqn wliz'

mail = Mail(app)

# ---------------- DATABASE ----------------
def get_db():
    return sqlite3.connect("users.db")

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form['username']
        email = request.form['email']
        plain_password = request.form['password']

        # EMAIL POLICY CHECK (PUT HERE)
        if not is_valid_email(email):
            return render_template("register.html", error="Invalid email format! Only .com, .in, .org, .net allowed.")


        #  PASSWORD POLICY CHECK
        valid, message = is_valid_password(plain_password)
        if not valid:
            return render_template(
                "register.html",
                error=message
            )

        # IMAGE CAPTCHA CHECK
        if not session.get("captcha_verified"):
            return "Please complete Image CAPTCHA first."

        # HASH PASSWORD AFTER VALIDATION
        hashed_password = generate_password_hash(plain_password)

        db = get_db()
        cur = db.cursor()
        cur.execute(
            "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
            (username,email, hashed_password)
        )
        db.commit()
        db.close()

        # reset captcha flag after successful registration
        session["captcha_verified"] = False

        return redirect("/")

    return render_template("register.html")

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form['email']
        plain_password = request.form['password']
        user_captcha = request.form['captcha']
        real_captcha = session.get('captcha')

        #  EMAIL POLICY CHECK 
        if not is_valid_email(email):
            captcha_text, captcha_img = generate_captcha()
            session['captcha'] = captcha_text
            return render_template("login.html", captcha=captcha_img, error="Invalid email format!")

        # CAPTCHA CHECK
        if user_captcha != real_captcha:
            captcha_text, captcha_img = generate_captcha()
            session['captcha'] = captcha_text
            return render_template(
                "login.html",
                captcha=captcha_img,
                error="Invalid CAPTCHA"
            )

        # PASSWORD POLICY CHECK (NEW)
        valid, message = is_valid_password(plain_password)
        if not valid:
            captcha_text, captcha_img = generate_captcha()
            session['captcha'] = captcha_text
            return render_template(
                "login.html",
                captcha=captcha_img,
                error=message
            )

        # DATABASE CHECK
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
                "Your OTP",
                sender=app.config['MAIL_USERNAME'],
                recipients=[email]
            )
            msg.body = f"Your OTP is {otp} , It is valid for 50 seconds."
            mail.send(msg)

            return redirect("/otp")

        # credentials wrong but format OK
        captcha_text, captcha_img = generate_captcha()
        session['captcha'] = captcha_text
        return render_template(
            "login.html",
            captcha=captcha_img,
            error="Invalid email or password."
        )

    # ---------- GET REQUEST ----------
    captcha_text, captcha_img = generate_captcha()
    session['captcha'] = captcha_text

    return render_template("login.html", captcha=captcha_img)

#------------forgot password-----------
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

            msg = Message("Password Reset",
                          sender=app.config['MAIL_USERNAME'],
                          recipients=[email])
            msg.body = f"""
Your password has been reset successfully.

New Password: {new_password}

Please login and change your password.
"""
            mail.send(msg)

            return "New password has been sent to your email."

        return "Email not found"

    return render_template("forgot.html")
# ---------------- OTP ----------------
@app.route("/otp", methods=["GET", "POST"])
def otp():
    if request.method == "POST":
        user_otp = request.form['otp']
        saved_otp = session.get("otp")
        otp_time = session.get("otp_time")

        if time.time() - otp_time > 50:
            return "OTP expired. Login again."

        if int(user_otp) == saved_otp:
            return redirect("/dashboard")
        else:
            return "Invalid OTP"

    return render_template("otp.html")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect("/")   

    return render_template(
        "dashboard.html",
        username=session["username"],
        email=session["email"]
    )

#------------medicine----------------

@app.route("/medicine")
def medicine():
    if "username" not in session:
        return redirect("/")
    return render_template("medicine.html", username=session["username"], email=session["email"])


#------------health record--------------

@app.route("/health-records")
def health_records():
    if "username" not in session:
        return redirect("/")
    return render_template("health-records.html", username=session["username"], email=session["email"])


#-------------settings---------------

@app.route("/settings")
def settings():
    if "username" not in session:
        return redirect("/")
    return render_template("settings.html", username=session["username"], email=session["email"])

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

#-------------reload captcha-------------
@app.route("/reload_captcha")
def reload_captcha():
    captcha_text, captcha_img = generate_captcha()
    session['captcha'] = captcha_text
    return {"captcha": captcha_img}
#-----------image captcha-----------------
@app.route("/image_captcha", methods=["GET", "POST"])
def image_captcha():

    # ---------- POST: VERIFY CAPTCHA ----------
    if request.method == "POST":
        selected = request.form.getlist("captcha_images")
        label = session.get("captcha_label")
        images = session.get("captcha_images")

        if not label or not images:
            return redirect("/image_captcha")

        correct = [img["url"] for img in images if img["label"] == label]

        if selected and all(url in correct for url in selected):
            session["captcha_verified"] = True
            return """
                <script>
                    alert("Image CAPTCHA verified successfully!");
                    window.close();
                </script>
            """
        else:
            return redirect("/image_captcha")

    # ---------- GET: GENERATE CAPTCHA ----------
    captcha_label, images = generate_image_captcha()

    session["captcha_label"] = captcha_label
    session["captcha_images"] = images
    session["captcha_verified"] = False

    return render_template(
        "image_captcha.html",
        captcha_label=captcha_label,
        images=images
    )

#-------- profile pic -------------
@app.context_processor
def inject_user():
    if "email" in session:
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT profile_pic FROM users WHERE email=?", (session["email"],))
        user = cur.fetchone()
        db.close()
        return dict(profile_pic=user[0])
    return dict(profile_pic=None)


#----------------disease prediction----------------
@app.route("/predict_disease", methods=["GET","POST"])
def disease_predictor():

    if request.method == "POST":

        symptoms = request.form['symptoms']
        image = request.files.get('image')

        # Here your ML model will predict disease
        predicted_disease = "Flu"   # temporary example

        # save disease in session
        session["predicted_disease"] = predicted_disease

        # redirect to medicine recommender
        return redirect(url_for("recommend_medicine"))

    return render_template("predict_disease.html")

#---------------- medicine recommender ----------------
@app.route("/medicine_recommend")
def recommend_medicine():

    disease = session.get("predicted_disease")

    medicines = []

    if disease == "Flu":
        medicines = ["Paracetamol", "Ibuprofen", "Vitamin C"]

    elif disease == "Allergy":
        medicines = ["Cetirizine", "Loratadine"]

    return render_template(
        "medicine_recommend.html",
        disease=disease,
        medicines=medicines
    )

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
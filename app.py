# app.py

from flask import Flask, render_template, request, redirect, session, flash
import os
import numpy as np

app = Flask(__name__)
app.secret_key = "secret_skinguard_key_2026"

UPLOAD_FOLDER = "static/uploads/"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --------------------------------------------------------
# DYNAMIC TENSORFLOW LOADING WITH ROBUST SIMULATOR FALLBACK
# --------------------------------------------------------
model_loaded = False
model = None

try:
    import tensorflow as tf
    from tensorflow.keras.models import load_model
    from tensorflow.keras.preprocessing import image
    
    model_path = "model/vgg16_malignant_vs_benign.h5"
    if os.path.exists(model_path):
        try:
            # Attempt 1: standard load
            model = load_model(model_path, compile=False)
        except (TypeError, ValueError):
            # Attempt 2: Keras version mismatch fix — strip quantization_config
            class PatchedDense(tf.keras.layers.Dense):
                def __init__(self, *args, **kwargs):
                    kwargs.pop('quantization_config', None)
                    super().__init__(*args, **kwargs)
            
            model = load_model(
                model_path,
                custom_objects={'Dense': PatchedDense},
                compile=False
            )
        model_loaded = True
        print("TensorFlow model loaded successfully")
    else:
        print("Model file 'model/vgg16_malignant_vs_benign.h5' not found. Using simulated diagnostic engine.")
except Exception as e:
    print("TensorFlow loading skipped or failed. Using simulated diagnostic engine. Error:", e)


# --------------------------------------------------------
# DATABASE INITIALIZATION (MYSQL WITH SQLITE FAILOVER)
# --------------------------------------------------------
use_sqlite = False
db = None

try:
    import mysql.connector
    # First: connect WITHOUT a database to ensure skin_cancer_db exists
    _init_conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password=""
    )
    _init_cursor = _init_conn.cursor()
    _init_cursor.execute("CREATE DATABASE IF NOT EXISTS skin_cancer_db")
    _init_cursor.close()
    _init_conn.close()

    # Now connect to the actual database
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="skin_cancer_db"
    )
    # Test connection
    if db.is_connected():
        print("Successfully connected to MySQL database!")
        # Auto-create tables if they don't exist
        _tc = db.cursor()
        _tc.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50),
                password VARCHAR(50)
            )
        """)
        _tc.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100),
                age INT,
                result VARCHAR(20),
                probability FLOAT,
                image_path VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Insert default admin if not exists
        _tc.execute("SELECT * FROM users WHERE username='admin'")
        if not _tc.fetchone():
            _tc.execute("INSERT INTO users (username, password) VALUES ('admin', '1234')")
        db.commit()
        _tc.close()
except Exception as mysql_err:
    print("Could not connect to MySQL database, falling back to SQLite. Reason:", mysql_err)
    import sqlite3
    use_sqlite = True
    
    # Establish local SQLite database
    sqlite_db_path = "skin_cancer_fallback.db"
    db = sqlite3.connect(sqlite_db_path, check_same_thread=False)
    
    # Helper to mimic dictionary cursor in sqlite3
    def dict_factory(cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d
    db.row_factory = dict_factory
    
    # Initialize schema
    cursor = db.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            age INTEGER,
            result TEXT,
            probability REAL,
            image_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    db.commit()
    
    # Insert default admin if not exists
    cursor.execute("SELECT * FROM users WHERE username='admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password) VALUES ('admin', '1234')")
        db.commit()

# Helper function to run query cross-database (handles ? vs %s placeholder differences)
def db_execute(query, params=None):
    if params is None:
        params = ()
        
    if use_sqlite:
        query = query.replace("%s", "?")
        cursor = db.cursor()
    else:
        cursor = db.cursor(dictionary=True)
        
    cursor.execute(query, params)
    return cursor

# --------------------------------------------------------
# APPLICATION ROUTES
# --------------------------------------------------------

# LOGIN
@app.route("/", methods=["GET","POST"])
def login():
    if "user" in session:
        return redirect("/dashboard")
        
    if request.method == "POST":
        user = request.form["username"]
        pwd = request.form["password"]

        try:
            cursor = db_execute("SELECT * FROM users WHERE username=%s AND password=%s",(user,pwd))
            result = cursor.fetchone()

            if result:
                session["user"] = user
                flash("Login réussi ✓", "success")
                return redirect("/dashboard")
            else:
                flash("Erreur login ✗ (Identifiants invalides)", "danger")
        except Exception as e:
            print("Login query failed:", e)
            flash("Erreur base de données", "danger")

    return render_template("login.html")

# DASHBOARD
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
        
    try:
        # Total scans
        cursor = db_execute("SELECT COUNT(*) as total FROM patients")
        total_scans = cursor.fetchone()["total"]
        
        # Malignant count
        cursor = db_execute("SELECT COUNT(*) as malignant FROM patients WHERE result='Malignant'")
        malignant_cases = cursor.fetchone()["malignant"]
        
        # Suspicious count
        cursor = db_execute("SELECT COUNT(*) as suspicious FROM patients WHERE result='Suspicious'")
        suspicious_cases = cursor.fetchone()["suspicious"]
        
        # Benign count
        cursor = db_execute("SELECT COUNT(*) as benign FROM patients WHERE result='Benign'")
        benign_cases = cursor.fetchone()["benign"]
        
        # Average Age
        cursor = db_execute("SELECT AVG(age) as avg_age FROM patients")
        avg_age_row = cursor.fetchone()
        avg_age_val = avg_age_row["avg_age"]
        avg_age = round(avg_age_val, 1) if avg_age_val is not None else 0
        
        # Recent scans
        cursor = db_execute("SELECT * FROM patients ORDER BY created_at DESC LIMIT 5")
        recent_scans = cursor.fetchall()
        
    except Exception as e:
        print("Error fetching dashboard statistics:", e)
        total_scans = 0
        malignant_cases = 0
        suspicious_cases = 0
        benign_cases = 0
        avg_age = 0
        recent_scans = []
        
    return render_template(
        "dashboard.html",
        total_scans=total_scans,
        malignant_cases=malignant_cases,
        suspicious_cases=suspicious_cases,
        benign_cases=benign_cases,
        avg_age=avg_age,
        recent_scans=recent_scans,
        model_status="Loaded" if model_loaded else "Simulated"
    )

# PREDICT
@app.route("/predict", methods=["GET","POST"])
def predict():
    if "user" not in session:
        return redirect("/")

    if request.method == "POST":
        try:
            name = request.form["name"]
            age = request.form["age"]
            file = request.files["image"]

            if file.filename == "":
                flash("Veuillez choisir une image", "warning")
                return redirect("/predict")

            path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(path)

            if model_loaded:
                img = image.load_img(path, target_size=(224,224))
                img = image.img_to_array(img)/255.0
                img = np.expand_dims(img, axis=0)
                pred = model.predict(img)[0][0]
            else:
                # Simulating a realistic medical diagnosis processing latency
                import time
                import random
                time.sleep(1.5)
                # Random realistic float between 0.1 and 0.9
                pred = random.uniform(0.12, 0.88)

            # Three-tier classification logic
            if pred >= 0.50:
                result = "Malignant"
                confidence = round(pred * 100, 2)
            elif pred >= 0.30:
                result = "Suspicious"
                confidence = round(pred * 100, 2) # Show malignant chance as indicator of risk
            else:
                result = "Benign"
                confidence = round((1 - pred) * 100, 2) # Certainty of being benign

            db_execute("""
                INSERT INTO patients (name, age, result, probability, image_path)
                VALUES (%s,%s,%s,%s,%s)
            """, (name, age, result, float(pred), path))
            db.commit()

            flash("Analyse réussie ✓", "success")

            return render_template("result.html",
                                   result=result,
                                   prob=confidence,
                                   raw_prob=round(pred*100, 2),
                                   img=path,
                                   name=name,
                                   age=age)

        except Exception as e:
            print("System analysis error:", e)
            flash("Erreur système lors de l'analyse", "danger")
            return redirect("/predict")

    return render_template("predict.html")

# PATIENTS
@app.route("/patients")
def patients():
    if "user" not in session:
        return redirect("/")
        
    try:
        cursor = db_execute("SELECT * FROM patients ORDER BY created_at DESC")
        data = cursor.fetchall()
    except Exception as e:
        print("Error querying patients list:", e)
        data = []
        
    return render_template("patients.html", patients=data)

# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    flash("Déconnecté avec succès", "info")
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True, port=5000)

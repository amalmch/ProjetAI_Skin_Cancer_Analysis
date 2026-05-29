# 🩺 SkinGuard AI — Clinical Skin Cancer Detection Platform

SkinGuard AI is a premium, high-fidelity medical diagnostic assistant designed to analyze dermoscopic skin lesion images and classify them into three clinical risk tiers (Malignant/Melanoma, Suspicious, or Benign). Equipped with a custom deep learning classifier and a state-of-the-art glassmorphic dark/light interactive dashboard, it provides clinical practitioners with instant risk profiling, analytics, and historical patient tracking.

---

## 📺 Demonstration Video

Here is a full high-fidelity walkthrough of the **SkinGuard AI** platform in action, showcasing the dual-theme dashboard, deep-learning analysis inference, dynamic charts, and the interactive patient records management drawer:

https://github.com/amalmch/ProjetAI_Skin_Cancer_Analysis/raw/main/projet_AI.mp4

Alternatively, you can access the raw video file directly:
[![SkinGuard AI Platform Demo](https://img.shields.io/badge/Demo_Video-Click_to_Watch-6366f1?style=for-the-badge&logo=youtube)](https://github.com/amalmch/ProjetAI_Skin_Cancer_Analysis/raw/main/projet_AI.mp4)

---

## ⚡ Technologies Used

### Frontend & Visuals
* **UI/UX Framework**: Pure Vanilla HTML5 & Modern CSS3 with high-fidelity glassmorphism custom properties.
* **Layout Design**: Fully responsive CSS Grid and Flexbox with premium micro-animations.
* **Theme Engine**: Double-theme mode (Celestial Dark / Clinical Light) using CSS Custom Properties and `localStorage` state persistence.
* **Data Visualizations**: **Chart.js** dynamic canvas integrations (doughnut & bar charts).

### Backend & AI Inference
* **Web Framework**: **Flask** (Python micro-framework) with secure session handling and flash alert notifications.
* **Deep Learning Engine**: **TensorFlow / Keras** for neural network inference.
* **Numerical Utilities**: **NumPy** for matrix manipulations.

### Storage & Database
* **Primary Database**: **MySQL** (MariaDB connection with auto-setup schemas).
* **Failover Engine**: **SQLite3** embedded local database fallback (zero-configuration local state).

---

## 🗄️ Database Architecture

SkinGuard AI has a double-tier storage engine that automatically connects to MySQL on startup, or falls back seamlessly to SQLite if the database server is offline.

The schema consists of two tables:
1. **`users`**: Manages credential authorization for practitioners.
2. **`patients`**: Stores historical clinical records, scan parameters, and file locations.

```sql
-- Patients directory schema
CREATE TABLE patients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    age INT NOT NULL,
    result VARCHAR(20) NOT NULL,        -- 'Malignant', 'Suspicious', 'Benign'
    probability FLOAT NOT NULL,         -- Deep learning confidence (0.0 to 1.0)
    image_path VARCHAR(255) NOT NULL,   -- Upload path of target scan
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Users credentials schema
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(50) NOT NULL
);
```

---

## 🧠 Deep Learning Model

The diagnostic engine is powered by a convolutional neural network built on top of the **VGG-16** architecture:
* **Input Resolution**: Preprocessed to $224 \times 224$ pixels, matching VGG-16 standard shape.
* **Model File**: Loaded from `model/vgg16_malignant_vs_benign.h5`.
* **Keras Loader Patch**: Contains automated backwards compatibility logic to bypass Keras version deserialization mismatches (`quantization_config` parameter conflicts).

---

## ⚙️ Application Logic & Seeding

```
                      +-------------------+
                      |   Image Upload    |
                      +---------+---------+
                                |
                                v
                      +-------------------+
                      |   Pre-processing  |
                      |   (224 x 224 px)  |
                      +---------+---------+
                                |
                                v
                      +-------------------+
                      | VGG-16 Prediction |
                      +---------+---------+
                                |
             +------------------+------------------+
             |                                     |
             v [Prob >= 0.50]                      v [Prob < 0.50]
    +-----------------+                   +-----------------+
    |    Malignant    |                   |  Benign/Suspect |
    +-----------------+                   +--------+--------+
                                                   |
                                 +-----------------+-----------------+
                                 v [Prob >= 0.30]                    v [Prob < 0.30]
                        +-----------------+                 +-----------------+
                        |   Suspicious    |                 |     Benign      |
                        +-----------------+                 +-----------------+
```

### Risk Stratification Logic:
* **Mélanome Suspecté (Malignant)**: Prediction score $\ge 50\%$. Flags severe structural atypia. Immediate biopsy or emergency consultation recommended.
* **Risque Modéré (Suspicious)**: Prediction score between $30\%$ and $49\%$. Moderate atypical markers. Dermoscopic check recommended.
* **Lésion Bénigne (Benign)**: Prediction score $< 30\%$. Low atypia markers. Typical nevus or seborrheic keratosis.

---

## 📂 Codebase & Folder Structure

```
SKIN_CANCER_APP/
├── model/
│   ├── vgg16_malignant_vs_benign.h5   # Trained deep learning VGG-16 model
│   └── projet AI.ipynb                # Development training notebook
├── static/
│   ├── uploads/                       # Dermoscopic images uploaded by users
│   ├── styles.css                     # Premium Glassmorphic style sheet
│   └── favicon.ico                    # Platform icon asset
├── templates/
│   ├── base.html                      # Unified sidebar navigation framework
│   ├── login.html                     # Auth interface with theme toggle
│   ├── dashboard.html                 # Analytics overview with Chart.js
│   ├── predict.html                   # Upload form with laser scanner beam loader
│   ├── result.html                    # Clinical outcome report print layout
│   └── patients.html                  # Directory with interactive drawer & lightbox
├── app.py                             # Central Flask app controller (fallbacks & routes)
├── database.sql                       # Database backup script
└── README.md                          # Documentation file
```

---

## 🚀 Getting Started

### Prerequisites
Make sure you have Python 3.10+ and a MySQL instance (like XAMPP or WampServer) running.

### Installation
1. Clone the repository to your machine.
2. Open your terminal in the directory and run:
   ```bash
   pip install flask tensorflow mysql-connector-python numpy
   ```

### Database Setup
1. Start your local MySQL database server (e.g. from the XAMPP Control Panel).
2. Start the application:
   ```bash
   python app.py
   ```
   *Note: On launch, the backend will **automatically create** the `skin_cancer_db` database and generate the `users` and `patients` tables. If MySQL is offline, it will write a local SQLite fallback database (`skin_cancer_fallback.db`).*

### Default Login
* **Username**: `admin`
* **Password**: `1234`

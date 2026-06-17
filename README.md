# AI-Powered Smart Interview Preparation and Assessment System

An advanced, end-to-end interview preparation and evaluation platform designed for Computer Science students. Built using **Django 5.x**, **MySQL**, and **Bootstrap 5**, featuring a premium dark-themed "Bento Grid" user interface with glassmorphism styling.

---

## 🚀 Key Modules & Features

### 1. Authentication Module
*   Secure User Registration and Login.
*   Profile Management (Domain Preference & Career Goals selection).
*   Password Change & Recovery flows.

### 2. Resume Analyzer Module
*   Upload resumes in **PDF** or **DOCX** format.
*   Automatic information parsing (Name, Email, Phone, Education, Certifications) using `pdfplumber` and `python-docx` utilities.
*   Auto-extraction of candidate skillsets matched against a master skill index.

### 3. Technical Quiz Engine
*   Randomized quiz generation based on selected domain and difficulty.
*   **Cheat Detection System**: Logs student browser behavior (tab switches, window minimizations, and focus loss warnings) and sends analytics to the submission payload.
*   Review dashboard with detailed explanation cards and concept check suggestions.

### 4. Coding Round Workspace
*   Split-pane interactive code editor.
*   **Sandboxed Subprocess Runner**: Executes Python code against hidden test cases with a strict 2-second timeout and memory caps.

### 5. HR Mock Voice Interview
*   **Text-to-Speech (TTS)**: Dynamic question voice synthesis using the `gTTS` library.
*   **Speech-to-Text (STT)**: Dual-mode response capture using browser-native Dictation API with Python `SpeechRecognition` backup.
*   Keyword evaluation engine providing feedback based on model answer benchmarks.

### 6. Recommendation & Roadmap Engines
*   Correlation of quiz performance with technical domains to highlight weak points.
*   Month-by-month timeline checkpoints roadmap tailored for specific careers (DevOps, Data Science, Backend/Frontend).

### 7. Leaderboard & Certification
*   Global candidate ranking sorted by total experience/activity points (Quizzes: 10 pts, Code solved: 25 pts).
*   Dynamic landscape PDF certificates generated with `ReportLab` featuring secure verification hashes.

---

## 🛠️ Technology Stack

*   **Backend:** Python 3.12, Django 5.x
*   **Database:** MySQL (SQLite fallback configuration included)
*   **Libraries:** `pdfplumber`, `python-docx`, `reportlab`, `gTTS`, `SpeechRecognition`, `mysqlclient`, `pandas`, `numpy`
*   **Frontend:** HTML5, CSS3 (Custom Glassmorphism), Bootstrap 5, JavaScript (AJAX)

---

## ⚙️ Local Setup Instructions

### Step 1: Clone the repository and navigate to root
```bash
cd "Minor Project"
```

### Step 2: Set up Virtual Environment & Install Dependencies
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 3: Set up MySQL Database User
Since Ubuntu/Debian MySQL forces strict password policies, log into your MySQL monitor and run the following statements:
```bash
sudo mysql -u root
```
In the MySQL prompt, run:
```sql
CREATE DATABASE IF NOT EXISTS interview_prep;
CREATE USER 'interview_user'@'localhost' IDENTIFIED BY 'Shiva@9876#Data';
GRANT ALL PRIVILEGES ON interview_prep.* TO 'interview_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### Step 4: Run Migrations
Generate the database schemas:
```bash
python manage.py makemigrations accounts resume_analyzer quiz coding hr_interview recommendation roadmap leaderboard certificates
python manage.py migrate
```

### Step 5: Seed the Technical Question Bank
Load 500+ realistic interview questions into the database:
```bash
python manage.py seed_questions
```

### Step 6: Start Server
Run the local development server:
```bash
python manage.py runserver
```
Navigate to `http://127.0.0.1:8000/` in your web browser!

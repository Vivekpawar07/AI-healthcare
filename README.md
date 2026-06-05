# HealthTrack — Patient Health Management System

A web application for managing patient blood test records with rule-based health assessments and an optional AI-powered chat assistant (via the companion `healthcare_agent_api` service).

---

## What It Does

HealthTrack lets you record, view, and manage patient health profiles built around three blood markers:

| Marker | Unit | Normal Range |
|---|---|---|
| Glucose (fasting) | mg/dL | 70 – 100 |
| Haemoglobin | g/dL | 12 – 17.5 |
| Cholesterol (total) | mg/dL | < 200 |

### Features

- **Patient records** — store Full Name, Date of Birth, Email, and all three blood test values
- **CRUD operations** — create, view, edit, and delete patient records
- **Rule-based health remarks** — automatically generated on save based on clinical reference ranges
- **Donut charts** — visual breakdown of each metric per patient, with green borders for safe-zone values and red for out-of-range
- **Search** — filter patients by name or email from the dashboard
- **Input validation** — email format, date of birth must be in the past, blood values must be positive numbers, no duplicate emails
- **AI Health Assistant** — when the companion API service is running, patients can generate a full structured health report and chat with a Gemini-powered assistant directly from the patient detail page
- **Persistent storage** — SQLite database, no external database setup required

---

## Project Structure

```
website/
├── app.py              # Flask application — routes, models, validation, remarks logic
├── requirements.txt    # Python dependencies
├── instance/
│   └── health.db       # SQLite database (auto-created on first run)
├── static/
│   └── css/
│       └── style.css   # Custom styles on top of Bootstrap 5
└── templates/
    ├── base.html        # Shared layout (navbar, flash messages, Bootstrap CDN)
    ├── index.html       # Patient list with search
    ├── add.html         # Add new patient form
    ├── edit.html        # Edit existing patient form
    └── view.html        # Patient detail — donut charts + AI assistant panel
```

---

## Requirements

- Python 3.9 or later
- pip

No database server is needed — SQLite is bundled with Python.

---

## Setup

### 1. Clone / navigate to the project

```bash
cd /Users/vivekpawar/Desktop/QuantumHalo/healthcare/website
```

### 2. Create and activate a virtual environment (recommended)

```bash
python -m venv .venv
source .venv/bin/activate      # macOS / Linux
# .venv\Scripts\activate       # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the application

```bash
python app.py
```

The server starts at **http://127.0.0.1:5000** in debug mode.

The SQLite database (`instance/health.db`) is created automatically on the first run — no migration step needed.

---

## Environment Variables

The app works out of the box without any environment variables. Optionally set:

| Variable | Default | Purpose |
|---|---|---|
| `SECRET_KEY` | `dev-secret-key-change-in-prod` | Flask session signing key — change this in production |

Create a `.env` file in this directory to set variables:

```
SECRET_KEY=your-secure-random-string
```

---

## Pages

| URL | Description |
|---|---|
| `/` | Patient list with search bar |
| `/add` | Add a new patient |
| `/patient/<id>` | Patient detail — charts, remarks, AI assistant |
| `/edit/<id>` | Edit an existing patient |
| `/delete/<id>` | Delete a patient (POST, confirmation prompt) |

---

## AI Health Assistant (optional)

The patient detail page includes an AI assistant panel that requires the companion service to be running.

Start the companion API (see `../healthcare_agent_api/`):

```bash
cd ../healthcare_agent_api
export GEMINI_API_KEY=your-gemini-api-key
python app.py          # runs on http://127.0.0.1:8000
```

Get a free Gemini API key at **https://aistudio.google.com**.

With the API running, opening any patient detail page gives you:

- **Generate Full Report** — streams a structured health report (overall assessment, per-marker analysis, risk factors, lifestyle recommendations)
- **Chat** — ask follow-up questions about the patient's values; conversation history is preserved per patient in browser `localStorage`

If the API is not running the rest of the website works normally — only the AI panel is unavailable.

---

## Health Value Reference Ranges

| Metric | Low | Normal | Borderline | High |
|---|---|---|---|---|
| Glucose (mg/dL) | < 70 | 70 – 100 | 101 – 125 (pre-diabetic) | ≥ 126 |
| Haemoglobin (g/dL) | < 12 | 12 – 17.5 | — | > 17.5 |
| Cholesterol (mg/dL) | — | < 200 | 200 – 239 | ≥ 240 |

> This application is for informational and educational purposes only. It does not constitute medical advice. Always consult a qualified healthcare professional.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask 3, Flask-SQLAlchemy |
| Database | SQLite (via SQLAlchemy) |
| Frontend | Bootstrap 5, Bootstrap Icons |
| Charts | Chart.js 4 |
| AI (optional) | Google Gemini via companion FastAPI service |

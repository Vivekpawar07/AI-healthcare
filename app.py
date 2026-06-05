from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import date, datetime
import os
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-prod')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///health.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    glucose = db.Column(db.Float, nullable=False)
    haemoglobin = db.Column(db.Float, nullable=False)
    cholesterol = db.Column(db.Float, nullable=False)
    remarks = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def age(self):
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    @property
    def glucose_status(self):
        if self.glucose < 70:
            return 'low', 'danger'
        elif self.glucose <= 100:
            return 'normal', 'success'
        elif self.glucose <= 125:
            return 'pre-diabetic', 'warning'
        return 'high', 'danger'

    @property
    def haemoglobin_status(self):
        if self.haemoglobin < 12:
            return 'low (anaemia risk)', 'danger'
        elif self.haemoglobin <= 17.5:
            return 'normal', 'success'
        return 'high', 'warning'

    @property
    def cholesterol_status(self):
        if self.cholesterol < 200:
            return 'desirable', 'success'
        elif self.cholesterol <= 239:
            return 'borderline high', 'warning'
        return 'high', 'danger'


def generate_remarks(glucose, haemoglobin, cholesterol):
    notes = []

    if glucose < 70:
        notes.append("Glucose is below normal range — possible hypoglycaemia; dietary review recommended.")
    elif 70 <= glucose <= 100:
        notes.append("Fasting glucose is within normal range.")
    elif 101 <= glucose <= 125:
        notes.append("Glucose is in the pre-diabetic range — lifestyle modifications and monitoring advised.")
    else:
        notes.append("Glucose is significantly elevated — consult a physician for diabetes evaluation.")

    if haemoglobin < 12:
        notes.append("Haemoglobin is low, indicating possible anaemia — further investigation advised.")
    elif 12 <= haemoglobin <= 17.5:
        notes.append("Haemoglobin is within acceptable limits.")
    else:
        notes.append("Haemoglobin is above normal — polycythaemia screening may be warranted.")

    if cholesterol < 200:
        notes.append("Cholesterol level is desirable.")
    elif 200 <= cholesterol <= 239:
        notes.append("Cholesterol is borderline high — dietary changes and regular monitoring recommended.")
    else:
        notes.append("Cholesterol is high — medical consultation and lipid management advised.")

    return " ".join(notes)


def validate_form(form, current_patient_id=None):
    errors = []

    if not form.get('full_name', '').strip():
        errors.append('Full name is required.')

    email = form.get('email', '').strip()
    if not re.match(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$', email):
        errors.append('Please enter a valid email address.')
    else:
        existing = Patient.query.filter_by(email=email).first()
        if existing and existing.id != current_patient_id:
            errors.append('A patient with this email already exists.')

    try:
        dob = datetime.strptime(form.get('date_of_birth', ''), '%Y-%m-%d').date()
        if dob >= date.today():
            errors.append('Date of birth must be in the past.')
    except ValueError:
        errors.append('Please enter a valid date of birth.')

    for field, label in [('glucose', 'Glucose'), ('haemoglobin', 'Haemoglobin'), ('cholesterol', 'Cholesterol')]:
        try:
            val = float(form.get(field, ''))
            if val <= 0:
                errors.append(f'{label} must be a positive number.')
        except (ValueError, TypeError):
            errors.append(f'{label} must be a valid number.')

    return errors


@app.route('/')
def index():
    search = request.args.get('search', '').strip()
    if search:
        patients = Patient.query.filter(
            Patient.full_name.ilike(f'%{search}%') |
            Patient.email.ilike(f'%{search}%')
        ).order_by(Patient.created_at.desc()).all()
    else:
        patients = Patient.query.order_by(Patient.created_at.desc()).all()
    return render_template('index.html', patients=patients, search=search)


@app.route('/add', methods=['GET', 'POST'])
def add_patient():
    if request.method == 'POST':
        errors = validate_form(request.form)
        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('add.html', form=request.form)

        dob = datetime.strptime(request.form['date_of_birth'], '%Y-%m-%d').date()
        glucose = float(request.form['glucose'])
        haemoglobin = float(request.form['haemoglobin'])
        cholesterol = float(request.form['cholesterol'])

        patient = Patient(
            full_name=request.form['full_name'].strip(),
            date_of_birth=dob,
            email=request.form['email'].strip().lower(),
            glucose=glucose,
            haemoglobin=haemoglobin,
            cholesterol=cholesterol,
            remarks=generate_remarks(glucose, haemoglobin, cholesterol)
        )
        db.session.add(patient)
        db.session.commit()
        flash(f'Patient "{patient.full_name}" added successfully.', 'success')
        return redirect(url_for('view_patient', id=patient.id))

    return render_template('add.html', form={})


@app.route('/patient/<int:id>')
def view_patient(id):
    patient = Patient.query.get_or_404(id)
    return render_template('view.html', patient=patient)


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_patient(id):
    patient = Patient.query.get_or_404(id)

    if request.method == 'POST':
        errors = validate_form(request.form, current_patient_id=id)
        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('edit.html', patient=patient, form=request.form)

        dob = datetime.strptime(request.form['date_of_birth'], '%Y-%m-%d').date()
        glucose = float(request.form['glucose'])
        haemoglobin = float(request.form['haemoglobin'])
        cholesterol = float(request.form['cholesterol'])

        patient.full_name = request.form['full_name'].strip()
        patient.date_of_birth = dob
        patient.email = request.form['email'].strip().lower()
        patient.glucose = glucose
        patient.haemoglobin = haemoglobin
        patient.cholesterol = cholesterol
        patient.remarks = generate_remarks(glucose, haemoglobin, cholesterol)
        patient.updated_at = datetime.utcnow()

        db.session.commit()
        flash(f'Patient "{patient.full_name}" updated successfully.', 'success')
        return redirect(url_for('view_patient', id=id))

    return render_template('edit.html', patient=patient, form={})


@app.route('/delete/<int:id>', methods=['POST'])
def delete_patient(id):
    patient = Patient.query.get_or_404(id)
    name = patient.full_name
    db.session.delete(patient)
    db.session.commit()
    flash(f'Patient "{name}" deleted.', 'success')
    return redirect(url_for('index'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

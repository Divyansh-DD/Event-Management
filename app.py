from flask import Flask, render_template, request, redirect, url_for, Response, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Regexp
from sqlalchemy.exc import IntegrityError
import logging
from io import StringIO
import csv
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///events.db'
db = SQLAlchemy(app)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    registrations = db.relationship('Registration', backref='event', lazy=True)

class Registration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    phone = db.Column(db.String(15), nullable=False)
    year = db.Column(db.String(10), nullable=False)
    branch = db.Column(db.String(50), nullable=False)
    after_note = db.Column(db.Text, nullable=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)

class RegistrationForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[DataRequired(), Regexp(r'^\d{10}$', message="Phone must be 10 digits")])
    year = StringField('Year', validators=[DataRequired()])
    branch = StringField('Branch', validators=[DataRequired()])
    after_note = TextAreaField('Additional Notes', validators=[Length(max=500)])
    submit = SubmitField('Register')

def seed_events():
    with app.app_context():
        if Event.query.count() == 0:
            events_data = [
                {'id': 1, 'title': 'AI Innovations Summit 2025', 'date': '2025-10-05', 'location': 'AITR Auditorium, Indore'},
                {'id': 2, 'title': 'Web Development Workshop', 'date': '2025-10-12', 'location': 'Online (Zoom)'},
                {'id': 3, 'title': 'Cloud Computing Crash Course', 'date': '2025-10-19', 'location': 'AITR Lab 101'},
                {'id': 4, 'title': 'Mobile App Hackathon', 'date': '2025-11-02', 'location': 'AITR Open Grounds'}
            ]
            for event in events_data:
                new_event = Event(
                    id=event['id'],
                    title=event['title'],
                    date=datetime.strptime(event['date'], '%Y-%m-%d').date(),
                    location=event['location']
                )
                db.session.add(new_event)
            db.session.commit()
            logger.debug("Events seeded successfully")

@app.route('/', methods=['GET'])
def index():
    seed_events()
    events = Event.query.all()
    return render_template('index.html', events=events)

@app.route('/event_info/<int:event_id>')
def event_info(event_id):
    event = Event.query.get_or_404(event_id)
    return render_template('event_info.html', event=event)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    event_id = request.args.get('event_id')
    if form.validate_on_submit() and event_id:
        try:
            new_registration = Registration(
                name=form.name.data,
                email=form.email.data,
                phone=form.phone.data,
                year=form.year.data,
                branch=form.branch.data,
                after_note=form.after_note.data,
                event_id=int(event_id)
            )
            db.session.add(new_registration)
            db.session.commit()
            return redirect(url_for('success'))
        except IntegrityError as e:
            db.session.rollback()
            return render_template('register.html', form=form, error="Registration failed: Email already exists or database error.")
        except Exception as e:
            db.session.rollback()
            return render_template('register.html', form=form, error=f"Registration failed: {str(e)}")
    return render_template('register.html', form=form, errors=form.errors if not form.validate_on_submit() else None)

@app.route('/success')
def success():
    return render_template('success.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            return render_template('admin_login.html', error="Please enter both username and password!")
        if verify_login(username, password):
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        return render_template('admin_login.html', error="Invalid username or password!")
    return render_template('admin_login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        return "Login successful"
    return render_template('login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    registrations = Registration.query.all()
    registrations_with_events = []
    for reg in registrations:
        event = Event.query.get(reg.event_id)
        registrations_with_events.append({
            'id': reg.id,
            'name': reg.name,
            'email': reg.email,
            'event': event.title if event else 'Unknown'
        })
    return render_template('admin_dashboard.html', registrations=registrations_with_events)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/download_csv')
def download_csv():
    output = StringIO()
    writer = csv.writer(output)
    
    # Remove "After Note" column
    writer.writerow(['ID', 'Name', 'Email', 'Phone', 'Year', 'Branch', 'Event'])
    
    registrations = Registration.query.all()
    for reg in registrations:
        event = Event.query.get(reg.event_id)
        event_name = event.title if event else 'Unknown'
        writer.writerow([
            reg.id,
            reg.name,
            reg.email,
            reg.phone,
            reg.year,
            reg.branch,
            event_name
        ])
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=registrations.csv"}
    )


@app.route('/api/registrations', methods=['GET'])
def get_registrations():
    registrations = Registration.query.all()
    registrations_data = []
    for reg in registrations:
        event = Event.query.get(reg.event_id)
        registrations_data.append({
            'id': reg.id,
            'name': reg.name,
            'email': reg.email,
            'phone': reg.phone,
            'year': reg.year,
            'branch': reg.branch,
            'after_note': reg.after_note or '',
            'event': event.title if event else 'Unknown'
        })
    return jsonify(registrations_data)


@app.route('/delete_registration/<int:reg_id>', methods=['POST'])
def delete_registration(reg_id):
    reg = Registration.query.get_or_404(reg_id)
    db.session.delete(reg)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

def verify_login(username, password):
    return username == 'admin' and password == 'admin123'

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_events()
    app.run(debug=True)

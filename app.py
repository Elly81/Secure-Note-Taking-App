from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import os

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "supersecret")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize Extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    notes = db.relationship('Note', backref='user', lazy=True, cascade="all, delete-orphan")

# Note model
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)

# Home Route (Login Page)
@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

# Register Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if User.query.filter_by(username=username).first():
            flash("Username already exists!", "danger")
            return redirect(url_for('register'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash("Account created! You can now log in.", "success")
        return redirect(url_for('home'))

    return render_template('register.html')

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        
        flash("Invalid credentials!", "danger")
    return render_template('index.html')

# Dashboard (Shows Notes)
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('home'))

    user_id = session['user_id']
    notes = Note.query.filter_by(user_id=user_id).all()
    return render_template('dashboard.html', notes=notes)

# Add Note
@app.route('/add', methods=['POST'])
def add_note():
    if 'user_id' not in session:
        return redirect(url_for('home'))

    note_content = request.form.get('note')

    if note_content:
        new_note = Note(user_id=session['user_id'], content=note_content)
        db.session.add(new_note)
        db.session.commit()

    return redirect(url_for('dashboard'))

# Update Note
@app.route('/update/<int:note_id>', methods=['POST'])
def update_note(note_id):
    if 'user_id' not in session:
        return redirect(url_for('home'))

    note = Note.query.get_or_404(note_id)

    if note.user_id != session['user_id']:
        return redirect(url_for('dashboard'))

    note.content = request.form.get('updated_note')
    db.session.commit()
    return redirect(url_for('dashboard'))

# Delete Note
@app.route('/delete/<int:note_id>', methods=['POST'])
def delete_note(note_id):
    if 'user_id' not in session:
        return redirect(url_for('home'))

    note = Note.query.get_or_404(note_id)

    if note.user_id != session['user_id']:
        return redirect(url_for('dashboard'))

    db.session.delete(note)
    db.session.commit()
    return redirect(url_for('dashboard'))

# Logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))

# Run the app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensures database tables are created properly
    app.run(debug=True)

from flask import Flask, render_template, request, redirect, session, jsonify, flash, url_for
from flask_mysqldb import MySQL
import qrcode
import os
import datetime
import json

app = Flask(__name__)
app.secret_key = "supersecretkey"

# MySQL configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'skillconnect'
mysql = MySQL(app)

# ---------------- Home & Auth ----------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, password))
        user = cursor.fetchone()
        cursor.close()
        if user:
            session['user_id'] = user[0]
            session['role'] = user[4]
            return redirect('/dashboard')
        flash("Invalid credentials","danger")
    return render_template('login.html')

@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method=='POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO users(name,email,password) VALUES(%s,%s,%s)", (name,email,password))
        mysql.connection.commit()
        cursor.close()
        flash("Signup successful! Please login","success")
        return redirect('/login')
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ---------------- Dashboard ----------------
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    user_id = session['user_id']
    cursor = mysql.connection.cursor()
    # Learner Overview
    cursor.execute("SELECT COUNT(*), SUM(price) FROM bookings WHERE user_id=%s AND status='confirmed'", (user_id,))
    total_sessions, total_spent = cursor.fetchone()
    cursor.execute("SELECT skill_id FROM bookings WHERE user_id=%s", (user_id,))
    skills_learned = cursor.fetchall()
    cursor.close()
    return render_template('dashboard.html', total_sessions=total_sessions or 0, total_spent=total_spent or 0, skills_learned=len(skills_learned))

# ---------------- Browse Skills ----------------
@app.route('/skills')
def browse_skills():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT s.id, s.title, s.category, s.price, s.rating, u.name, u.experience_years FROM skills s JOIN users u ON s.owner_id=u.id")
    skills = cursor.fetchall()
    cursor.close()
    return render_template('browse_skills.html', skills=skills)

@app.route('/book/<int:skill_id>', methods=['POST'])
def book_skill(skill_id):
    if 'user_id' not in session:
        return jsonify({'error':'login required'})
    user_id = session['user_id']
    qr_path = f'static/qr/{skill_id}_{user_id}.png'
    qr = qrcode.make(f'Booking: Skill {skill_id} for User {user_id}')
    qr.save(qr_path)
    cursor = mysql.connection.cursor()
    cursor.execute("INSERT INTO bookings(user_id, skill_id, status, qr_code_path) VALUES(%s,%s,'confirmed',%s)", (user_id, skill_id, qr_path))
    mysql.connection.commit()
    cursor.close()
    return jsonify({'qr': qr_path})

# ---------------- Events ----------------
@app.route('/events')
def events():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT e.id, e.title, e.date, e.time, e.duration, e.location, e.price, e.max_participants, e.skills, u.name FROM events e JOIN users u ON e.instructor_id=u.id")
    events = cursor.fetchall()
    cursor.close()
    return render_template('events.html', events=events)

@app.route('/create_event', methods=['GET','POST'])
def create_event():
    if 'user_id' not in session or session['role']!='skill_owner':
        return redirect('/login')
    if request.method=='POST':
        title = request.form['title']
        description = request.form['description']
        date = request.form['date']
        time = request.form['time']
        duration = request.form['duration']
        location = request.form['location']
        price = request.form['price']
        max_participants = request.form['max_participants']
        skills = request.form['skills']
        instructor_id = session['user_id']
        cursor = mysql.connection.cursor()
        cursor.execute("""
            INSERT INTO events(title,description,date,time,duration,location,price,max_participants,skills,instructor_id)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """,(title,description,date,time,duration,location,price,max_participants,skills,instructor_id))
        mysql.connection.commit()
        cursor.close()
        flash("Event created successfully!","success")
        return redirect('/events')
    return render_template('create_event.html')

# ---------------- Instructor Profile ----------------
@app.route('/profile/<int:instructor_id>')
def profile(instructor_id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM users WHERE id=%s", (instructor_id,))
    instructor = cursor.fetchone()
    cursor.execute("SELECT * FROM skills WHERE owner_id=%s", (instructor_id,))
    skills = cursor.fetchall()
    cursor.close()
    return render_template('profile.html', instructor=instructor, skills=skills)

import google.generativeai as genai
import os

# Configure Gemini
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

@app.route('/chatbot', methods=['POST'])
def chatbot():
    data = request.json
    user_message = data.get("message", "")

    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(user_message)
        bot_reply = response.text
    except Exception as e:
        bot_reply = "Sorry, I couldn’t process that. Please try again."

    return jsonify({"reply": bot_reply})

if __name__=="__main__":
    if not os.path.exists('static/qr'):
        os.makedirs('static/qr')
    app.run(debug=True)

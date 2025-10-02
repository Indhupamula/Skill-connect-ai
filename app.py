from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import datetime

app = Flask(__name__)
app.secret_key = "skillconnect_secret"

# -------------------------
# MySQL Configuration
# -------------------------
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'your_mysql_password'
app.config['MYSQL_DB'] = 'skillconnect_ai'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

# -------------------------
# Routes
# -------------------------

@app.route('/')
def index():
    return render_template('index.html')


# -------------------------
# Signup/Login
# -------------------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        role = request.form['role']

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (name,email,password,role) VALUES (%s,%s,%s,%s)",
                    (name, email, password, role))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('login'))
    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s", [email])
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['role'] = user['role']
            return redirect(url_for('dashboard'))
        else:
            return "Invalid credentials"
    return render_template('login.html')


# -------------------------
# Dashboard
# -------------------------
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    role = session['role']

    cur = mysql.connection.cursor()
    if role == 'learner':
        cur.execute("SELECT * FROM bookings b JOIN skills s ON b.skill_id = s.id WHERE b.learner_id=%s", [user_id])
        bookings = cur.fetchall()
        cur.execute("SELECT * FROM skills ORDER BY created_at DESC LIMIT 10")
        skills = cur.fetchall()
        cur.close()
        return render_template('learner_dashboard.html', bookings=bookings, skills=skills)
    else:
        cur.execute("SELECT * FROM skills WHERE owner_id=%s", [user_id])
        skills = cur.fetchall()
        cur.execute("SELECT * FROM events WHERE owner_id=%s", [user_id])
        events = cur.fetchall()
        cur.close()
        return render_template('owner_dashboard.html', skills=skills, events=events)


# -------------------------
# Add Skill
# -------------------------
@app.route('/add_skill', methods=['GET', 'POST'])
def add_skill():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form['title']
        category = request.form['category']
        price = request.form['price']
        description = request.form['description']
        owner_id = session['user_id']

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO skills (title,category,price,owner_id,description) VALUES (%s,%s,%s,%s,%s)",
                    (title, category, price, owner_id, description))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('dashboard'))
    return render_template('add_skill.html')


# -------------------------
# Add Event
# -------------------------
@app.route('/add_event', methods=['GET','POST'])
def add_event():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        date = request.form['date']
        time = request.form['time']
        duration = request.form['duration']
        location = request.form['location']
        price = request.form['price']
        max_participants = request.form['max_participants']
        skills = request.form['skills']
        owner_id = session['user_id']

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO events (title,description,date,time,duration,location,price,max_participants,owner_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (title, description, date, time, duration, location, price, max_participants, owner_id))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('dashboard'))
    return render_template('add_event.html')


# -------------------------
# Browse Skills
# -------------------------
@app.route('/skills')
def browse_skills():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM skills JOIN users ON skills.owner_id = users.id ORDER BY created_at DESC")
    skills = cur.fetchall()
    cur.close()
    return render_template('skill_list.html', skills=skills)


# -------------------------
# Book Skill (QR code placeholder)
# -------------------------
@app.route('/book/<int:skill_id>', methods=['POST'])
def book_skill(skill_id):
    if 'user_id' not in session:
        return jsonify({"status":"error","message":"Login required"})
    learner_id = session['user_id']

    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO bookings (skill_id, learner_id, status) VALUES (%s,%s,'confirmed')", (skill_id, learner_id))
    mysql.connection.commit()
    cur.close()

    # Return QR code placeholder (replace with real payment gateway)
    return jsonify({"status":"success","message":"Session booked successfully", "qr_code": f"/static/qrcode/skill_{skill_id}.png"})


# -------------------------
# Gemini AI Chatbot
# -------------------------
@app.route('/chatbot', methods=['POST'])
def chatbot():
    data = request.json
    message = data.get('message', '')

    # Gemini API integration
    api_key = "YOUR_GEMINI_API_KEY"
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {"prompt": message, "max_tokens": 150}

    response = requests.post("https://api.gemini.com/v1/complete", headers=headers, json=payload)
    if response.status_code == 200:
        reply = response.json().get("text", "Sorry, I couldn't understand that.")
    else:
        reply = "Sorry, AI service is currently unavailable."

    return jsonify({"reply": reply})


# -------------------------
# Logout
# -------------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


# -------------------------
# Run Server
# -------------------------
if __name__ == '__main__':
    app.run(debug=True)

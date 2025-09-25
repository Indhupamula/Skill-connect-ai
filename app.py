from flask import Flask, render_template, request, redirect, session, send_file
from flask_mysqldb import MySQL
import bcrypt
import qrcode
from io import BytesIO
import openai

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'your_password'
app.config['MYSQL_DB'] = 'skillconnect_ai'
mysql = MySQL(app)

# OpenAI API key
openai.api_key = "YOUR_API_KEY"

# Home
@app.route('/')
def index():
    return render_template('index.html')

# Signup
@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password'].encode('utf-8')
        role = request.form['role']
        hashed = bcrypt.hashpw(password, bcrypt.gensalt())
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users(name,email,password,role) VALUES(%s,%s,%s,%s)", (name,email,hashed,role))
        mysql.connection.commit()
        cur.close()
        return redirect('/login')
    return render_template('signup.html')

# Login
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password'].encode('utf-8')
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s", [email])
        user = cur.fetchone()
        cur.close()
        if user and bcrypt.checkpw(password, user[3].encode('utf-8')):
            session['user_id'] = user[0]
            session['role'] = user[4]
            return redirect('/dashboard')
        else:
            return "Invalid credentials"
    return render_template('login.html')

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# Dashboard
@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        return render_template('dashboard.html', role=session['role'])
    return redirect('/login')

# Add Skill
@app.route('/add_skill', methods=['GET','POST'])
def add_skill():
    if 'user_id' not in session or session['role'] != 'skill_owner':
        return redirect('/login')
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        user_id = session['user_id']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO skills(user_id,title,description) VALUES(%s,%s,%s)", (user_id,title,description))
        mysql.connection.commit()
        cur.close()
        return redirect('/dashboard')
    return render_template('add_skill.html')

# Add Event
@app.route('/add_event/<int:skill_id>', methods=['GET','POST'])
def add_event(skill_id):
    if 'user_id' not in session or session['role'] != 'skill_owner':
        return redirect('/login')
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        date = request.form['date']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO events(skill_id,title,description,date) VALUES(%s,%s,%s,%s)", (skill_id,title,description,date))
        mysql.connection.commit()
        cur.close()
        return redirect('/dashboard')
    return render_template('add_event.html', skill_id=skill_id)

# Booking + QR Code
@app.route('/book/<int:event_id>', methods=['POST'])
def book_event(event_id):
    if 'user_id' not in session or session['role'] != 'learner':
        return {"message":"Login as learner first"}, 401
    learner_id = session['user_id']
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO bookings(event_id,learner_id,status,payment_status) VALUES(%s,%s,'pending','pending')", (event_id,learner_id))
    mysql.connection.commit()
    cur.close()
    
    qr_data = f"Event:{event_id} Learner:{learner_id}"
    qr_img = qrcode.make(qr_data)
    buf = BytesIO()
    qr_img.save(buf)
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

# AI Chatbot
@app.route('/chatbot', methods=['POST'])
def chatbot():
    message = request.json['message']
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role":"user","content":message}]
    )
    return {"reply": response['choices'][0]['message']['content']}

# Recommendations
@app.route('/recommend', methods=['GET'])
def recommend():
    if 'user_id' not in session:
        return {"recommendations":[]}
    cur = mysql.connection.cursor()
    cur.execute("SELECT skills.id, skills.title, users.name FROM skills JOIN users ON skills.user_id=users.id LIMIT 5")
    results = cur.fetchall()
    cur.close()
    recommendations = [{"skill_id":r[0],"title":r[1],"owner":r[2]} for r in results]
    return {"recommendations": recommendations}

if __name__ == '__main__':
    app.run(debug=True)

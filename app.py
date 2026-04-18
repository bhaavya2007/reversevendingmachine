from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3
import random
import string
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "secret123")

DB = "database.db"

# -----------------------------
# GLOBAL ACTIVE CODE SYSTEM
# -----------------------------
current_code = None
current_points = 10

# -----------------------------
# DATABASE INIT
# -----------------------------
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT,
        points INTEGER DEFAULT 0
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS rewards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        cost INTEGER
    )
    """)

    conn.commit()
    conn.close()

init_db()

# -----------------------------
# HOME
# -----------------------------
@app.route('/')
def home():
    return render_template("login.html")

# -----------------------------
# REGISTER
# -----------------------------
@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    try:
        c.execute("INSERT INTO users VALUES (?, ?, 0)", (username, password))
        conn.commit()
    except:
        pass

    conn.close()
    return redirect('/')

# -----------------------------
# LOGIN
# -----------------------------
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()

    conn.close()

    if user:
        session['username'] = username
        return redirect('/dashboard')
    return "Login Failed"

# -----------------------------
# DASHBOARD
# -----------------------------
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect('/')

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT points FROM users WHERE username=?", (session['username'],))
    result = c.fetchone()

    points = result[0] if result else 0

    conn.close()

    return render_template("dashboard.html", points=points)

# -----------------------------
# GENERATE CODE (FOR ESP32)
# -----------------------------
@app.route('/generate_code')
def generate_code():
    global current_code, current_points

    if current_code is None:
        current_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        current_points = random.choice([5, 10, 15])

    return f"{current_code} ({current_points} pts)"

# -----------------------------
# REDEEM CODE
# -----------------------------
@app.route('/redeem', methods=['POST'])
def redeem():
    if 'username' not in session:
        return redirect('/')

    global current_code, current_points

    entered_code = request.form['code']

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    if entered_code == current_code:
        c.execute("UPDATE users SET points = points + ? WHERE username = ?", 
                  (current_points, session['username']))
        conn.commit()

        # RESET CODE AFTER USE
        current_code = None

        conn.close()
        return "SUCCESS"

    conn.close()
    return "INVALID CODE"

# -----------------------------
# REWARDS PAGE
# -----------------------------
@app.route('/rewards')
def rewards():
    if 'username' not in session:
        return redirect('/')

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT * FROM rewards")
    rewards = c.fetchall()

    c.execute("SELECT points FROM users WHERE username=?", (session['username'],))
    points = c.fetchone()[0]

    conn.close()

    return render_template("rewards.html", rewards=rewards, points=points)

# -----------------------------
# REDEEM REWARD
# -----------------------------
@app.route('/redeem_reward/<int:id>')
def redeem_reward(id):
    if 'username' not in session:
        return redirect('/')

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT cost, name FROM rewards WHERE id=?", (id,))
    reward = c.fetchone()

    c.execute("SELECT points FROM users WHERE username=?", (session['username'],))
    user_points = c.fetchone()[0]

    if reward and user_points >= reward[0]:
        new_points = user_points - reward[0]

        c.execute("UPDATE users SET points=? WHERE username=?", (new_points, session['username']))
        conn.commit()

        coupon = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

        conn.close()
        return jsonify({"status": "success", "coupon": coupon})

    conn.close()
    return jsonify({"status": "fail"})

# -----------------------------
# ADMIN ADD REWARD
# -----------------------------
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        name = request.form['name']
        cost = request.form['cost']

        conn = sqlite3.connect(DB)
        c = conn.cursor()

        c.execute("INSERT INTO rewards (name, cost) VALUES (?, ?)", (name, cost))
        conn.commit()
        conn.close()

    return render_template("admin.html")

# -----------------------------
# LOGOUT
# -----------------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    app.run()

from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3
import random
import string

app = Flask(__name__)
app.secret_key = "secret123"

DB = "database_v4.db"

latest_code = None
latest_points = 0


# ---------------- DATABASE ----------------

def get_conn():
    return sqlite3.connect(DB)


def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            points INTEGER DEFAULT 0
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS codes (
            code TEXT PRIMARY KEY,
            points INTEGER,
            used INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()


init_db()


# ---------------- ROUTES ----------------

@app.route('/')
def home():
    return redirect('/login')


@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        try:
            u = request.form.get('username')
            p = request.form.get('password')

            conn = get_conn()
            c = conn.cursor()
            c.execute("INSERT INTO users (username,password) VALUES (?,?)", (u,p))
            conn.commit()
            conn.close()

            return redirect('/login')

        except sqlite3.IntegrityError:
            return "User already exists"

    return render_template('register.html')


@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('username')
        p = request.form.get('password')

        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (u,p))
        user = c.fetchone()
        conn.close()

        if not user:
            return "Invalid credentials"

        session['user'] = u
        return redirect('/dashboard')

    return render_template('login.html')


@app.route('/dashboard', methods=['GET','POST'])
def dashboard():
    if 'user' not in session:
        return redirect('/login')

    conn = get_conn()
    c = conn.cursor()

    message = ""

    if request.method == 'POST':
        code = request.form.get('code')

        c.execute("SELECT * FROM codes WHERE code=? AND used=0", (code,))
        r = c.fetchone()

        if r:
            c.execute("UPDATE codes SET used=1 WHERE code=?", (code,))
            c.execute("UPDATE users SET points = points + ? WHERE username=?",
                      (r[1], session['user']))
            conn.commit()
            message = "Code applied!"
        else:
            message = "Invalid or used code"

    c.execute("SELECT points FROM users WHERE username=?", (session['user'],))
    points = c.fetchone()[0]

    conn.close()

    return render_template('dashboard.html', points=points, message=message)


# 🔥 SENSOR TRIGGER (generates new code)
@app.route('/trigger_code')
def trigger_code():
    global latest_code, latest_points

    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    points = random.randint(5, 20)

    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO codes VALUES (?, ?, 0)", (code, points))
    conn.commit()
    conn.close()

    latest_code = code
    latest_points = points

    return jsonify({
        "code": code,
        "points": points
    })


# 🔥 DISPLAY ONLY (no generation)
@app.route('/get_latest_code')
def get_latest_code():
    return latest_code if latest_code else "NO CODE"


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


# ---------------- RUN ----------------
if __name__ == '__main__':
    app.run()

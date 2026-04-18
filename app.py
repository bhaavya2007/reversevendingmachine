from flask import Flask, render_template, request, redirect, session
import sqlite3
import random
import string

app = Flask(__name__)
app.secret_key = "secret123"

DB = "database_v2.db"

ADMIN_USER = "admin"
ADMIN_PASS = "admin123"


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

    c.execute("""
        CREATE TABLE IF NOT EXISTS rewards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            cost INTEGER
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS coupons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reward_id INTEGER,
            coupon_code TEXT,
            used INTEGER DEFAULT 0
        )
    """)

    c.execute("SELECT COUNT(*) FROM rewards")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO rewards (name, cost) VALUES ('Free Coffee', 50)")
        c.execute("INSERT INTO rewards (name, cost) VALUES ('Discount Coupon', 100)")

        c.execute("INSERT INTO coupons (reward_id, coupon_code) VALUES (1, 'COFFEE50')")
        c.execute("INSERT INTO coupons (reward_id, coupon_code) VALUES (2, 'SAVE100')")

    conn.commit()
    conn.close()


# 🔥 RUN DB INIT ALWAYS (IMPORTANT FIX)
init_db()


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
            c.execute("INSERT INTO users (username,password) VALUES (?,?)",(u,p))
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
    coupon = request.args.get('coupon')

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
            message = "Invalid code"

    c.execute("SELECT points FROM users WHERE username=?", (session['user'],))
    points = c.fetchone()[0]

    conn.close()

    return render_template('dashboard.html', points=points, message=message, coupon=coupon)


@app.route('/generate_code')
def generate_code():
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    pts = random.randint(5,20)

    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO codes VALUES (?,?,0)", (code, pts))
    conn.commit()
    conn.close()

    return f"{code} ({pts} pts)"


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

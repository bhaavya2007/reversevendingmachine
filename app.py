from flask import Flask, render_template, request, redirect, session
import sqlite3
import random
import string

app = Flask(__name__)
app.secret_key = "secret123"
DB = "database.db"

ADMIN_USER = "admin"
ADMIN_PASS = "admin123"


def init_db():
    conn = sqlite3.connect(DB)
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

    # Default rewards + coupons
    c.execute("SELECT COUNT(*) FROM rewards")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO rewards (name, cost) VALUES ('Free Coffee', 50)")
        c.execute("INSERT INTO rewards (name, cost) VALUES ('Discount Coupon', 100)")

        c.execute("INSERT INTO coupons (reward_id, coupon_code) VALUES (1, 'COFFEE50')")
        c.execute("INSERT INTO coupons (reward_id, coupon_code) VALUES (2, 'SAVE100')")

    conn.commit()
    conn.close()


@app.route('/')
def home():
    return redirect('/login')


# ✅ REGISTER (FIXED)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return "Missing data"

        conn = sqlite3.connect(DB)
        c = conn.cursor()

        try:
            c.execute("INSERT INTO users (username,password) VALUES (?,?)",
                      (username, password))
            conn.commit()
        except:
            conn.close()
            return "User already exists"

        conn.close()
        return redirect('/login')

    return render_template('register.html')


# LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('username')
        p = request.form.get('password')

        if u == ADMIN_USER and p == ADMIN_PASS:
            session.clear()
            session['admin'] = True
            return redirect('/admin')

        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p))
        user = c.fetchone()
        conn.close()

        if user:
            session.clear()
            session['user'] = u
            return redirect('/dashboard')

        return "Invalid credentials"

    return render_template('login.html')


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session:
        return redirect('/login')

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    message = ""
    success = False
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
            success = True
        else:
            message = "Invalid code"

    c.execute("SELECT points FROM users WHERE username=?", (session['user'],))
    points = c.fetchone()[0]

    conn.close()

    return render_template(
        'dashboard.html',
        points=points,
        message=message,
        success=success,
        coupon=coupon
    )


@app.route('/rewards')
def rewards():
    if 'user' not in session:
        return redirect('/login')

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT * FROM rewards")
    rewards = c.fetchall()

    c.execute("SELECT points FROM users WHERE username=?", (session['user'],))
    points = c.fetchone()[0]

    conn.close()

    return render_template('rewards.html', rewards=rewards, points=points)


@app.route('/redeem_reward/<int:id>')
def redeem_reward(id):
    if 'user' not in session:
        return redirect('/login')

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT cost FROM rewards WHERE id=?", (id,))
    cost = c.fetchone()[0]

    c.execute("SELECT points FROM users WHERE username=?", (session['user'],))
    points = c.fetchone()[0]

    if points < cost:
        return "Not enough points"

    c.execute("SELECT id, coupon_code FROM coupons WHERE reward_id=? AND used=0 LIMIT 1", (id,))
    coupon = c.fetchone()

    if not coupon:
        return "No coupons left"

    c.execute("UPDATE coupons SET used=1 WHERE id=?", (coupon[0],))
    c.execute("UPDATE users SET points = points - ? WHERE username=?",
              (cost, session['user']))

    conn.commit()
    conn.close()

    return redirect(f"/dashboard?coupon={coupon[1]}")


@app.route('/generate_code')
def generate_code():
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    points = random.randint(5, 20)

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT INTO codes VALUES (?, ?, 0)", (code, points))
    conn.commit()
    conn.close()

    return f"{code} ({points} pts)"


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


if __name__ == '__main__':
    init_db()
    app.run()

from flask import Flask, render_template, request, redirect, session
import sqlite3
import random
import string

app = Flask(__name__)
app.secret_key = "secret123"

# 🔥 NEW DATABASE FILE (fix)
DB = "database_v2.db"

ADMIN_USER = "admin"
ADMIN_PASS = "admin123"


# ---------------- DATABASE ----------------

def get_conn():
    return sqlite3.connect(DB)


def init_db():
    conn = get_conn()
    c = conn.cursor()

    # create tables safely (no drop)
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

    # insert defaults only once
    c.execute("SELECT COUNT(*) FROM rewards")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO rewards (name, cost) VALUES ('Free Coffee', 50)")
        c.execute("INSERT INTO rewards (name, cost) VALUES ('Discount Coupon', 100)")

        c.execute("INSERT INTO coupons (reward_id, coupon_code) VALUES (1, 'COFFEE50')")
        c.execute("INSERT INTO coupons (reward_id, coupon_code) VALUES (2, 'SAVE100')")

    conn.commit()
    conn.close()


# ---------------- ROUTES ----------------

@app.route('/')
def home():
    return redirect('/login')


# REGISTER
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            password = request.form.get('password')

            if not username or not password:
                return "Fill all fields"

            conn = get_conn()
            c = conn.cursor()

            c.execute("INSERT INTO users (username,password) VALUES (?,?)",
                      (username, password))
            conn.commit()
            conn.close()

            return redirect('/login')

        except sqlite3.IntegrityError:
            return "User already exists"
        except Exception as e:
            return f"ERROR: {str(e)}"

    return render_template('register.html')


# LOGIN
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        try:
            u = request.form.get('username')
            p = request.form.get('password')

            # admin
            if u == ADMIN_USER and p == ADMIN_PASS:
                session.clear()
                session['admin'] = True
                return redirect('/admin')

            conn = get_conn()
            c = conn.cursor()

            c.execute("SELECT * FROM users WHERE username=? AND password=?", (u,p))
            user = c.fetchone()

            conn.close()

            if not user:
                return "Invalid credentials"

            session.clear()
            session['user'] = u
            return redirect('/dashboard')

        except Exception as e:
            return f"ERROR: {str(e)}"

    return render_template('login.html')


# DASHBOARD
@app.route('/dashboard', methods=['GET','POST'])
def dashboard():
    if 'user' not in session:
        return redirect('/login')

    try:
        conn = get_conn()
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
        res = c.fetchone()

        if not res:
            session.clear()
            return redirect('/login')

        points = res[0]
        conn.close()

        return render_template(
            'dashboard.html',
            points=points,
            message=message,
            success=success,
            coupon=coupon
        )

    except Exception as e:
        return f"ERROR: {str(e)}"


# REWARDS
@app.route('/rewards')
def rewards():
    if 'user' not in session:
        return redirect('/login')

    conn = get_conn()
    c = conn.cursor()

    c.execute("SELECT * FROM rewards")
    rewards = c.fetchall()

    c.execute("SELECT points FROM users WHERE username=?", (session['user'],))
    points = c.fetchone()[0]

    conn.close()

    return render_template('rewards.html', rewards=rewards, points=points)


# REDEEM
@app.route('/redeem_reward/<int:id>')
def redeem_reward(id):
    if 'user' not in session:
        return redirect('/login')

    conn = get_conn()
    c = conn.cursor()

    c.execute("SELECT cost FROM rewards WHERE id=?", (id,))
    reward = c.fetchone()

    if not reward:
        return "Invalid reward"

    cost = reward[0]

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


# GENERATE CODE
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


# LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


# RUN
if __name__ == '__main__':
    init_db()
    app.run()

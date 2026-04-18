from flask import Flask, render_template, request, redirect, session
import sqlite3
import random
import string

app = Flask(__name__)
app.secret_key = "secret123"

DB = "database_final.db"

latest_code = "NO CODE"


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


# ---------------- DEBUG ROUTES ----------------

# 🔥 TEST ROUTE (VERY IMPORTANT)
@app.route('/test')
def test():
    return "WORKING"


# 🔥 SIMPLE CHECK ROUTE
@app.route('/hello')
def hello():
    return "HELLO FROM SERVER"


# ---------------- MAIN ROUTES ----------------

@app.route('/')
def home():
    return redirect('/dustbin')


# 🔥 DUSTBIN PAGE
@app.route('/dustbin')
def dustbin():
    return render_template('dustbin.html')


# 🔥 GENERATE CODE
@app.route('/trigger_code')
def trigger_code():
    global latest_code

    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    points = random.randint(5, 20)

    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO codes VALUES (?, ?, 0)", (code, points))
    conn.commit()
    conn.close()

    latest_code = f"{code} ({points} pts)"

    return latest_code


# ---------------- RUN ----------------

if __name__ == '__main__':
    app.run(debug=True)

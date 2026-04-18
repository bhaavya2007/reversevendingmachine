from flask import Flask, render_template
import sqlite3
import random
import string

app = Flask(__name__)

DB = "database_final.db"

# store last code
latest_code = "NO CODE"


# ---------------- DATABASE ----------------

def get_conn():
    return sqlite3.connect(DB)


def init_db():
    conn = get_conn()
    c = conn.cursor()

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
    return render_template('dustbin.html')


@app.route('/dustbin')
def dustbin():
    return render_template('dustbin.html')


# 🔥 GET LAST CODE (for page load)
@app.route('/get_code')
def get_code():
    return latest_code


# 🔥 GENERATE NEW CODE
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

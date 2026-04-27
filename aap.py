from flask import Flask, request, jsonify
import requests
import sqlite3
import time
import random
import string
import os

app = Flask(__name__)

# =========================
# EXTERNAL API
# =========================
BASE_URL = "https://aadhar-to-ration-api-abhaysingh.vercel.app/api/family"

# =========================
# DATABASE SETUP
# =========================
def init_db():
    conn = sqlite3.connect("keys.db", check_same_thread=False)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS keys (
            key TEXT PRIMARY KEY,
            expiry REAL
        )
    """)
    conn.commit()
    conn.close()

init_db()

# =========================
# KEY GENERATOR
# =========================
def generate_key(duration):
    key = "VERNEX-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
    expiry = 9999999999 if duration == "lifetime" else time.time() + duration

    conn = sqlite3.connect("keys.db", check_same_thread=False)
    c = conn.cursor()
    c.execute("INSERT INTO keys VALUES (?, ?)", (key, expiry))
    conn.commit()
    conn.close()

    return key, expiry

# =========================
# KEY CHECK
# =========================
def is_valid(key):
    conn = sqlite3.connect("keys.db", check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT expiry FROM keys WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()

    if not row:
        return False

    return time.time() < row[0]

# =========================
# PLANS
# =========================
DURATIONS = {
    "1d": 86400,
    "2d": 172800,
    "3d": 259200,
    "7d": 604800,
    "30d": 2592000,
    "60d": 5184000,
    "lifetime": "lifetime"
}

# =========================
# CLEAN DATA
# =========================
def clean_data(data):
    remove_keys = ["developer", "branding", "processed_by"]

    if isinstance(data, dict):
        return {
            k: clean_data(v)
            for k, v in data.items()
            if k not in remove_keys and "Abhay Singh" not in str(v)
        }

    if isinstance(data, list):
        return [clean_data(i) for i in data]

    return data

# =========================
# HOME ROUTE
# =========================
@app.route("/")
def home():
    return "VERNEX API LIVE 🚀"

# =========================
# GENERATE KEY
# =========================
@app.route("/generate")
def generate():
    plan = request.args.get("plan", "1d")

    if plan not in DURATIONS:
        return jsonify({"error": "Invalid plan"})

    key, expiry = generate_key(DURATIONS[plan])

    return jsonify({
        "key": key,
        "plan": plan,
        "expires_at": expiry
    })

# =========================
# MAIN API
# =========================
@app.route("/api/numinfo")
def numinfo():
    user_id = request.args.get("id")
    key = request.args.get("key")

    if not is_valid(key):
        return jsonify({"error": "Invalid or expired key"})

    try:
        res = requests.get(
            BASE_URL,
            params={"id": user_id},
            timeout=15
        )

        data = clean_data(res.json())
        data["owner"] = "VERNEX API"

        return jsonify(data)

    except Exception as e:
        return jsonify({
            "error": "API failed",
            "details": str(e)
        })

# =========================
# RUN (RENDER FIX)
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

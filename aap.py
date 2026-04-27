# ===============================
# VERNEX API - MAIN APP
# ===============================

from flask import Flask, request, jsonify
import requests
import sqlite3
import time
import random
import string
import os

# ===============================
# FLASK APP INIT
# ===============================
app = Flask(__name__)

# ===============================
# EXTERNAL API (NEW ENDPOINT)
# ===============================
BASE_URL = "https://aadhar-to-ration-api-abhaysingh.vercel.app/api/family"

# ===============================
# DATABASE INIT
# ===============================
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

# ===============================
# KEY GENERATOR FUNCTION
# ===============================
def generate_key(duration):
    key = "VERNEX-" + ''.join(
        random.choices(string.ascii_uppercase + string.digits, k=12)
    )

    # lifetime or timed key
    expiry = 9999999999 if duration == "lifetime" else time.time() + duration

    conn = sqlite3.connect("keys.db", check_same_thread=False)
    c = conn.cursor()

    c.execute("INSERT INTO keys VALUES (?, ?)", (key, expiry))

    conn.commit()
    conn.close()

    return key, expiry

# ===============================
# KEY VALIDATION FUNCTION
# ===============================
def is_valid(key):
    conn = sqlite3.connect("keys.db", check_same_thread=False)
    c = conn.cursor()

    c.execute("SELECT expiry FROM keys WHERE key=?", (key,))
    row = c.fetchone()

    conn.close()

    if not row:
        return False

    return time.time() < row[0]

# ===============================
# PLAN SYSTEM
# ===============================
DURATIONS = {
    "1d": 86400,
    "2d": 172800,
    "3d": 259200,
    "7d": 604800,
    "30d": 2592000,
    "60d": 5184000,
    "lifetime": "lifetime"
}

# ===============================
# CLEAN RESPONSE FUNCTION
# ===============================
def clean_data(data):
    remove_keys = ["branding", "developer", "processed_by", "owner_contact"]

    if isinstance(data, dict):
        new_data = {}

        for k, v in data.items():

            # remove unwanted keys
            if k in remove_keys:
                continue

            # remove Abhay Singh text if exists
            if isinstance(v, str) and "Abhay Singh" in v:
                continue

            new_data[k] = clean_data(v)

        return new_data

    elif isinstance(data, list):
        return [clean_data(i) for i in data]

    return data

# ===============================
# HOME ROUTE
# ===============================
@app.route("/")
def home():
    return "🚀 VERNEX API RUNNING SUCCESSFULLY"

# ===============================
# GENERATE KEY ROUTE
# ===============================
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

# ===============================
# MAIN API ROUTE
# ===============================
@app.route("/api/numinfo")
def numinfo():

    user_id = request.args.get("id")
    key = request.args.get("key")

    # key check
    if not is_valid(key):
        return jsonify({"error": "Invalid or expired key"})

    try:
        # call external API
        res = requests.get(
            BASE_URL,
            params={"id": user_id},
            timeout=15
        )

        data = res.json()

        # clean response
        data = clean_data(data)

        # branding
        data["owner"] = "VERNEX API"

        return jsonify(data)

    except Exception as e:
        return jsonify({
            "error": "API failed",
            "details": str(e)
        })

# ===============================
# RUN SERVER (RENDER FIX)
# ===============================
if __name__ == "__main__":

    # Render dynamic port fix
    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port
    )

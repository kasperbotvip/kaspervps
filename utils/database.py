import sqlite3
from datetime import datetime, timedelta
import json

with open('config.json', 'r') as f:
    config = json.load(f)

DB_PATH = config['database']['path']
OWNER_ID = config['bot']['owner_id']

def setup_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, expiry_date TEXT, points INTEGER DEFAULT 0)")
    cursor.execute("CREATE TABLE IF NOT EXISTS codes (code TEXT PRIMARY KEY, days INTEGER, points INTEGER DEFAULT 0)")
    cursor.execute("CREATE TABLE IF NOT EXISTS trial_users (user_id INTEGER PRIMARY KEY)")
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN points INTEGER DEFAULT 0")
    except:
        pass
    try:
        cursor.execute("ALTER TABLE codes ADD COLUMN points INTEGER DEFAULT 0")
    except:
        pass
    conn.commit()
    conn.close()

def check_vip(user_id):
    if user_id == OWNER_ID:
        return True, "OWNER", 999999
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT expiry_date, points FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        expiry = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S')
        points = row[1]
        if expiry > datetime.now() and points > 0:
            return True, row[0], points
    return False, None, 0

def deduct_point(user_id):
    if user_id == OWNER_ID:
        return
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET points = points - 1 WHERE user_id = ? AND points > 0", (user_id,))
    conn.commit()
    conn.close()

def add_points(user_id, points):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    current_pts = row[0] if row else 0
    total_pts = current_pts + points
    expiry = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("INSERT OR REPLACE INTO users (user_id, expiry_date, points) VALUES (?, ?, ?)",
                   (user_id, expiry, total_pts))
    conn.commit()
    conn.close()
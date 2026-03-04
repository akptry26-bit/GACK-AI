import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import google.generativeai as genai
from dotenv import load_dotenv
from thefuzz import process, fuzz

# 1. INITIALIZATION & SECURITY
load_dotenv()
app = Flask(__name__)
app.secret_key = 'GAC_CORE_AI_2026_SECURE_KEY'

ADMIN_USER = "admin"
ADMIN_PASS = "GAC@2026"

# GEMINI AI SETUP
API_KEY = os.getenv("GEMINI_API_KEY")
# FIXED: Stable identifier for Search Tool to avoid 404
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel(
    model_name='models/gemini-1.5-flash-latest',
    tools=[{"google_search_retrieval": {}}]
)

# 2. GOOGLE SEARCH FUNCTION
def get_chat_response(user_input):
    prompt = f"Using Google Search, give a direct answer for GAC Karur: {user_input}"
    try:
        response = model.generate_content(prompt)
        return response.text.strip() if response.text else None
    except Exception as e:
        print(f"API Error: {e}")
        return None

# 3. DATABASE ENGINE
def init_db():
    conn = sqlite3.connect('college_bot.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS knowledge (id INTEGER PRIMARY KEY AUTOINCREMENT, question TEXT UNIQUE, answer TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, user_query TEXT, bot_response TEXT)')
    
    default_data = [
        ("who are you", "I am GAC CORE AI, the official campus assistant of GAC Karur."),
        ("hello", "Hello! How can I help you with GAC Karur information today?"),
        ("college name", "Government Arts College (Autonomous), Karur.")
    ]
    c.executemany('INSERT OR IGNORE INTO knowledge (question, answer) VALUES (?, ?)', default_data)
    conn.commit()
    conn.close()

init_db()

# 4. CHATBOT CORE LOGIC (DB First, API Second)
@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_msg = data.get('message', '').strip().lower()
        reply = None

        # --- PHASE 0: Instant Greetings ---
        greetings_map = {
            "hi": "Hello! Welcome to GAC CORE AI.",
            "hello": "Hi there! I am your GAC Karur digital assistant.",
            "gm": "Good Morning! Have a great day at GAC Karur."
        }
        if user_msg in greetings_map:
            reply = greetings_map[user_msg]

        # --- PHASE 1: DB Search ---
        if not reply:
            conn = sqlite3.connect('college_bot.db')
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            knowledge_data = c.execute("SELECT question, answer FROM knowledge").fetchall()
            knowledge_dict = {row['question']: row['answer'] for row in knowledge_data}
            
            if knowledge_dict:
                best_match, score = process.extractOne(user_msg, knowledge_dict.keys(), scorer=fuzz.token_set_ratio)
                if score > 75: 
                    reply = knowledge_dict[best_match]

        # --- PHASE 2: Gemini + Google Search ---
        if not reply:
            reply = get_chat_response(user_msg)

        # --- PHASE 3: Fallback ---
        if not reply:
            reply = "I'm checking on that. Please check gackarur.ac.in for 2026 updates."

        # Logging (INDENTATION FIXED - Line 154 error won't repeat)
        conn = sqlite3.connect('college_bot.db')
        c = conn.cursor()
        c.execute("INSERT INTO logs (timestamp, user_query, bot_response) VALUES (?, ?, ?)", 
                  (datetime.now().strftime("%H:%M:%S"), user_msg, reply))
        conn.commit()
        conn.close()
        
        return jsonify({"status": "success", "reply": reply})
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "reply": "Thinking... try again!"}), 500

# --- ADMIN ROUTES ---
@app.route('/admin-login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form.get('username') == ADMIN_USER and request.form.get('password') == ADMIN_PASS:
            session['logged_in'] = True
            return redirect(url_for('admin_portal'))
        error = "Invalid Credentials!"
    return render_template('login.html', error=error)

@app.route('/admin-portal')
def admin_portal():
    if not session.get('logged_in'): return redirect(url_for('login'))
    conn = sqlite3.connect('college_bot.db')
    conn.row_factory = sqlite3.Row
    knowledge = conn.execute('SELECT * FROM knowledge ORDER BY id DESC').fetchall()
    logs = conn.execute('SELECT * FROM logs ORDER BY id DESC LIMIT 50').fetchall()
    conn.close()
    return render_template('admin.html', knowledge=knowledge, logs=logs)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)


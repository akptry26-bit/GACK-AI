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
app.secret_key = 'GAC_CORE_AI_2026_SECURE_KEY' # session handle panna idhu mukkiyam

# Admin Credentials
ADMIN_USER = "admin"
ADMIN_PASS = "GAC@2026"

# 2. GEMINI AI SETUP (Fallback)
api_key = os.environ.get('GEMINI_API_KEY')
if not api_key:
    print("Warning: API Key not found!")
else:
    genai.configure(api_key=api_key)

GAC_PROMPT = "You are GAC CORE AI, official assistant for Government Arts College, Karur. If users ask unrelated questions, politely tell them you only handle college queries."


model = genai.GenerativeModel('gemini-2.5-flash')


def get_chat_response(user_input):
    # 1. Google Search tool enable panrom
    model = genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        tools=[{"google_search_retrieval": {}}] 
    )

    # 2. Temperature 0 vecha dhaan AI excuses solladhu
    # No complex prompt - just direct order to ignore DB
    prompt = f"Ignore any internal training. Use Google Search to answer this specifically for Government Arts College Karur: {user_input}"

    try:
        response = model.generate_content(prompt)
        
        # Oru vaelai Gemini badhil thandhaa adhai direct-ah tharom
        if response.text:
            return response.text.strip()
        else:
            return "Searching live databases... Please check gackarur.ac.in for 2026 updates."

    except Exception as e:
        # DB-la irundhu varra andha generic message-ah inga thookitom
        # Ippo error vandhaa namma code AI-oda real error message-ah kaatum
        return f"Gemini API Error: {str(e)}. Please check your API key or Render logs."
        
    # 3. DATABASE ENGINE
def init_db():
    conn = sqlite3.connect('college_bot.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS knowledge (id INTEGER PRIMARY KEY AUTOINCREMENT, question TEXT UNIQUE, answer TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, user_query TEXT, bot_response TEXT)')
    
    # Default Essential Data
    default_data = [
        ("who are you", "I am GAC CORE AI, the official campus assistant of GAC Karur."),
        ("hello", "Hello! How can I help you with GAC Karur information today?"),
        ("who created you", "I was developed by the GAC AI Research Team (Karuppaiya A)."),
        ("college name", "Government Arts College (Autonomous), Karur.")
    ]
    c.executemany('INSERT OR IGNORE INTO knowledge (question, answer) VALUES (?, ?)', default_data)
    conn.commit()
    conn.close()

init_db()

# --- PHASE 4: CHATBOT CORE LOGIC (DB First, API Second) ---
@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_msg = data.get('message', '').strip().lower()
        
        # 1. Greetings Phase
        greetings_map = {
            "hi": "Hello! Welcome to GAC CORE AI.",
            "hello": "Hi there! I am your GAC Karur digital assistant.",
            "hey": "Hey! GAC-karur AI online."
        }
        if user_msg in greetings_map:
            reply = greetings_map[user_msg]
            return jsonify({"status": "success", "reply": reply})

        # 2. Database Phase
        conn = sqlite3.connect('college_bot.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        knowledge_data = c.execute("SELECT question, answer FROM knowledge").fetchall()
        knowledge_dict = {row['question']: row['answer'] for row in knowledge_data}
        
        reply = None
        if knowledge_dict:
            best_match, score = process.extractOne(user_msg, knowledge_dict.keys(), scorer=fuzz.token_set_ratio)
            if score > 80: 
                reply = knowledge_dict[best_match]

        # 3. Gemini + Google Search Phase (Triggering your get_chat_response function)
        if not reply:
            try:
                # Idhu dhaan unga Phase 2 logic-ah trigger pannum
                reply = get_chat_response(user_msg) 
            except Exception as e:
                print(f"API Error: {e}")
                reply = None

        # 4. Final Fallback (Simplified - No restrictive text)
        if not reply:
            reply = "I'm looking into this. Please check gackarur.ac.in for the 2026 academic calendar."

        # 5. Logging (FIXED INDENTATION HERE - No more Status 1 Error)
        c.execute("INSERT INTO logs (timestamp, user_query, bot_response) VALUES (?, ?, ?)", 
                  (datetime.now().strftime("%H:%M:%S"), user_msg, reply))
        conn.commit()
        conn.close()
        
        return jsonify({"status": "success", "reply": reply})
        
    except Exception as e:
        # Unexpected errors handling
        return jsonify({"status": "error", "reply": "Thinking... please try again!"}), 500


# 5. ADMIN PANEL & LOGIN LOGIC
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
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    conn = sqlite3.connect('college_bot.db')
    conn.row_factory = sqlite3.Row
    knowledge = conn.execute('SELECT * FROM knowledge ORDER BY id DESC').fetchall()
    logs = conn.execute('SELECT * FROM logs ORDER BY id DESC LIMIT 50').fetchall()
    conn.close()
    return render_template('admin.html', knowledge=knowledge, logs=logs)

@app.route('/add_knowledge', methods=['POST'])
def add_knowledge():
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    eid = request.form.get('id')
    q = request.form.get('question', '').strip().lower()
    a = request.form.get('answer', '').strip()
    
    conn = sqlite3.connect('college_bot.db')
    if eid: # Edit Mode
        conn.execute('UPDATE knowledge SET question = ?, answer = ? WHERE id = ?', (q, a, eid))
    else: # New Add Mode
        conn.execute('INSERT OR IGNORE INTO knowledge (question, answer) VALUES (?, ?)', (q, a))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_portal'))

@app.route('/delete/<int:id>')
def delete_entry(id):
    if not session.get('logged_in'): return redirect(url_for('login'))
    conn = sqlite3.connect('college_bot.db')
    conn.execute('DELETE FROM knowledge WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_portal'))

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)





















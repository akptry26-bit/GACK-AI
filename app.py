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

# Step 1: Replace with your actual key


# Step 2: Use the most basic model
model = genai.GenerativeModel('gemini-2.5-flash') 
# Note: Experimental versions kasta-ma irundha 1.5-flash use panna stable-ah irukkum.

def get_live_google_response(user_input):
    try:
        # Dynamic-ah current date-ah eduthu 2026 updates-ku push panrom
        current_date = datetime.now().strftime("%B %d, 2026")
        
        # models/ prefix and -latest identifier is MUST to avoid 404
        model = genai.GenerativeModel(
            model_name='models/gemini-1.5',
            tools=[{"google_search_retrieval": {}}]
        )

        # STRICT INSTRUCTION: Tell AI to ignore 2024 data and use Google Search
        prompt = (
            f"Current Date: {current_date}. "
            f"MANDATORY: Use Google Search tool to provide the LATEST live info. "
            f"Do NOT use internal knowledge from 2024. Question: {user_input}"
        )

        response = model.generate_content(prompt)
        return response.text.strip() if response.text else None
    except Exception as e:
        print(f"Google Push Error: {e}")
        return None
        
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
@app.route('/ask', methods=['POST'])
def ask():
    try:
        user_message = request.json.get('message')
        # Gemini API call
        response = model.generate_content(user_message)
        return jsonify({'reply': response.text})
    except Exception as e:
        # Indha line-ah add pannunga, terminal-la enna error-nu kaattum
        print(f"Error: {e}") 
        return jsonify({'reply': 'LINK ERROR: Server connection failed.'})

# 4. CHATBOT CORE LOGIC (DB First, API Second)
@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_msg = data.get('message', '').strip().lower()
        reply = None

        # --- Phase 0: Greetings ---
        greetings = {"hi": "Hello! GAC CORE AI online.", "hello": "Hi! How can I help you?"}
        if user_msg in greetings:
            reply = greetings[user_msg]

        # --- Phase 1: Local DB Search ---
        if not reply:
            conn = sqlite3.connect('college_bot.db')
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            knowledge_data = c.execute("SELECT question, answer FROM knowledge").fetchall()
            knowledge_dict = {row['question']: row['answer'] for row in knowledge_data}
            if knowledge_dict:
                match, score = process.extractOne(user_msg, knowledge_dict.keys(), scorer=fuzz.token_set_ratio)
                if score > 85: reply = knowledge_dict[match]

        # --- Phase 2: GOOGLE SEARCH PUSH (The Real Fix) ---
        # DB-la illana automatic-ah Google-la irundhu 2026 data push aagum
        if not reply:
            reply = get_live_google_response(user_msg)

        # --- Phase 3: Final Fallback (Professional) ---
        if not reply:
            reply = "I'm having trouble fetching live data. Please check gackarur.ac.in for 2026 updates."

        # Logging (Fixed spacing to avoid Line 154 error)
        conn = sqlite3.connect('college_bot.db')
        c = conn.cursor()
        c.execute("INSERT INTO logs (timestamp, user_query, bot_response) VALUES (?, ?, ?)", 
                  (datetime.now().strftime("%H:%M:%S"), user_msg, reply))
        conn.commit()
        conn.close()
        
        return jsonify({"status": "success", "reply": reply})

    except Exception as e:
        print(f"Critical Error: {e}")
        return jsonify({"status": "error", "reply": "Thinking... try again!"}), 500


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

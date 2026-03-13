import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import google.generativeai as genai
from dotenv import load_dotenv
from thefuzz import process, fuzz
from datetime import datetime
import json

# JSON data-vah load panna oru function
def load_college_data():
    with open('data.json', 'r') as f:
        return json.load(f)

# Data-vah oru variable-la vechukonga
college_info = load_college_data()

def update_json(new_question, new_answer):
    # 1. Read existing data
    data = load_college_data()
    
    # 2. Add new data (Unga structure-ku thaguntha maari)
    if 'custom_qa' not in data:
        data['custom_qa'] = []
    data['custom_qa'].append({"q": new_question, "a": new_answer})
    
    # 3. Write back to file
    with open('data.json', 'w') as f:
        json.dump(data, f, indent=4)
        
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





def get_live_college_info(user_query):
    try:
        # 1. LIVE DATE FORCE: March 2026 updates-ku idhu dhaan base
        today = datetime.now().strftime("%B %d, 2026")
        
        # 2. v1beta CONFIGURATION:
        model = genai.GenerativeModel(
            model_name='models/gemini-2.5-flash',
            tools=[{"google_search_retrieval": {}}]
        )

        # 3. THE "STRICT ANALYZER" PROMPT:
        # AI-kitta "Browse gackarur.ac.in" nu direct order podrom.
        prompt = (
    "Current Date: March 13, 2026. "
    "MANDATORY: You are an assistant for GAC Karur. "
    "MANDATORY: Use Google Search to browse ONLY 'gackarur.ac.in'. "
    "CRITICAL: Do NOT invent names. If you cannot find the actual staff names on the website, "
    "simply say: 'Official staff list is currently not reachable on the website portal.' "
    "Do NOT give generic English names like Eleanor or Michael. Only give names found on gackarur.ac.in."
    f"Query: {user_query}"
)

        # Generating content using the tool
        response = model.generate_content(prompt)
        
        if response.text:
            return response.text.strip()
            
    except Exception as e:
        print(f"v1beta Tool Error: {e}")
        return "I'm checking the live GAC Karur portal. For official 2026 dates, visit gackarur.ac.in."
        
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
        ("Principal", "Dr. K. VASUDEVAN , M.A., M.Phil., B.Ed., Ph.D.,"),
        ("cs hod name", "Dr. M. PRABAKARAN, M.Sc., M.Phil., M.C.A., MBA., M.Tech., Ph.D.,"),
        ("242513", "karuppaiya")
        ("Department of COMPUTER SCIENCE","Computer Science Department was started in the academic year 1988-89.
        ✅It is notable that the Computer Science Course (B.Sc) with co-education (1988-89) in Tamilnadu was first started in our college only.
        ✅In the academic year 2007-2008 another B.Sc Computer Science ( Shift II ) was started as per the Tamilnadu Government Order.
        ✅In the academic year 2004-2005 Post Graduate Course ( M.Sc ) was started.
        ✅The sanctioned strength is 60 ( 30 + 30 ) for under graduate Programmes and 30 for post graduate Programme.
        ✅Research Programmes such as M.Phil and Ph.D was started in the year 2011-2012 academic year.
        ✅Full time and Part time research Programmes are offered and it was approved by both Government of Tamilnadu and Bharathidasan University, Tiruchirapalli, with sanctioned strength of 25 for M.Phil and 16 for Ph.D.
        ✅The Department is functioning successfully with Eight regular staff members and Four guest lecturers.")
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
        
        # --- PHASE 0: Instant Response (Greetings) ---
        # Database-ku munnadiye idhu check pannum, so fast-ah irukkum
        greetings_map = {
            "hi": "Hello! Welcome to GAC CORE AI. How can I help you today?",
        "hello": "Hi there! I am your GAC Karur digital assistant. Ask me anything!",
        "hey": "Hey! GAC-karur AI online. What's on your mind?",
        "gm": "Good Morning! Wishing you a wonderful and productive day at GAC Karur.",
        "good morning": "Good Morning! Hope you have a great day ahead!",
        "gn": "Good Night! Rest well. I'll be here if you need anything tomorrow.",
        "good night": "Good Night! Sleep well. System entering low-power mode.",
        
        "thank you": "You're very welcome! Glad I could help.",
        "thanks": "No problem! Happy to assist a GAC student."
        }

        if user_msg in greetings_map:
            reply = greetings_map[user_msg]
            # Log panniye aaganum admin-ku theriya
            conn = sqlite3.connect('college_bot.db')
            c = conn.cursor()
            c.execute("INSERT INTO logs (timestamp, user_query, bot_response) VALUES (?, ?, ?)", 
                      (datetime.now().strftime("%H:%M:%S"), user_msg, reply))
            conn.commit()
            conn.close()
            return jsonify({"status": "success", "reply": reply})

        # --- PHASE 1: Local Knowledge Base Search (Existing Code) ---
        conn = sqlite3.connect('college_bot.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        knowledge_data = c.execute("SELECT question, answer FROM knowledge").fetchall()
        knowledge_dict = {row['question']: row['answer'] for row in knowledge_data}
        
        reply = None
        if knowledge_dict:
            best_match, score = process.extractOne(user_msg, knowledge_dict.keys(), scorer=fuzz.token_set_ratio)
            if score > 70: # Konjam threshold-ah kuraichuruken (75 -> 70) for better results
                reply = knowledge_dict[best_match]

        # Phase 2: Gemini AI
        if not reply and model:
            try:
                response = model.generate_content(user_msg)
                reply = response.text
            except:
                reply = None

        # Phase 3: Final Fallback
        if not reply:
            reply = "I am trained to answer questions only about GAC Karur. Please ask about courses, principal, or admissions."

        # Logging
        c.execute("INSERT INTO logs (timestamp, user_query, bot_response) VALUES (?, ?, ?)", 
                  (datetime.now().strftime("%H:%M:%S"), user_msg, reply))
        conn.commit()
        conn.close()
        
        return jsonify({"status": "success", "reply": reply})
        
    except Exception as e:
        print(f"Error: {e}") # Terminal-la enna error-nu paakka
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


























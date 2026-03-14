import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import google.generativeai as genai
from dotenv import load_dotenv
from thefuzz import process, fuzz
from datetime import datetime

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
    "Current Date: March 14, 2026. "
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
        ("242513", "karuppaiya"),
   
# --- FACILITIES ---
        ("library details", "The central library has over 60,000 books, 80 journals, and a modern digital library section."),
        ("hostel facilities", "There are separate hostels for boys and girls with safe accommodation and healthy food."),
        ("shift timings", "Shift 1: 08:45 AM to 01:40 PM. Shift 2: 01:45 PM to 06:15 PM."),
        ("wifi and labs", "The campus is Wi-Fi enabled, and all science departments have well-equipped individual laboratories."),
# --- CAMPUS RULES & TIMINGS ---
        ("attendance rule", "Students must maintain a minimum of 75% attendance to appear for Semester Examinations."),
        ("id card policy", "Wearing the College ID card is mandatory inside the campus at all times."),
        ("ragging policy", "GAC Karur is a Ragging-Free campus. Ragging is strictly prohibited and punishable."),
        ("office hours", "The college office works from 10:00 AM to 05:45 PM on all working days."),
        ("Department of COMPUTER SCIENCE", """ ✅Computer Science Department was started in the academic year 1988-89,
        ✅It is notable that the Computer Science Course (B.Sc) with co-education (1988-89) in Tamilnadu was first started in our college only.
        ✅In the academic year 2007-2008 another B.Sc Computer Science ( Shift II ) was started as per the Tamilnadu Government Order.
        ✅In the academic year 2004-2005 Post Graduate Course ( M.Sc ) was started.
        ✅The sanctioned strength is 60 ( 30 + 30 ) for under graduate Programmes and 30 for post graduate Programme.
        ✅Research Programmes such as M.Phil and Ph.D was started in the year 2011-2012 academic year.
        ✅Full time and Part time research Programmes are offered and it was approved by both Government of Tamilnadu and Bharathidasan University, Tiruchirapalli, with sanctioned strength of 25 for M.Phil and 16 for Ph.D.
        ✅The Department is functioning successfully with Eight regular staff members and Four guest lecturers. """)
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





# --- STEP 2: The Final Chat Route ---
@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_msg = data.get('message', '').strip().lower()
        
        # 1. Greetings (Instant)
        greetings = {"hi": "Hello!", "hello": "Hi! GAC AI online.", "thanks": "Welcome!"}
        if user_msg in greetings:
            return jsonify({"status": "success", "reply": greetings[user_msg]})

        # 2. Strength Data (Custom Logic)
        strength_reply = get_cs_strength(user_msg) 
        if strength_reply:
            return jsonify({"status": "success", "reply": strength_reply})

        # 3. Local Data Search (The Tuple List from your screenshot)
        # Indha loop mela neenga anupuna andha 'default_data' list-ah check pannum
        for question, answer in default_data:
            if question.lower() in user_msg:
                return jsonify({"status": "success", "reply": answer})

        # --- PHASE 2: Gemini AI with Google Search (Updated) ---
        if not reply and model:
            try:
                # Tools-la 'google_search_retrieval' add panna dhaan search aagum
                # Model configure pannum bodhu idhu irukanum
                response = model.generate_content(
                    f"You are the GAC Karur Assistant. User asked: {user_msg}",
                    tools=[{'google_search_retrieval': {}}] # <--- Google Search Power!
                )
                
                if response and response.text:
                    reply = response.text
            except Exception as e:
                # Oru vela search fail aana, normal Gemini-ah call pannum
                response = model.generate_content(f"Answer briefly: {user_msg}")
                reply = response.text if response else None

        # 5. Final Fallback
        return jsonify({"status": "success", "reply": "I am trained for GAC Karur info. Can you be more specific?"})

    except Exception as e:
        # Error vandha 'Offline' nu sollaama, Gemini-ku redirect panna vaikkalam
        return jsonify({"status": "success", "reply": "Thinking... try asking again!"})


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





























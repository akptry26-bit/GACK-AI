import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session,
redirect, url_for
import google.generativeai as genai
from dotenv import load_dotenv
from thefuzz import process, fuzz
load_dotenv()
app = Flask(__name__)
app.secret_key = 'GAC_CORE_AI_2026_SECURE_KEY' # session handle panna
idhu mukkiyam
ADMIN_USER = "admin"
ADMIN_PASS = "GAC@2026"
api_key = os.environ.get('GEMINI_API_KEY')
if not api_key:
    print("Warning: API Key
not found!")
else:
   genai.configure(api_key=api_key)
GAC_PROMPT = "You are GAC CORE AI, official assistant for
Government Arts College, Karur. If users ask unrelated questions, politely tell
them you only handle college queries."
model = genai.GenerativeModel('gemini-2.5-flash') 
def get_live_google_response(user_input):
    try:
        current_date =
datetime.now().strftime("%B %d, 2026")
        model =
genai.GenerativeModel(
           model_name='models/gemini-1.5',
           tools=[{"google_search_retrieval": {}}]
        )
        prompt = (
            f"Current Date:
{current_date}. "
            f"MANDATORY: Use
Google Search tool to provide the LATEST live info. "
            f"Do NOT use
internal knowledge from 2024. Question: {user_input}"
        )
        response =
model.generate_content(prompt)
        return
response.text.strip() if response.text else None
    except Exception as e:
        print(f"Google Push
Error: {e}")
        return None
def init_db():
    conn =
sqlite3.connect('college_bot.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT
EXISTS knowledge (id INTEGER PRIMARY KEY AUTOINCREMENT, question TEXT UNIQUE,
answer TEXT)')
    c.execute('CREATE TABLE IF NOT
EXISTS logs (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, user_query
TEXT, bot_response TEXT)')
    default_data = [
        ("who are you",
"I am GAC CORE AI, the official campus assistant of GAC Karur."),
        ("hello",
"Hello! How can I help you with GAC Karur information today?")    ]
    c.executemany('INSERT OR
IGNORE INTO knowledge (question, answer) VALUES (?, ?)', default_data)
    conn.commit()
    conn.close()
init_db()
 
 
@app.route('/admin-login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if
request.form.get('username') == ADMIN_USER and request.form.get('password') ==
ADMIN_PASS:
            session['logged_in'] =
True
            return
redirect(url_for('admin_portal'))
        error = "Invalid
Credentials!"
    return
render_template('login.html', error=error)
@app.route('/admin-portal')
def admin_portal():
    if not
session.get('logged_in'):
        return
redirect(url_for('login'))
    conn =
sqlite3.connect('college_bot.db')
    conn.row_factory = sqlite3.Row
    knowledge =
conn.execute('SELECT * FROM knowledge ORDER BY id DESC').fetchall()
    logs = conn.execute('SELECT *
FROM logs ORDER BY id DESC LIMIT 50').fetchall()
    conn.close()
    return
render_template('admin.html', knowledge=knowledge, logs=logs)
@app.route('/add_knowledge', methods=['POST'])
def add_knowledge():
    if not
session.get('logged_in'): return redirect(url_for('login'))
    eid = request.form.get('id')
    q =
request.form.get('question', '').strip().lower()
    a = request.form.get('answer',
'').strip()
    conn =
sqlite3.connect('college_bot.db')
    if eid: 
        conn.execute('UPDATE
knowledge SET question = ?, answer = ? WHERE id = ?', (q, a, eid))
    else: 
        conn.execute('INSERT OR
IGNORE INTO knowledge (question, answer) VALUES (?, ?)', (q, a))
    conn.commit()
    conn.close()
    return
redirect(url_for('admin_portal'))
@app.route('/delete/<int:id>')
def delete_entry(id):
    if not
session.get('logged_in'): return redirect(url_for('login'))
    conn =
sqlite3.connect('college_bot.db')
    conn.execute('DELETE FROM
knowledge WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return
redirect(url_for('admin_portal'))
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return
redirect(url_for('login'))
@app.route('/')
def index():
    return
render_template('index.html')
if __name__ == '__main__':
    app.run(host='0.0.0.0',
port=5000, debug=True)
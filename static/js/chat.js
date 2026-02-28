/**
 * GAC CORE NEURAL ENGINE v3.0
 * Deep Link Logic for Academic Information
 */

const scroller = document.getElementById('chat-scroller');
const inputField = document.getElementById('query-input');
const submitBtn = document.getElementById('submit-btn');
const systemStatus = document.getElementById('engine-status');

// 1. Theme Configuration
function toggleTheme() {
    const isLight = document.body.classList.toggle('light-mode');
    const icon = document.getElementById('theme-toggle-btn').querySelector('i');
    icon.className = isLight ? 'fas fa-sun' : 'fas fa-moon';
    localStorage.setItem('gac-core-theme', isLight ? 'light' : 'dark');
}

// 2. Messaging Core (THE FIX)
async function handleSubmission() {
    const queryText = inputField.value.trim();
    if (!queryText) return;

    // Reset UI for next input
    inputField.value = '';
    inputField.disabled = true;
    systemStatus.innerText = "QUERYING NEURAL DATABASE...";
    systemStatus.style.color = "var(--accent)";

    // 1. Render User Message
    renderMessage(queryText, 'user');

    // 2. Render AI Thinking Bubble
    const aiId = `ai-link-${Date.now()}`;
    const loader = renderMessage('<span class="neural-pulse">Analyzing academic packets...</span>', 'bot', aiId);

    try {
        // MUKKIYAM: Intha fetch URL /chat nu Flask la irukanum
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: queryText })
        });

        if (!response.ok) throw new Error("Database Link Failure");

        const data = await response.json();

        // 3. Finalize Response with Delay
        setTimeout(() => {
            loader.querySelector('.chat-bubble').innerText = data.reply;
            systemStatus.innerText = "NEURAL SYSTEM ONLINE";
            systemStatus.style.color = "#10b981";
            finalizeSession();
        }, 650);

    } catch (err) {
        loader.querySelector('.chat-bubble').innerText = "LINK ERROR: Database engine is currently offline. Ensure Python server is running.";
        systemStatus.innerText = "SYSTEM FAULT DETECTED";
        systemStatus.style.color = "#ef4444";
        finalizeSession();
    }
}

// 3. UI Factory Functions
function renderMessage(content, type, id = null) {
    const timeNow = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const msgDiv = document.createElement('div');
    msgDiv.className = `message-row ${type}-row animate-in`;
    if(id) msgDiv.id = id;

    const iconType = type === 'bot' ? 'fa-robot' : 'fa-user-graduate';

    msgDiv.innerHTML = `
        <div class="avatar-shroud"><i class="fas ${iconType}"></i></div>
        <div class="bubble-stack">
            <div class="chat-bubble">${content}</div>
            <span class="time-stamp">${timeNow}</span>
        </div>
    `;

    scroller.appendChild(msgDiv);
    scrollDown();
    return msgDiv;
}

function scrollDown() {
    scroller.scrollTo({ top: scroller.scrollHeight, behavior: 'smooth' });
}

function finalizeSession() {
    inputField.disabled = false;
    inputField.focus();
}

function autoInput(val) {
    inputField.value = val;
    handleSubmission();
}

// 4. Global Event Handlers
submitBtn.onclick = handleSubmission;
inputField.onkeypress = (e) => { if (e.key === 'Enter') handleSubmission(); };

// Initialization
window.onload = () => {
    if (localStorage.getItem('gac-core-theme') === 'light') toggleTheme();
    inputField.focus();
    console.log("%c GAC NEURAL LINK v3.0 ONLINE ", "background: #00d2ff; color: #000; font-weight: bold; padding: 8px;");
};


async function sendMessage() {
    const input = document.getElementById('user-input'); // Unga ID check pannunga
    const message = input.value.trim();
    
    if(!message) return;

    // UI-la message-ah kaatunga
    appendUserMessage(message); 
    input.value = '';

    try {
        // MUKKIYAM: URL must be '/chat'
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message })
        });

        const data = await response.json();
        appendBotMessage(data.reply); // Bot reply-ah display panna

    } catch (error) {
        console.error("Error:", error);
        appendBotMessage("Connection failed. Check if Flask is running!");
    }

}

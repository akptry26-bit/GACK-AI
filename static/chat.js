/**
 * GAC CORE NEURAL ENGINE v2.0
 * Advanced Interaction Logic
 */

const messageContainer = document.getElementById('message-container');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const engineStatus = document.getElementById('engine-status');

// 1. Theme Orchestration Logic
function toggleTheme() {
    const body = document.body;
    const themeIcon = document.getElementById('theme-icon');
    
    body.classList.toggle('light-mode');
    
    if (body.classList.contains('light-mode')) {
        themeIcon.className = 'fas fa-sun';
        localStorage.setItem('core-theme', 'light');
    } else {
        themeIcon.className = 'fas fa-moon';
        localStorage.setItem('core-theme', 'dark');
    }
}

// 2. Message Dispatcher
async function dispatchMessage() {
    const rawInput = userInput.value.trim();
    if (!rawInput) return;

    // UI State Management
    userInput.value = '';
    userInput.disabled = true;
    engineStatus.innerText = "PROCESSING NEURAL PATHS...";
    engineStatus.parentElement.querySelector('.status-dot').style.background = "#00f2ff";

    // 1. Render User Bubble
    renderBubble(rawInput, 'user');

    // 2. Render AI Thinking State
    const aiResponseId = `ai-${Date.now()}`;
    const aiBubble = renderBubble('<span class="neural-pulse">Analyzing...</span>', 'ai', aiResponseId);

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: rawInput })
        });

        if (!response.ok) throw new Error("Link Severed");

        const data = await response.json();

        // Simulate typing delay for AI realism
        setTimeout(() => {
            simulateTyping(aiBubble, data.reply);
            resetUIState();
        }, 800);

    } catch (error) {
        aiBubble.querySelector('.text-content').innerText = "FATAL ERROR: Failed to communicate with GAC Database Core.";
        resetUIState(true);
    }
}

// 3. Interface Builders
function renderBubble(content, sender, id = null) {
    const msgTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${sender}-entry animate-in`;
    if(id) msgDiv.id = id;

    const icon = sender === 'ai' ? 'fa-robot' : 'fa-user-graduate';
    const header = sender === 'ai' ? 'SYSTEM CORE' : 'TERMINAL ACCESS';

    msgDiv.innerHTML = `
        <div class="avatar-box"><i class="fas ${icon}"></i></div>
        <div class="bubble-wrap">
            <div class="bubble">
                <div class="bubble-header">${header}</div>
                <div class="text-content">${content}</div>
            </div>
            <span class="msg-time">${msgTime}</span>
        </div>
    `;

    messageContainer.appendChild(msgDiv);
    autoScroll();
    return msgDiv;
}

function simulateTyping(element, text) {
    const textTarget = element.querySelector('.text-content');
    textTarget.innerText = text;
    autoScroll();
}

function autoScroll() {
    messageContainer.scrollTo({ top: messageContainer.scrollHeight, behavior: 'smooth' });
}

function resetUIState(isError = false) {
    userInput.disabled = false;
    userInput.focus();
    engineStatus.innerText = isError ? "SYSTEM FAULT DETECTED" : "NEURAL ENGINE ONLINE";
    engineStatus.parentElement.querySelector('.status-dot').style.background = isError ? "#ef4444" : "#10b981";
}

// 4. Shortcut Handlers
function quickFill(text) {
    userInput.value = text;
    dispatchMessage();
}

// 5. Global Listeners
sendBtn.addEventListener('click', dispatchMessage);

userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') dispatchMessage();
});

// Initialization Sequence
window.onload = () => {
    if (localStorage.getItem('core-theme') === 'light') toggleTheme();
    userInput.focus();
    console.log("%c GAC NEURAL LINK INITIALIZED SUCCESSFUL ", "background: #00f2ff; color: #000; font-weight: bold; padding: 5px;");
};
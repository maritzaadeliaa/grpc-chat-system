const loginContainer = document.getElementById('login-container');
const chatContainer = document.getElementById('chat-container');
const loginForm = document.getElementById('login-form');
const chatForm = document.getElementById('chat-form');
const messagesBox = document.getElementById('messages-box');
const messageInput = document.getElementById('message-input');

let ws = null;
let currentUsername = "";

function appendMessage(msg, typeClass, senderName) {
    const el = document.createElement('div');
    el.classList.add('message', typeClass);
    
    const now = new Date();
    const timeStr = now.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    
    if (typeClass === 'system') {
        el.innerHTML = `<div class="text">${msg}</div>`;
    } else {
        const nameHtml = senderName ? `<div class="sender-name">${senderName}</div>` : '';
        el.innerHTML = `
            ${nameHtml}
            <div class="bubble">
                <span class="msg-text">${msg}</span>
                <span class="time">${timeStr}</span>
            </div>
        `;
    }
    
    messagesBox.appendChild(el);
    // Auto scroll to bottom
    messagesBox.scrollTop = messagesBox.scrollHeight;
}

loginForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const username = document.getElementById('username').value.trim();
    const room = document.getElementById('room').value.trim();
    
    if (!username || !room) return;
    
    // Save to sessionStorage
    sessionStorage.setItem('username', username);
    sessionStorage.setItem('room', room);
    
    currentUsername = username;
    document.getElementById('current-room').innerText = "Room: " + room;
    document.getElementById('current-user').innerText = "@" + username;
    
    // Sembunyikan warning sebelumnya (jika ada)
    document.getElementById('login-warning').style.display = 'none';

    // Disable button and change text
    const submitBtn = loginForm.querySelector('button');
    submitBtn.disabled = true;
    submitBtn.innerText = "Connecting...";

    // Establish WebSocket Connection
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/${encodeURIComponent(username)}/${encodeURIComponent(room)}`;
    
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        appendMessage("WebSocket Connected", "system");
    };

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            if (data.type === 'login_status') {
                if (data.status === 'SUCCESS') {
                    // Berhasil login, barulah kita ganti ke UI chat
                    loginContainer.style.display = 'none';
                    chatContainer.style.display = 'flex';
                    messagesBox.innerHTML = '';
                    appendMessage("Connected to server", "system");
                    appendMessage(data.message, "system");
                } else {
                    // Gagal login/Username taken
                    const warnEl = document.getElementById('login-warning');
                    warnEl.innerText = data.message;
                    warnEl.style.display = 'block';
                    
                    const submitBtn = loginForm.querySelector('button');
                    submitBtn.disabled = false;
                    submitBtn.innerText = "Join Space";
                    
                    ws.close();
                }
            } else if (data.type === 'system') {
                appendMessage(data.message, "system");
            } else if (data.type === 'chat') {
                if (data.message === "[JOIN]") {
                    appendMessage(`${data.username} joined the room!`, "system");
                    return;
                }
                const isMine = data.username === currentUsername;
                appendMessage(data.message, isMine ? 'mine' : 'other', isMine ? null : data.username);
            } else if (data.type === 'error') {
                appendMessage("Error: " + data.message, "system");
                ws.close();
            }
        } catch(e) {
            console.error("Failed to parse msg:", event.data);
        }
    };

    ws.onclose = () => {
        appendMessage("Disconnected from server", "system");
        ws = null;
        
        // Reset tombol login jika websocket terputus saat masih loading
        const submitBtn = loginForm.querySelector('button');
        if (submitBtn.disabled) {
            submitBtn.disabled = false;
            submitBtn.innerText = "Join Space";
            const warnEl = document.getElementById('login-warning');
            warnEl.innerText = "Connection failed / Server closed.";
            warnEl.style.display = 'block';
        }
    };
});

chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const txt = messageInput.value.trim();
    if (txt && ws && ws.readyState === WebSocket.OPEN) {
        // Tampilkan pesan kita sendiri di layar (optimistic rendering)
        appendMessage(txt, 'mine', null);
        
        // Send message to python websocket backend
        ws.send(txt);
        messageInput.value = "";
    }
});

document.getElementById('leave-btn').addEventListener('click', () => {
    if (ws) {
        ws.close();
    }
    // Clear session
    sessionStorage.removeItem('username');
    sessionStorage.removeItem('room');
    
    chatContainer.style.display = 'none';
    loginContainer.style.display = 'block';
    document.getElementById('username').value = "";
    document.getElementById('room').value = "";
});

// Auto-login if session exists
window.addEventListener('DOMContentLoaded', () => {
    const savedUser = sessionStorage.getItem('username');
    const savedRoom = sessionStorage.getItem('room');
    if (savedUser && savedRoom) {
        document.getElementById('username').value = savedUser;
        document.getElementById('room').value = savedRoom;
        
        // Buat trigger event submit secara manual
        loginForm.dispatchEvent(new Event('submit'));
    }
});

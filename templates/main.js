document.addEventListener("DOMContentLoaded", () => {
    loadRecommendations();
});

function loadRecommendations() {
    fetch('/recommend')
        .then(res => res.json())
        .then(data => {
            const container = document.getElementById('recommendations');
            if (!container) return;
            container.innerHTML = '';
            data.recommendations.forEach(r => {
                const div = document.createElement('div');
                div.innerHTML = `
                    <strong>${r.title}</strong> by ${r.owner} 
                    <button onclick="bookSession(${r.skill_id})">Book Session</button>
                `;
                container.appendChild(div);
            });
        });
}

function bookSession(skillId) {
    fetch(`/book/${skillId}`, {method:'POST'})
        .then(res => res.blob())
        .then(blob => {
            const url = URL.createObjectURL(blob);
            const img = document.createElement('img');
            img.src = url;
            img.alt = 'QR Code';
            document.body.appendChild(img);
        });
}

function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value;
    if(!message) return;

    const chatWindow = document.getElementById('chat-window');
    const userMsg = document.createElement('p');
    userMsg.innerHTML = `<strong>You:</strong> ${message}`;
    chatWindow.appendChild(userMsg);

    fetch('/chatbot', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({message})
    })
    .then(res => res.json())
    .then(data => {
        const botMsg = document.createElement('p');
        botMsg.innerHTML = `<strong>Bot:</strong> ${data.reply}`;
        chatWindow.appendChild(botMsg);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    });

    input.value = '';
}
function bookSession(skillId) {
    fetch(`/pay/${skillId}`, { method: 'POST' })
    .then(res => res.blob())
    .then(blob => {
        const url = URL.createObjectURL(blob);
        const img = document.createElement('img');
        img.src = url;
        img.alt = 'Booking QR Code';
        document.body.appendChild(img);
    };
}


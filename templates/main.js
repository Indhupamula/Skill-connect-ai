// main.js - frontend interactions for SkillConnect AI

document.addEventListener("DOMContentLoaded", () => {
  // If a recommendations area exists, try to load recommendations
  if (document.getElementById('recommendations')) {
    loadRecommendations();
  }
});

// Load simple recommendations (calls /recommend)
function loadRecommendations() {
  fetch('/recommend')
    .then(res => res.json())
    .then(data => {
      const container = document.getElementById('recommendations');
      if (!container) return;
      container.innerHTML = '';
      (data.recommendations || []).forEach(r => {
        const div = document.createElement('div');
        div.className = 'skill-card';
        div.innerHTML = `
          <h3>${escapeHtml(r.title)}</h3>
          <p>Owner: ${escapeHtml(r.owner)}</p>
          <p>Price: $${r.price ?? 'N/A'}</p>
          <button onclick="bookSkill(${r.skill_id})">Book Session</button>
        `;
        container.appendChild(div);
      });
    })
    .catch(err => console.error('Failed to load recommendations', err));
}

// Book a skill -> request backend to create booking + QR
function bookSkill(skillId) {
  fetch(`/book/${skillId}`, { method: 'POST' })
    .then(res => res.json())
    .then(data => {
      if (data.error) {
        alert(data.error);
        return;
      }
      if (data.qr) {
        showQrModal(data.qr);
      } else {
        alert('Booked successfully.');
      }
    })
    .catch(err => {
      console.error(err);
      alert('Booking failed.');
    });
}

// Display QR in a simple modal-like overlay
function showQrModal(qrPath) {
  // create overlay
  const overlay = document.createElement('div');
  overlay.style.position = 'fixed';
  overlay.style.left = 0;
  overlay.style.top = 0;
  overlay.style.width = '100%';
  overlay.style.height = '100%';
  overlay.style.background = 'rgba(0,0,0,0.6)';
  overlay.style.display = 'flex';
  overlay.style.alignItems = 'center';
  overlay.style.justifyContent = 'center';
  overlay.style.zIndex = 9999;

  const box = document.createElement('div');
  box.style.background = '#fff';
  box.style.padding = '20px';
  box.style.borderRadius = '8px';
  box.style.textAlign = 'center';
  box.innerHTML = `<h3>Booking Confirmed</h3><p>Scan this QR at the session</p>`;

  const img = document.createElement('img');
  img.src = qrPath;
  img.alt = 'QR Code';
  img.style.maxWidth = '260px';
  img.style.display = 'block';
  img.style.margin = '12px auto';

  const closeBtn = document.createElement('button');
  closeBtn.textContent = 'Close';
  closeBtn.style.marginTop = '8px';
  closeBtn.onclick = () => document.body.removeChild(overlay);

  box.appendChild(img);
  box.appendChild(closeBtn);
  overlay.appendChild(box);
  document.body.appendChild(overlay);
}

// Chatbot: send message to /chatbot and show reply
function sendMessage() {
  const input = document.getElementById('chat-input');
  if (!input) return;
  const message = input.value.trim();
  if (!message) return;

  const chatWindow = document.getElementById('chat-window');
  appendChatMessage('You', message, chatWindow);

  fetch('/chatbot', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ message })
  })
    .then(res => res.json())
    .then(data => {
      appendChatMessage('Bot', data.reply || 'Sorry, no response.', chatWindow);
    })
    .catch(err => {
      console.error(err);
      appendChatMessage('Bot', 'Error contacting chatbot.', chatWindow);
    });

  input.value = '';
  input.focus();
}

function appendChatMessage(sender, text, container) {
  if (!container) return;
  const p = document.createElement('p');
  p.innerHTML = `<strong>${escapeHtml(sender)}:</strong> ${escapeHtml(text)}`;
  container.appendChild(p);
  container.scrollTop = container.scrollHeight;
}

// utility: basic html escape
function escapeHtml(unsafe) {
  if (unsafe === null || unsafe === undefined) return '';
  return String(unsafe)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

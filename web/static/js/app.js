// web/static/js/app.js
(function () {
  function $(id) { return document.getElementById(id); }
  function append(role, text) {
    const s = $('chat-stream');
    const el = document.createElement('div');
    el.className = 'msg ' + role;
    el.textContent = text;
    s.appendChild(el);
    s.scrollTop = s.scrollHeight;
  }

  async function sendChat() {
    const input = $('chat-input');
    const text = (input.value || '').trim();
    if (!text) return;
    append('user', text);
    input.value = '';
    try {
      const res = await fetch('/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: text })
      });
      const data = await res.json();
      append('agent', data.answer || '(no answer)');
    } catch (e) {
      append('agent', '(request failed)');
    }
  }

  async function contact() {
    try {
      await fetch('/contact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason: 'user_clicked_contact' })
      });
      alert('We have emailed support.');
    } catch (e) {
      alert('Contact failed.');
    }
  }

  function toggleSidebar() {
    const sidebar = $('sidebar');
    const btn = $('sidebar-toggle');
    const expanded = btn.getAttribute('aria-expanded') === 'true';
    btn.setAttribute('aria-expanded', expanded ? 'false' : 'true');
    sidebar.classList.toggle('sidebar--collapsed', expanded);
  }

  window.addEventListener('DOMContentLoaded', () => {
    const sendBtn = $('chat-send');
    const input = $('chat-input');
    const contactBtn = $('contact-btn');
    const toggleBtn = $('sidebar-toggle');

    if (sendBtn) sendBtn.addEventListener('click', sendChat);
    if (input) input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') sendChat();
    });
    if (contactBtn) contactBtn.addEventListener('click', contact);
    if (toggleBtn) toggleBtn.addEventListener('click', toggleSidebar);
  });
})();


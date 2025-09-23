// web/static/js/app.js
(function () {
  function $(id) { return document.getElementById(id); }

  function append(role, text) {
    const stream = $('chat-stream');
    if (!stream) return;
    const wrapper = document.createElement('div');
    wrapper.className = 'msg msg--' + role;
    const bubble = document.createElement('div');
    bubble.className = 'msg__bubble';
    bubble.textContent = text;
    wrapper.appendChild(bubble);
    stream.appendChild(wrapper);
    stream.scrollTop = stream.scrollHeight;
  }

  async function sendChat() {
    const input = $('chat-input');
    if (!input) return;
    const text = (input.value || '').trim();
    if (!text) return;
    append('user', text);
    input.value = '';
    input.focus();
    try {
      const res = await fetch('/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: text })
      });
      if (!res.ok) {
        throw new Error('Request failed');
      }
      const data = await res.json();
      append('agent', data.answer || 'No answer returned.');
    } catch (err) {
      append('agent', 'Sorry, something went wrong. Please try again.');
      console.error(err);
    }
  }

  async function contact() {
    try {
      const res = await fetch('/contact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason: 'user_clicked_contact' })
      });
      if (!res.ok) {
        throw new Error('Contact failed');
      }
      alert('We have emailed support.');
    } catch (err) {
      console.error(err);
      alert('We could not send the escalation email.');
    }
  }

  function setSidebarState(collapsed) {
    const sidebar = $('sidebar');
    if (!sidebar) return;
    sidebar.classList.toggle('sidebar--collapsed', collapsed);
    const layout = document.querySelector('.layout');
    if (layout) {
      layout.classList.toggle('layout--sidebar-collapsed', collapsed);
    }
    document.querySelectorAll('[data-sidebar-toggle]').forEach((btn) => {
      btn.setAttribute('aria-expanded', collapsed ? 'false' : 'true');
    });
  }

  function toggleSidebar() {
    const sidebar = $('sidebar');
    if (!sidebar) return;
    const isCollapsed = sidebar.classList.contains('sidebar--collapsed');
    setSidebarState(!isCollapsed);
  }

  window.addEventListener('DOMContentLoaded', () => {
    const sendBtn = $('chat-send');
    const input = $('chat-input');
    const contactBtn = $('contact-btn');
    const sidebar = $('sidebar');
    const form = document.querySelector('.chat__composer');

    if (sendBtn) sendBtn.addEventListener('click', sendChat);
    if (input) {
      input.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' && !event.shiftKey) {
          event.preventDefault();
          sendChat();
        }
      });
    }
    if (form) {
      form.addEventListener('submit', (event) => event.preventDefault());
    }
    if (contactBtn) contactBtn.addEventListener('click', contact);
    document.querySelectorAll('[data-sidebar-toggle]').forEach((btn) => {
      btn.addEventListener('click', toggleSidebar);
    });

    if (sidebar) {
      const collapsed = sidebar.classList.contains('sidebar--collapsed');
      setSidebarState(collapsed);
    }

    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') {
        setSidebarState(true);
      }
    });
  });
})();


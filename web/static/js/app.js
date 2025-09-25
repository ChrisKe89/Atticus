// web/static/js/app.js
(function () {
  function $(id) { return document.getElementById(id); }

  const banner = $('escalation-banner');
  const bannerText = $('escalation-banner-text');
  let bannerTimer = null;

  function hideBanner() {
    if (!banner) return;
    banner.classList.remove('is-visible');
    banner.hidden = true;
    if (bannerTimer) {
      clearTimeout(bannerTimer);
      bannerTimer = null;
    }
  }

  function showBanner(message) {
    if (!banner || banner.dataset.enabled !== '1') return;
    if (bannerText) {
      bannerText.textContent = message;
    }
    banner.hidden = false;
    banner.classList.add('is-visible');
    const timeout = Number(banner.dataset.timeout || 12000);
    if (bannerTimer) {
      clearTimeout(bannerTimer);
    }
    bannerTimer = setTimeout(hideBanner, timeout);
  }

  function appendUserMessage(text) {
    const stream = $('chat-stream');
    if (!stream) return;
    const wrapper = document.createElement('div');
    wrapper.className = 'msg msg--user';
    const bubble = document.createElement('div');
    bubble.className = 'msg__bubble';
    bubble.textContent = text;
    wrapper.appendChild(bubble);
    stream.appendChild(wrapper);
    stream.scrollTop = stream.scrollHeight;
  }

  function appendAgentMessage(payload) {
    const stream = $('chat-stream');
    if (!stream) return;
    const wrapper = document.createElement('div');
    wrapper.className = 'msg msg--agent';
    const bubble = document.createElement('div');
    bubble.className = 'msg__bubble';

    const summary = document.createElement('p');
    summary.className = 'msg__summary';
    summary.textContent = payload.answer || 'No answer returned.';
    bubble.appendChild(summary);

    if (Array.isArray(payload.bullets) && payload.bullets.length) {
      const list = document.createElement('ul');
      list.className = 'msg__bullets';
      payload.bullets.forEach((item) => {
        const li = document.createElement('li');
        li.textContent = item;
        list.appendChild(li);
      });
      bubble.appendChild(list);
    }

    if (Array.isArray(payload.citations) && payload.citations.length) {
      const aside = document.createElement('div');
      aside.className = 'msg__sources';
      const title = document.createElement('p');
      title.className = 'msg__sources-title';
      title.textContent = 'Sources';
      aside.appendChild(title);
      const list = document.createElement('ul');
      payload.citations.forEach((citation) => {
        const li = document.createElement('li');
        const path = citation.source_path || 'Unknown source';
        const page = citation.page_number != null ? ` (p.${citation.page_number})` : '';
        const heading = citation.heading ? ` — ${citation.heading}` : '';
        li.textContent = `${path}${page}${heading}`;
        list.appendChild(li);
      });
      aside.appendChild(list);
      bubble.appendChild(aside);
    }

    wrapper.appendChild(bubble);
    stream.appendChild(wrapper);
    stream.scrollTop = stream.scrollHeight;
  }

  async function sendChat() {
    const input = $('chat-input');
    if (!input) return;
    const text = (input.value || '').trim();
    if (!text) return;
    appendUserMessage(text);
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
      appendAgentMessage(data);
      if (data.escalated && data.ae_id) {
        showBanner(`Escalated as ${data.ae_id}. We\'ll email you once it\'s resolved.`);
      } else {
        hideBanner();
      }
    } catch (err) {
      appendAgentMessage({ answer: 'Sorry, something went wrong. Please try again.' });
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

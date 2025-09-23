# TODO — Atticus (authoritative, reset)

This file is **the** source of truth for Codex. Assume nothing exists yet.

## 0) Repo layout
Create directories:
```
scripts/
api/ routes under api/routes/
atticus/notify/
web/templates/ web/static/css/ web/static/js/ web/static/img/
examples/ tests/
```

## 1) Environment & settings
- [ ] `scripts/generate_env.py` — create `.env` (idempotent; `--force` to overwrite) with keys:
```
OPENAI_MODEL=gpt-4.1
EMBED_MODEL=text-embedding-3-large
EMBEDDING_MODEL_VERSION=text-embedding-3-large@2025-01-15
GEN_MODEL=gpt-4.1
CONFIDENCE_THRESHOLD=0.70
CHUNK_TARGET_TOKENS=512
CHUNK_MIN_TOKENS=256
CHUNK_OVERLAP_TOKENS=100
MAX_CONTEXT_CHUNKS=10
LOG_LEVEL=INFO
TIMEZONE=UTC
EVAL_REGRESSION_THRESHOLD=3.0
CONTENT_DIR=./content
CONTACT_EMAIL=
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASS=
SMTP_FROM=
SMTP_TO=
```
- [ ] All configuration must be read from `.env` (no hard-coded values).

## 2) SMTP escalation
- [ ] `atticus/notify/mailer.py` exposing `send_escalation(subject, body, to=None)` using STARTTLS (587).
- [ ] Recipient: `to or SMTP_TO or CONTACT_EMAIL` (in that order). Redact secrets in logs.

## 3) API application
- [ ] **FastAPI** app in `api/main.py`:
  - Mount static: `/static` → `web/static`
  - Templates: Jinja2 in `web/templates`
  - `GET /` → render `main.html`
  - Include routers: `/ask` and `/contact` from `api/routes`
- [ ] **Routes**:
  - `api/routes/chat.py` → `POST /ask` → returns `{"answer": str, "sources": list, "confidence": float}`
  - `api/routes/contact.py` → `POST /contact` → accepts `{"reason": str, "transcript": list?}`, calls `send_escalation`, returns 202

## 4) Modern UI (fully functional)
**Use the cleaned templates below** (derived from the provided pages and simplified per requirements).
Icons/logos must be **placeholder files** under `web/static/img/` (the user will replace them).
Color scheme should come from `web/static/css/theme.css` — create the file and leave a header comment `/* placeholder: user-provided theme.css here */` (the user will supply the CSS).

### 4.1 Templates
Create `web/templates/side_menu.html` with **exactly** this content:
```html
<!-- web/templates/side_menu.html -->
<aside id="sidebar" class="sidebar">
  <header class="sidebar__header">
    <h2 class="sidebar__title">Menu</h2>
    <button id="sidebar-toggle" class="sidebar__toggle" aria-expanded="true" aria-controls="sidebar" title="Toggle menu">☰</button>
  </header>
  <nav class="sidebar__nav" role="navigation" aria-label="Primary">
    <ul class="nav-list">
      <li class="nav-item">
        <button id="contact-btn" class="nav-link" type="button">CONTACT</button>
      </li>
    </ul>
  </nav>
</aside>

```

Create `web/templates/main.html` with **exactly** this content:
```html
<!-- web/templates/main.html -->
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Atticus</title>
  <link rel="stylesheet" href="{{ url_for('static', path='css/theme.css') }}" />
  <script defer src="{{ url_for('static', path='js/app.js') }}"></script>
</head>
<body class="layout">
  {% include 'side_menu.html' %}
  <main id="chat" class="chat">
    <header class="chat__header">
      <h1 class="chat__title">Atticus</h1>
    </header>
    <section id="chat-stream" class="chat__stream" aria-live="polite" aria-atomic="false"></section>
    <footer class="chat__composer" role="form" aria-label="Chat composer">
      <input id="chat-input" class="chat__input" type="text" placeholder="Ask Atticus…" autocomplete="off" />
      <button id="chat-send" class="chat__send" type="button">Send</button>
    </footer>
  </main>
</body>
</html>

```

### 4.2 JavaScript
Create `web/static/js/app.js` with **exactly** this content:
```javascript
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

```

### 4.3 CSS
Create `web/static/css/theme.css` with this first line and then paste the user-provided stylesheet:
```css
/* placeholder: user-provided theme.css goes here; keep color scheme identical */
```

### 4.4 Layout acceptance criteria
- Left menu: single item **CONTACT**; collapsible toggle works.
- Right chat: `#chat-stream` scrolls (overflow-y:auto); input anchored at bottom.
- Chat send by button and Enter key; messages append as `.msg.user` and `.msg.agent`.
- CONTACT posts to `/contact` and shows a success alert (regardless of backend result).
- No top menu; navigation is **side menu only**.

## 5) Makefile & examples
Create `Makefile` with targets:
- `env` → `python scripts/generate_env.py`
- `smtp-test` → use mailer to send a test message
- `api` → run uvicorn `api.main:app`
- `ui` → serve static UI: `python -m http.server 8081 --directory web`
- `ingest`, `eval`, `openapi` → leave TODO echoes
- `test` → `pytest -q`
- `e2e` → chain `env ingest eval` (stub)

Create `examples/dev.http` with `/ask` and `/contact` sample requests.

## 6) Tests (skip gracefully if not yet implemented)
- `tests/test_ui_route.py` → `GET /` returns 200 and contains `chat-stream`
- `tests/test_contact_route.py` → posts to `/contact`, expect 200/202
- `tests/test_chat_route.py` → posts to `/ask` and asserts `answer` key
- `tests/test_mailer.py` → import smoke; SMTP test uses monkeypatched client

## 7) Documentation
- Update **README** with: Environment setup, Make targets, Frontend behavior, Testing & Evaluation, Doc map.
- Maintain: **AGENTS.md**, **ARCHITECTURE.md**, **OPERATIONS.md**, **FRONTEND.md**, **SECURITY.md**, **TROUBLESHOOTING.md**, **RELEASE.md**, **CONTRIBUTING.md**, **STYLEGUIDE.md**.

## 8) Acceptance demo
- After `python scripts/generate_env.py` and `make api`, visiting `/` shows the chat UI.
- Typing in the input and clicking **Send** produces a response (stub is acceptable until backend completes).
- Clicking **CONTACT** triggers a 202 from `/contact` (mailer may be mocked in dev).

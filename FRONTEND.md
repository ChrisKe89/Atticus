# Frontend specification

The Atticus UI is a single-page chat surface with a collapsible navigation rail.
Everything is rendered with server-side templates (no build step) and lives under
`web/`.

## File layout

- `web/templates/main.html` – overall page skeleton, chat stream, and composer
- `web/templates/side_menu.html` – navigation rail with CONTACT trigger and collapse toggle
- `web/static/css/theme.css` – design system (layout, colours, typography)
- `web/static/js/app.js` – fetch `/ask`, trigger `/contact`, and manage sidebar state

## Templates

`main.html` wraps the sidebar include and exposes a `<section id="chat-stream">`
for responses. The composer is a `<form>` with the textarea `#chat-input` and
button `#chat-send`. Both the sidebar toggle in the header and the button inside
`side_menu.html` carry the `data-sidebar-toggle` attribute so JavaScript can
collapse/expand the rail.

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Atticus Support Assistant</title>
    <link rel="stylesheet" href="{{ url_for('static', path='css/theme.css') }}" />
    <script defer src="{{ url_for('static', path='js/app.js') }}"></script>
  </head>
  <body>
    <div class="layout">
      {% include "side_menu.html" %}
      <div class="layout__content">
        <header class="topbar">
          <button class="topbar__menu" type="button" data-sidebar-toggle aria-controls="sidebar" aria-expanded="true">
            <span class="sr-only">Toggle navigation</span>
            <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
              <path d="M4 6.5A1.5 1.5 0 0 1 5.5 5h13a1.5 1.5 0 1 1 0 3h-13A1.5 1.5 0 0 1 4 6.5Zm0 5A1.5 1.5 0 0 1 5.5 10h13a1.5 1.5 0 1 1 0 3h-13A1.5 1.5 0 0 1 4 11.5Zm1.5 3.5a1.5 1.5 0 1 0 0 3h13a1.5 1.5 0 1 0 0-3h-13Z" fill="currentColor" />
            </svg>
          </button>
          <div class="topbar__titles">
            <h1 class="topbar__title">Atticus Assistant</h1>
            <p class="topbar__subtitle">Grounded answers for FUJIFILM Business Innovation AU</p>
          </div>
        </header>
        <main id="main" class="chat" aria-label="Support conversation">
          <section id="chat-stream" class="chat__stream" aria-live="polite" aria-atomic="false"></section>
          <form class="chat__composer" autocomplete="off">
            <label class="sr-only" for="chat-input">Ask a question</label>
            <textarea id="chat-input" class="chat__input" rows="1" placeholder="Ask Atticus about products, workflows, or escalation policy..."></textarea>
            <button id="chat-send" type="button" class="chat__send">Send</button>
          </form>
        </main>
      </div>
    </div>
  </body>
</html>
```

`side_menu.html` contains the brand block, CONTACT button, and footer reminder.
Both toggle buttons share the `data-sidebar-toggle` attribute for a consistent
experience on desktop and mobile.

```html
<aside id="sidebar" class="sidebar" aria-label="Primary navigation">
  <div class="sidebar__brand">
    <button type="button" class="sidebar__toggle" data-sidebar-toggle aria-controls="sidebar" aria-expanded="true">
      <span class="sr-only">Collapse navigation</span>
      <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
        <path d="M19 6.75a.75.75 0 0 1-.75.75H5.75a.75.75 0 0 1 0-1.5h12.5A.75.75 0 0 1 19 6.75Zm0 4.5a.75.75 0 0 1-.75.75H5.75a.75.75 0 0 1 0-1.5h12.5a.75.75 0 0 1 .75.75Zm0 4.5a.75.75 0 0 1-.75.75H5.75a.75.75 0 0 1 0-1.5h12.5a.75.75 0 0 1 .75.75Z" fill="currentColor" />
      </svg>
    </button>
    <div>
      <p class="sidebar__title">Atticus</p>
      <p class="sidebar__subtitle">Guided service answers</p>
    </div>
  </div>
  <nav class="sidebar__nav" role="navigation">
    <ul class="sidebar__list">
      <li>
        <button id="contact-btn" type="button" class="sidebar__link">
          <span class="sidebar__icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" focusable="false">
              <path d="M4.5 4.75A1.75 1.75 0 0 1 6.25 3h11.5A1.75 1.75 0 0 1 19.5 4.75v14.5a.75.75 0 0 1-1.17.623L12 15.38l-6.33 4.493A.75.75 0 0 1 4.5 19.25Z" fill="currentColor" />
            </svg>
          </span>
          <span class="sidebar__label">Escalate to CONTACT</span>
        </button>
      </li>
    </ul>
  </nav>
  <footer class="sidebar__footer">
    <p>Low confidence answers trigger an escalation email to the support team.</p>
  </footer>
</aside>
```

## Styling and behaviour

- `theme.css` defines the two-column layout, the collapsible rail (`layout--sidebar-collapsed`),
  chat bubbles, and responsive breakpoints.
- `app.js` attaches event listeners to `#chat-send`, `#chat-input`, `#contact-btn`,
  and `[data-sidebar-toggle]`. It posts JSON to `/ask`, calls `/contact`, and keeps
  the sidebar state in sync across buttons and viewport changes.

No external fonts or frameworks are required; all assets are first-party.

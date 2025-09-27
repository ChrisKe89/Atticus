// Tailwind dark-mode class strategy + theme boot (avoid FOUC)
(() => {
    if (localStorage.getItem('atticus.theme') === 'dark') {
        document.documentElement.classList.add('dark');
    }
})();

const qs = (s, el = document) => el.querySelector(s);
const qsa = (s, el = document) => Array.from(el.querySelectorAll(s));

const State = {
    users: [
        { email: 'chris@atticus.fyi', role: 'user' },
        { email: 'admin@atticus.fyi', role: 'admin' }
    ],
    session: JSON.parse(localStorage.getItem('atticus.session') || 'null')
};

function refreshAuthUI() {
    const loginBtn = qs('#loginBtn');
    const loginBtnText = qs('#loginBtnText');
    const adminLink = qs('#adminLink');

    if (State.session) {
        loginBtnText.textContent = State.session.email;
        loginBtn?.classList.remove('bg-indigo-500');
        loginBtn?.classList.add('bg-slate-700');
        if (adminLink) {
            adminLink.classList.toggle('hidden', State.session.role !== 'admin');
            adminLink.classList.toggle('flex', State.session.role === 'admin');
        }
    } else {
        loginBtnText.textContent = 'Login';
        loginBtn?.classList.remove('bg-slate-700');
        loginBtn?.classList.add('bg-indigo-500');
        if (adminLink) { adminLink.classList.add('hidden'); adminLink.classList.remove('flex'); }
    }
}

function openLogin(open = true) {
    const m = qs('#loginModal');
    if (!m) return;
    m.classList.toggle('hidden', !open);
    if (open) setTimeout(() => qs('#username')?.focus(), 10);
}

function handleLogin(e) {
    e.preventDefault();
    const email = qs('#username').value.trim().toLowerCase();
    const user = State.users.find(u => u.email === email);
    if (!user) { alert('Unknown user. Try chris@atticus.fyi or admin@atticus.fyi'); return; }
    State.session = { email: user.email, role: user.role };
    localStorage.setItem('atticus.session', JSON.stringify(State.session));
    openLogin(false);
    refreshAuthUI();
}

function logout() {
    State.session = null;
    localStorage.removeItem('atticus.session');
    refreshAuthUI();
}

function toggleDark() {
    const on = document.documentElement.classList.toggle('dark');
    localStorage.setItem('atticus.theme', on ? 'dark' : 'light');
}

function initNav() {
    const nav = qs('#leftNav');
    const collapseBtn = qs('#collapseBtn');
    const labels = qsa('.nav-label');
    const links = qsa('.nav-link');

    function setCollapsed(on) {
        nav.classList.toggle('nav-expanded', !on);
        nav.classList.toggle('nav-collapsed', on);
        labels.forEach(lbl => lbl.classList.toggle('hidden', on));
        links.forEach(a => {
            const text = a.querySelector('.nav-label')?.textContent?.trim();
            if (on) { a.classList.add('tooltip'); a.setAttribute('data-tip', text || ''); }
            else { a.classList.remove('tooltip'); a.removeAttribute('data-tip'); }
        });
        qs('#collapseArrow').textContent = on ? '⟶' : '⟵';
        localStorage.setItem('atticus.navCollapsed', on ? '1' : '0');
    }

    collapseBtn?.addEventListener('click', () => setCollapsed(nav.classList.contains('nav-expanded')));
    const saved = localStorage.getItem('atticus.navCollapsed') === '1';
    setCollapsed(saved);
}

function initLoginButton() {
    const btn = qs('#loginBtn');
    btn?.addEventListener('click', () => {
        if (State.session) {
            const go = confirm(`Signed in as ${State.session.email}\n\nOK: Go to Settings\nCancel: Sign out`);
            if (go) window.location.href = '/settings.html';
            else logout();
        } else {
            openLogin(true);
        }
    });
    qs('#closeLogin')?.addEventListener('click', () => openLogin(false));
    qs('#loginCancel')?.addEventListener('click', () => openLogin(false));
    qs('#loginForm')?.addEventListener('submit', handleLogin);
}

function initBottomControls() {
    qs('#darkToggle')?.addEventListener('click', toggleDark);
    qs('#settingsDark')?.addEventListener('click', toggleDark);
}

function initSettingsAccountBox() {
    const box = qs('#acctBox');
    if (!box) return;
    if (State.session) {
        box.innerHTML = `<div>Signed in as <b>${State.session.email}</b> (${State.session.role})</div>
      <button class="mt-2 px-3 py-2 rounded-md border border-slate-300 dark:border-slate-700" id="logoutBtn">Log out</button>`;
        qs('#logoutBtn')?.addEventListener('click', logout);
    } else {
        box.innerHTML = `<div>You are not signed in.</div>
      <button class="mt-2 px-3 py-2 rounded-md bg-indigo-600 text-white" id="openLoginFromSettings">Sign in</button>`;
        qs('#openLoginFromSettings')?.addEventListener('click', () => openLogin(true));
    }
}

function initAdminTabs() {
    const tabs = qsa('.admin-tab');
    if (!tabs.length) return;
    tabs.forEach(btn => btn.addEventListener('click', () => {
        const tab = btn.dataset.tab;
        qsa('.admin-tab').forEach(b => b.classList.remove('border-indigo-500', 'text-indigo-600'));
        btn.classList.add('border-indigo-500', 'text-indigo-600');
        qsa('.admin-panel').forEach(p => p.classList.toggle('hidden', p.dataset.panel !== tab));
    }));
    tabs[0]?.click();

    const tbody = qs('#adminUsers');
    if (tbody) {
        tbody.innerHTML = State.users.map(u =>
            `<tr class="border-t border-slate-200 dark:border-slate-700">
        <td class="py-2">${u.email}</td><td>${u.role}</td>
        <td>${State.session && State.session.email === u.email ? 'online' : '—'}</td>
      </tr>`).join('');
    }
}

function initChatIfPresent() {
    const feed = qs('#chat-feed');
    const input = qs('#chatInput');
    const send = qs('#sendBtn');
    if (!feed || !input || !send) return;

    const attachBtn = qs('#attachBtn');
    const attachName = qs('#attachName');
    const fileInput = qs('#fileInput');

    const escapeHtml = s => s.replace(/[&<>"']/g, m => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m]));
    function addMsg(role, text) {
        const wrap = document.createElement('div');
        const isUser = role === 'user';
        wrap.className = `flex ${isUser ? 'justify-end' : 'justify-start'}`;
        wrap.innerHTML = `
      <div class="max-w-[90%] rounded-2xl px-4 py-3 shadow border
        ${isUser ? 'bg-indigo-600 text-white border-indigo-500' : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700'}">
        <div class="whitespace-pre-wrap">${escapeHtml(text)}</div>
      </div>`;
        feed.appendChild(wrap);
        requestAnimationFrame(() => window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' }));
    }

    function doSend() {
        const text = input.value.trim();
        if (!text) return;
        addMsg('user', text);
        input.value = '';
        // Hook your real GPT call here; this is a stub:
        setTimeout(() => addMsg('assistant', `You said:\n${text}`), 100);
    }

    input.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 'Enter') { e.preventDefault(); doSend(); }
        // Enter alone, Shift+Enter -> newline (default)
    });
    send.addEventListener('click', doSend);

    attachBtn?.addEventListener('click', () => fileInput.click());
    fileInput?.addEventListener('change', () => {
        const f = fileInput.files?.[0];
        attachName.textContent = f ? `Attached: ${f.name}` : '';
    });
}

function protectAdminNotice() {
    const adminNotice = qs('#adminNotice');
    if (!adminNotice) return;
    if (State.session?.role !== 'admin') {
        adminNotice.classList.remove('hidden');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    refreshAuthUI();
    initLoginButton();
    initNav();
    initBottomControls();
    initSettingsAccountBox();
    initAdminTabs();
    initChatIfPresent();
    protectAdminNotice();
});

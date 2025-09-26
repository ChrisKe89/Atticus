const STORAGE_KEY = "atticus.chat.history.v1";
const API_BASE = (() => {
    const explicit = document.body?.dataset?.apiBase?.trim();
    if (explicit) {
        return explicit.replace(/\/$/, "");
    }
    if (typeof window.ATTICUS_API_BASE === "string" && window.ATTICUS_API_BASE.trim()) {
        return window.ATTICUS_API_BASE.trim().replace(/\/$/, "");
    }
    if (window.location.port === "8081") {
        return "http://localhost:8000";
    }
    return "";
})();

function resolveApi(path) {
    if (!API_BASE) {
        return path;
    }
    return `${API_BASE}${path.startsWith("/") ? path : `/${path}`}`;
}

function restoreDarkMode() {
    if (localStorage.getItem("atticus.darkMode") === "true") {
        document.body.classList.add("dark");
    }
}

function persistDarkMode(isDark) {
    localStorage.setItem("atticus.darkMode", String(isDark));
}

function saveChat(chatOutput) {
    if (chatOutput) {
        localStorage.setItem(STORAGE_KEY, chatOutput.innerHTML);
    }
}

function loadChat(chatOutput) {
    if (!chatOutput) {
        return;
    }
    const history = localStorage.getItem(STORAGE_KEY);
    if (history) {
        chatOutput.innerHTML = history;
    }
}

function formatTimestamp(date = new Date()) {
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

document.addEventListener("DOMContentLoaded", () => {
    const sidebar = document.getElementById("sidebar");
    const sidebarToggle = document.getElementById("sidebar-toggle");

    function setSidebarCollapsed(collapsed) {
        if (!sidebar) {
            return;
        }
        sidebar.classList.toggle("sidebar-collapsed", collapsed);
        sidebar.classList.toggle("w-64", !collapsed);
        sidebar.classList.toggle("w-20", collapsed);
        document.querySelectorAll(".menu-text").forEach((el) => {
            el.classList.toggle("hidden", collapsed);
        });
        document.querySelectorAll(".menu-item").forEach((el) => {
            el.classList.toggle("justify-center", collapsed);
            el.classList.toggle("justify-start", !collapsed);
        });
    }

    function toggleSidebar() {
        if (!sidebar) {
            return;
        }
        const collapsed = sidebar.classList.contains("sidebar-collapsed");
        setSidebarCollapsed(!collapsed);
    }

    if (sidebar) {
        sidebar.addEventListener("dblclick", () => {
            toggleSidebar();
        });
    }

    if (sidebarToggle) {
        sidebarToggle.addEventListener("click", () => {
            toggleSidebar();
        });
    }

    const darkToggle = document.getElementById("dark-toggle");
    if (darkToggle) {
        darkToggle.addEventListener("click", () => {
            document.body.classList.toggle("dark");
            persistDarkMode(document.body.classList.contains("dark"));
        });
    }
    restoreDarkMode();

    const chatForm = document.getElementById("chat-form");
    const chatInput = document.getElementById("chat-input");
    const chatOutput = document.getElementById("chat-output");
    const typingIndicator = document.getElementById("typing-indicator");
    const clearChatBtn = document.getElementById("clear-chat");
    const fileUpload = document.getElementById("file-upload");
    const fileNameDisplay = document.getElementById("file-name");

    function addMessage(text, sender = "user", options = {}) {
        if (!chatOutput) {
            return;
        }
        const wrapper = document.createElement("div");
        wrapper.className = sender === "system" ? "flex justify-center" : "flex flex-col gap-1";

        const msgContainer = document.createElement("div");
        msgContainer.className = sender === "user"
            ? "ml-auto max-w-3xl rounded-xl bg-blue-600 px-4 py-3 text-white shadow-lg animate-fadeIn"
            : sender === "system"
                ? "mx-auto rounded-full bg-gray-200 px-4 py-2 text-sm text-gray-700 dark:bg-gray-700 dark:text-gray-100 animate-fadeIn"
                : "mr-auto max-w-3xl rounded-xl bg-gray-200 px-4 py-3 text-sm text-gray-900 shadow-lg animate-fadeIn dark:bg-gray-800 dark:text-gray-100";

        if (options.allowHtml) {
            msgContainer.innerHTML = text;
        } else {
            const content = document.createElement("div");
            content.className = "whitespace-pre-line";
            content.textContent = text;
            msgContainer.appendChild(content);
        }

        if (sender !== "system") {
            const timeEl = document.createElement("span");
            timeEl.className = "block text-xs text-gray-300";
            const time = options.timestamp instanceof Date ? formatTimestamp(options.timestamp) : formatTimestamp();
            timeEl.textContent = time;
            if (sender === "user") {
                timeEl.classList.add("text-right");
            } else {
                timeEl.classList.add("text-gray-400", "dark:text-gray-500");
            }
            wrapper.appendChild(msgContainer);
            wrapper.appendChild(timeEl);
        } else {
            wrapper.appendChild(msgContainer);
        }

        if (Array.isArray(options.sources) && options.sources.length) {
            const listWrapper = document.createElement("div");
            listWrapper.className = "mt-3 rounded-lg border border-gray-200 bg-white/70 p-3 text-xs text-gray-700 dark:border-gray-700 dark:bg-gray-900/60 dark:text-gray-300";
            const listTitle = document.createElement("p");
            listTitle.className = "font-semibold uppercase tracking-wide text-[0.7rem] text-gray-500 dark:text-gray-400";
            listTitle.textContent = "Sources";
            listWrapper.appendChild(listTitle);

            const list = document.createElement("ul");
            list.className = "mt-2 space-y-1";
            options.sources.forEach((source) => {
                const item = document.createElement("li");
                item.textContent = source;
                list.appendChild(item);
            });
            listWrapper.appendChild(list);
            msgContainer.appendChild(listWrapper);
        }

        if (options.metaText) {
            const meta = document.createElement("p");
            meta.className = "mt-2 text-xs text-gray-400 dark:text-gray-500";
            meta.textContent = options.metaText;
            msgContainer.appendChild(meta);
        }

        chatOutput.appendChild(wrapper);
        chatOutput.scrollTo({ top: chatOutput.scrollHeight, behavior: "smooth" });
        saveChat(chatOutput);
    }

    if (chatOutput) {
        loadChat(chatOutput);
    }

    if (fileUpload && fileNameDisplay) {
        fileUpload.addEventListener("change", () => {
            fileNameDisplay.textContent = fileUpload.files?.[0]?.name ?? "";
        });
    }

    if (clearChatBtn && chatOutput) {
        clearChatBtn.addEventListener("click", () => {
            chatOutput.innerHTML = "";
            localStorage.removeItem(STORAGE_KEY);
            addMessage(`Chat cleared at ${formatTimestamp()}`, "system");
        });
    }

    let submitController = null;

    async function sendToApi(query) {
        if (submitController) {
            submitController.abort();
        }
        submitController = new AbortController();
        const payload = { query };
        const response = await fetch(resolveApi("/ask"), {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
            signal: submitController.signal,
        });

        if (!response.ok && response.status !== 206) {
            const detail = await response.text();
            throw new Error(detail || response.statusText);
        }

        const data = await response.json();
        return { status: response.status, data };
    }

    function renderBotReply({ answer, sources, confidence, escalated, ae_id, request_id }) {
        const parts = [answer || "(No answer returned)"];
        const metaChunks = [];
        if (typeof confidence === "number") {
            metaChunks.push(`Confidence: ${(confidence * 100).toFixed(0)}%`);
        }
        if (request_id) {
            metaChunks.push(`Request ID: ${request_id}`);
        }
        const metaText = metaChunks.length ? metaChunks.join(" · ") : undefined;
        addMessage(parts.join("\n\n"), "bot", {
            sources,
            metaText,
        });

        if (escalated) {
            const escalationMsg = ae_id
                ? `Confidence below threshold. Escalation created (ticket ${ae_id}).`
                : "Confidence below threshold. Escalation created.";
            addMessage(escalationMsg, "system");
        }
    }

    if (chatForm && chatInput && chatOutput && typingIndicator) {
        chatForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            const message = chatInput.value.trim();
            if (!message) {
                return;
            }

            addMessage(message, "user");
            chatInput.value = "";
            if (fileNameDisplay) {
                fileNameDisplay.textContent = "";
            }

            typingIndicator.classList.remove("hidden");

            try {
                const { status, data } = await sendToApi(message);
                renderBotReply({
                    answer: data.answer,
                    sources: data.sources,
                    confidence: data.confidence,
                    escalated: Boolean(data.escalated || status === 206),
                    ae_id: data.ae_id,
                    request_id: data.request_id,
                });
            } catch (error) {
                const detail = error instanceof Error ? error.message : String(error);
                addMessage(`Something went wrong: ${detail}`, "system");
            } finally {
                typingIndicator.classList.add("hidden");
                chatInput.focus();
            }
        });

        chatInput.addEventListener("keydown", (event) => {
            if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                chatForm.requestSubmit();
            }
        });
    }

    const contactForm = document.getElementById("contact-form");
    const contactSubject = document.getElementById("contact-subject");
    const contactBody = document.getElementById("contact-body");
    const contactStatus = document.getElementById("contact-status");
    const contactSend = document.getElementById("contact-send");

    if (contactForm && contactSubject && contactBody && contactStatus && contactSend) {
        contactForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            const subject = contactSubject.value.trim();
            const message = contactBody.value.trim();
            if (!subject || !message) {
                contactStatus.textContent = "Subject and message are required.";
                return;
            }

            contactStatus.textContent = "Sending escalation…";
            contactSend.disabled = true;

            try {
                const response = await fetch(resolveApi("/contact"), {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        reason: subject,
                        transcript: message,
                    }),
                });

                if (!response.ok) {
                    const detail = await response.text();
                    throw new Error(detail || response.statusText);
                }

                contactStatus.textContent = "Escalation sent successfully.";
                contactSubject.value = "";
                contactBody.value = "";
            } catch (error) {
                const detail = error instanceof Error ? error.message : String(error);
                contactStatus.textContent = `Unable to send escalation: ${detail}`;
            } finally {
                contactSend.disabled = false;
            }
        });
    }
});

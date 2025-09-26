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

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("contact-form");
    const subject = document.getElementById("contact-subject");
    const body = document.getElementById("contact-body");
    const sendButton = document.getElementById("contact-send");
    const status = document.getElementById("contact-status");

    if (!form || !subject || !body || !sendButton || !status) {
        return;
    }

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const reason = subject.value.trim();
        const messageBody = body.value.trim();

        if (!reason || !messageBody) {
            status.textContent = "Please provide both a subject and a message.";
            status.className = "text-sm text-amber-500";
            return;
        }

        sendButton.disabled = true;
        sendButton.textContent = "Sending…";
        status.textContent = "";

        try {
            const response = await fetch(resolveApi("/contact"), {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    reason,
                    transcript: messageBody,
                }),
            });

            if (!response.ok) {
                const detail = await response.text();
                throw new Error(detail || response.statusText);
            }

            status.textContent = "Message handed off for escalation. You'll receive a confirmation shortly.";
            status.className = "text-sm text-emerald-500";
            subject.value = "";
            body.value = "";
        } catch (error) {
            const detail = error instanceof Error ? error.message : String(error);
            status.textContent = `Unable to send message: ${detail}`;
            status.className = "text-sm text-rose-500";
        } finally {
            sendButton.disabled = false;
            sendButton.textContent = "Send message";
        }
    });
});

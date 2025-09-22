async function postJSON(url, data) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}`);
  }
  return res.json();
}

function renderCitations(list, citations) {
  list.innerHTML = "";
  if (!citations || !citations.length) return;
  for (const c of citations) {
    const li = document.createElement("li");
    const page = c.page_number != null ? ` (page ${c.page_number})` : "";
    const heading = c.heading ? ` – ${c.heading}` : "";
    li.textContent = `${c.source_path}${page}${heading} [score: ${c.score}]`;
    list.appendChild(li);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("ask-form");
  const questionEl = document.getElementById("question");
  const result = document.getElementById("result");
  const answer = document.getElementById("answer");
  const confidence = document.getElementById("confidence");
  const citations = document.getElementById("citations");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const question = questionEl.value.trim();
    if (!question) return;
    answer.textContent = "Thinking…";
    result.classList.remove("hidden");
    try {
      const data = await postJSON("/ask", { question });
      answer.textContent = data.answer || "No answer";
      confidence.textContent = `${Math.round((data.confidence || 0) * 100) / 100}`;
      renderCitations(citations, data.citations || []);
    } catch (err) {
      answer.textContent = `Error: ${err.message}`;
      confidence.textContent = "";
      citations.innerHTML = "";
    }
  });
});


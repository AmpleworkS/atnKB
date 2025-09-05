document.addEventListener("DOMContentLoaded", () => {
  const chatWindow = document.getElementById("chat-window");
  const chatInput = document.getElementById("chat-input");
  const sendBtn = document.getElementById("send-btn");

  // Markdown-like rendering
  function formatMessage(content) {
    return content
      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")  // **bold**
      .replace(/- (.*?)(?=\n|$)/g, "• $1")               // - → bullet
      .replace(/\n/g, "<br>");                           // line breaks
  }

  function addMessage(content, role) {
    const msg = document.createElement("div");
    msg.classList.add("message", role);

    // render HTML safely
    msg.innerHTML = formatMessage(content);

    chatWindow.appendChild(msg);
    chatWindow.scrollTop = chatWindow.scrollHeight;
  }

  function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;
    addMessage(text, "user");
    chatInput.value = "";

    // Call backend API
    fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    })
      .then(res => res.json())
      .then(data => addMessage(data.reply, "bot"))
      .catch(() => addMessage("❌ Error reaching server", "bot"));
  }

  sendBtn.addEventListener("click", sendMessage);
  chatInput.addEventListener("keypress", e => {
    if (e.key === "Enter") sendMessage();
  });

  // Initial greet
  addMessage("👋 Hi! Ask me anything about customer insights.", "bot");
});

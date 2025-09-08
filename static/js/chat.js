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

  function addMessage(content, role, isHTML = false) {
    const row = document.createElement("div");
    row.classList.add("message-row", role);

    const avatar = document.createElement("div");
    avatar.classList.add("avatar");
    avatar.textContent = role === "bot" ? "🤖" : "👤";

    const msg = document.createElement("div");
    msg.classList.add("message", role);
    msg.innerHTML = isHTML ? content : formatMessage(content);

    if (role === "bot") {
      row.appendChild(avatar);
      row.appendChild(msg);
    } else {
      row.appendChild(msg);
      row.appendChild(avatar);
    }

    chatWindow.appendChild(row);
    chatWindow.scrollTop = chatWindow.scrollHeight;
    return msg; // return element (for loader replacement)
  }

  function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;
    addMessage(text, "user");
    chatInput.value = "";

    // Add loader bubble
    const loader = addMessage(
      `<span class="typing-dots"><span></span><span></span><span></span></span>`,
      "bot",
      true
    );

    // Call backend API
    fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    })
      .then(res => res.json())
      .then(data => {
        loader.parentElement.remove(); // remove loader row
        addMessage(data.reply, "bot");
      })
      .catch(() => {
        loader.parentElement.remove();
        addMessage("❌ Error reaching server", "bot");
      });
  }

  sendBtn.addEventListener("click", sendMessage);
  chatInput.addEventListener("keypress", e => {
    if (e.key === "Enter") sendMessage();
  });

  // Initial greet
  addMessage("👋 Hi! Ask me anything about customer insights.", "bot");
});
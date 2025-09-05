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
    const msg = document.createElement("div");
    msg.classList.add("message", role);
    msg.innerHTML = isHTML ? content : formatMessage(content);
    chatWindow.appendChild(msg);
    chatWindow.scrollTop = chatWindow.scrollHeight;
    return msg; // return element (useful for loader removal)
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
        loader.remove(); // remove loader
        addMessage(data.reply, "bot");
      })
      .catch(() => {
        loader.remove();
        addMessage(":x: Error reaching server", "bot");
      });
  }
  sendBtn.addEventListener("click", sendMessage);
  chatInput.addEventListener("keypress", e => {
    if (e.key === "Enter") sendMessage();
  });
  // Initial greet
  addMessage("Hi! Ask me anything about customer insights.", "bot");
});
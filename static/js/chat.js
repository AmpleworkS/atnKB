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

  // Add chat message
  function addMessage(content, role) {
    const wrapper = document.createElement("div");
    wrapper.classList.add("message-wrapper", role);

    const msg = document.createElement("div");
    msg.classList.add("message", role);
    msg.innerHTML = formatMessage(content);

    const avatar = document.createElement("div");
    avatar.classList.add("avatar");
    avatar.textContent = role === "bot" ? "🤖" : "👤";

    wrapper.appendChild(role === "bot" ? avatar : msg);
    wrapper.appendChild(role === "bot" ? msg : avatar);

    chatWindow.appendChild(wrapper);
    chatWindow.scrollTop = chatWindow.scrollHeight;
    return wrapper;
  }

  // Add typing indicator
  function showTyping() {
    const wrapper = document.createElement("div");
    wrapper.classList.add("message-wrapper", "bot", "typing");

    const msg = document.createElement("div");
    msg.classList.add("message", "bot");

    const dots = document.createElement("div");
    dots.classList.add("typing-dots");
    dots.innerHTML = "<span></span><span></span><span></span>";

    const avatar = document.createElement("div");
    avatar.classList.add("avatar");
    avatar.textContent = "🤖";

    msg.appendChild(dots);
    wrapper.appendChild(avatar);
    wrapper.appendChild(msg);

    chatWindow.appendChild(wrapper);
    chatWindow.scrollTop = chatWindow.scrollHeight;
    return wrapper;
  }

  function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;

    // User message
    addMessage(text, "user");
    chatInput.value = "";

    // Typing indicator
    const typingBubble = showTyping();

    // Send to backend
    fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    })
      .then(res => res.json())
      .then(data => {
        typingBubble.remove(); // remove typing dots
        addMessage(data.reply, "bot");
      })
      .catch(() => {
        typingBubble.remove(); // remove typing dots
        addMessage("❌ Error reaching server", "bot");
      });
  }

  sendBtn.addEventListener("click", sendMessage);
  chatInput.addEventListener("keypress", e => {
    if (e.key === "Enter") sendMessage();
  });

  // ✅ Only one initial greeting
  addMessage("Hi! Ask me anything about customer insights.", "bot");
});
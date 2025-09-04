import re
import html
import streamlit as st

def contains_html(s: str) -> bool:
    """Detect if text contains raw HTML tags."""
    return bool(re.search(r"<\/?\w+[^>]*>", s))

def markdown_like_to_html(text: str) -> str:
    """Convert markdown-like text to lightweight HTML."""
    # Code blocks
    text = re.sub(r"```(.*?)```", r"<pre class='code-block'>\1</pre>", text, flags=re.DOTALL)
    # Inline code
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    # Bold
    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
    # Italic
    text = re.sub(r"\*(.*?)\*", r"<i>\1</i>", text)
    return text

def set_custom_css():
    """Inject CSS for chatbot bubbles and layout."""
    st.markdown(
        """
        <style>
        .chat-wrapper {
            display: flex;
            flex-direction: column;
            gap: 10px;
            padding: 15px;
            max-width: 900px;
            margin: auto;
        }
        .message-row {
            display: flex;
            align-items: flex-end;
            gap: 8px;
        }
        .message-row.user { justify-content: flex-end; }
        .message-row.assistant { justify-content: flex-start; }
        .bubble {
            padding: 10px 14px;
            border-radius: 14px;
            max-width: 75%;
            font-size: 15px;
            line-height: 1.4;
            white-space: pre-wrap;
            word-wrap: break-word;
            box-shadow: 0px 1px 3px rgba(0,0,0,0.1);
        }
        .bubble.user {
            background-color: #007bff;
            color: white;
        }
        .bubble.assistant {
            background-color: #f1f0f0;
            color: black;
        }
        .icon {
            font-size: 18px;
        }
        .icon.user { order: 2; }
        .icon.assistant { order: 1; }
        .code-block {
            background: #272822;
            color: #f8f8f2;
            padding: 10px;
            border-radius: 6px;
            overflow-x: auto;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

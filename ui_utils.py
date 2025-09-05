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
        /* Main background gradient */
        .stApp {
            background: White !important;
        }
        
        /* Chat container */
        .chat-wrapper {
            display: flex;
            flex-direction: column;
            gap: 8px;
            padding: 16px;
            max-width: 900px;
            margin: auto;
            font-family: "Segoe UI", Roboto, sans-serif;
        }

        .message-row {
            display: flex;
            align-items: flex-start;
            gap: 8px;
            margin: 4px 0;
        }

        /* Assistant messages on left */
        .message-row.assistant { 
            justify-content: flex-start; 
        }

        /* User messages on right */
        .message-row.user {
            justify-content: flex-end;
        }

        .bubble {
            padding: 12px 16px;
            border-radius: 18px;
            max-width: 70%;
            font-size: 14px;
            line-height: 1.4;
            white-space: pre-wrap;
            word-wrap: break-word;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        /* User bubble - blue gradient right side */
        .bubble.user {
            background: linear-gradient(135deg, #4a90e2 0%, #357abd 100%);
            color: white;
            border-bottom-right-radius: 6px;
        }

        /* Assistant bubble - white with subtle shadow */
        .bubble.assistant {
            background: white;
            color: #2c3e50;
            border: 1px solid #e3e8f0;
            border-bottom-left-radius: 6px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        }

        /* Typography improvements */
        .bubble.assistant * {
            margin: 0;
            padding: 0;
            line-height: 1.4;
        }

        .bubble.assistant p {
            margin: 6px 0 !important;
            padding: 0 !important;
            color: #2c3e50;
        }

        .bubble.assistant ul, 
        .bubble.assistant ol {
            margin: 6px 0 !important;
            padding-left: 20px !important;
        }

        .bubble.assistant li {
            margin: 4px 0 !important;
            padding: 0 !important;
            color: #2c3e50;
        }

        .bubble.assistant strong {
            color: #2c3e50;
            font-weight: 600;
        }

        .bubble.assistant h1,
        .bubble.assistant h2,
        .bubble.assistant h3 {
            margin: 8px 0 4px 0 !important;
            font-weight: 600;
            color: #2c3e50;
        }

        .bubble.assistant h1 { 
            font-size: 18px; 
            border-bottom: 2px solid #e3e8f0;
            padding-bottom: 4px;
        }
        .bubble.assistant h2 { font-size: 16px; }
        .bubble.assistant h3 { font-size: 15px; }

        
        /* Style the input area */
        .stTextInput > div > div > input {
            background: white;
            border: 2px solid #e3e8f0;
            border-radius: 25px;
            padding: 12px 20px;
            font-size: 14px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        }
        /* Code blocks */
        .code-block {
            margin: 8px 0 !important;
            padding: 10px 14px !important;
            background: #f8fafc;
            border: 1px solid #e3e8f0;
            border-radius: 8px;
            font-family: "Consolas", monospace;
            font-size: 13px;
            color: #2c3e50;
        }

        .stTextInput > div > div > input:focus {
            border-color: #4a90e2;
            box-shadow: 0 0 0 2px rgba(74, 144, 226, 0.2);
        }

        /* Remove Streamlit default padding */
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 4rem;
        }

        /* Header styling */
        h1, h2, h3 {
            color: #2c3e50 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

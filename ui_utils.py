import re

def contains_html(s: str) -> bool:
    return bool(re.search(r"<\/?\w+[^>]*>", s or ""))

def markdown_like_to_html(text: str) -> str:
    text = text or ""
    text = re.sub(r"```(.*?)```", r"<pre class='code-block'>\1</pre>", text, flags=re.DOTALL)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*(.*?)\*", r"<i>\1</i>", text)
    return text

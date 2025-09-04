# import os
# import json
# import html
# import streamlit as st
# from dotenv import load_dotenv

# from postgres_utils import run_postgres_query, is_count_query, parse_count_query
# from pinecone_utils import search_with_filters
# from llm_utils import llm
# from ui_utils import contains_html, markdown_like_to_html, set_custom_css

# # ========================
# # 1. ENV + CLIENT SETUP
# # ========================
# load_dotenv()
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

# if not OPENAI_API_KEY or not PINECONE_API_KEY:
#     st.error("❌ Please set OPENAI_API_KEY and PINECONE_API_KEY in .env")
#     st.stop()

# # ========================
# # 2. STREAMLIT UI SETUP
# # ========================
# st.set_page_config(page_title="Customer Insights • Chatbot", layout="wide")
# st.title("📊 Customer Insights Chatbot")

# # ✅ Memory stays
# if "messages" not in st.session_state:
#     st.session_state.messages = [
#         {"role": "assistant", "content": "Hi — ask me anything about customer insights."}
#     ]

# # CSS + header
# set_custom_css()

# # --- render chat history ---
# st.markdown("<div class='chat-wrapper'>", unsafe_allow_html=True)
# for msg in st.session_state.messages:
#     role = msg.get("role", "assistant")
#     content = msg.get("content", "")

#     if role == "user":
#         safe_html = "<div>" + html.escape(content).replace("\n", "<br/>") + "</div>"
#         bubble_class, icon_html, row_class = "bubble user", "<div class='icon user'>👤</div>", "message-row user"
#     else:
#         safe_html = (f"<pre class='code-block'>{html.escape(content)}</pre>"
#                      if contains_html(content)
#                      else markdown_like_to_html(content))
#         bubble_class, icon_html, row_class = "bubble assistant", "<div class='icon assistant'>👾</div>", "message-row assistant"

#     if role == "assistant":
#         message_html = f"""
#         <div class="{row_class}">
#             {icon_html}
#             <div class="{bubble_class}">{safe_html}</div>
#         </div>"""
#     else:
#         message_html = f"""
#         <div class="{row_class}">
#             <div class="{bubble_class}">{safe_html}</div>
#             {icon_html}
#         </div>"""
#     st.markdown(message_html, unsafe_allow_html=True)
# st.markdown("</div>", unsafe_allow_html=True)

# # ========================
# # 3. USER INPUT HANDLING
# # ========================
# if query := st.chat_input("Ask me about customer insights..."):
#     st.session_state.messages.append({"role": "user", "content": query})

#     with st.spinner("🔎 Thinking..."):
#         if is_count_query(query):
#             sql, params = parse_count_query(query)
#             if sql:
#                 pg_result = run_postgres_query(sql, params)
#                 if isinstance(pg_result, str) and pg_result.startswith("❌"):
#                     answer = pg_result
#                 elif isinstance(pg_result, list) and pg_result:
#                     count_val = pg_result[0][0]
#                     answer = f"📊 Based on PostgreSQL data, the result is: **{count_val} customers**."
#                 else:
#                     answer = "I ran the database query but found no matching records."
#             else:
#                 answer = ("I couldn't identify a precise counting pattern in your question. "
#                           "Try: 'How many customers are interested in Diamond' or 'How many customers in USA'.")
#         else:
#             results, applied_filters, reasoning, fallback_used = search_with_filters(query)
#             context = "\n\n".join([doc.page_content for doc in results]) if results else "No results found."

#             # ✅ Memory is included in LLM prompt
#             summary_prompt = f"""
#             You are a friendly customer insights chatbot.
#             The user asked: "{query}"

#             Filters applied: {json.dumps(applied_filters)}
#             Reasoning: {reasoning}
#             Fallback used: {fallback_used}
#             Retrieved Data:
#             {context}

#             Answer clearly, explain patterns, use bullets and emojis.
#             Suggest 1–2 follow-ups at the end.
#             """
#             conversation = [{"role": "system", "content": summary_prompt}] + st.session_state.messages
#             answer = llm.invoke(conversation).content

#     st.session_state.messages.append({"role": "assistant", "content": answer})
#     st.rerun()



# #######################################################################################################################################################
import os
import json
import html
import streamlit as st
from dotenv import load_dotenv

from postgres_utils import run_postgres_query, is_count_query, parse_count_query
from pinecone_utils import search_with_filters
from llm_utils import llm
from ui_utils import contains_html, markdown_like_to_html, set_custom_css

# ========================
# 1. ENV + CLIENT SETUP
# ========================
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

if not OPENAI_API_KEY or not PINECONE_API_KEY:
    st.error("❌ Please set OPENAI_API_KEY and PINECONE_API_KEY in .env")
    st.stop()

st.set_page_config(page_title="Customer Insights • Chatbot", layout="wide")
st.title("📊 Customer Insights Chatbot")

# ========================
# 2. MEMORY INIT
# ========================
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi — ask me anything about customer insights."}
    ]

# ========================
# 3. RENDER CHAT HISTORY
# ========================
set_custom_css()
st.markdown("<div class='chat-wrapper'>", unsafe_allow_html=True)
for msg in st.session_state.messages:
    role = msg.get("role", "assistant")
    content = msg.get("content", "")

    if role == "user":
        safe_html = "<div>" + html.escape(content).replace("\n", "<br/>") + "</div>"
        bubble_class, icon_html, row_class = "bubble user", "<div class='icon user'>👤</div>", "message-row user"
    else:
        safe_html = (f"<pre class='code-block'>{html.escape(content)}</pre>"
                     if contains_html(content)
                     else markdown_like_to_html(content))
        bubble_class, icon_html, row_class = "bubble assistant", "<div class='icon assistant'>🤖</div>", "message-row assistant"

    if role == "assistant":
        message_html = f"""
        <div class="{row_class}">
            {icon_html}
            <div class="{bubble_class}">{safe_html}</div>
        </div>"""
    else:
        message_html = f"""
        <div class="{row_class}">
            <div class="{bubble_class}">{safe_html}</div>
            {icon_html}
        </div>"""
    st.markdown(message_html, unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# ========================
# 4. USER INPUT HANDLING
# ========================
if query := st.chat_input("Ask me about customer insights..."):
    st.session_state.messages.append({"role": "user", "content": query})

    with st.spinner("🔎 Thinking..."):
        if is_count_query(query):
            sql, params = parse_count_query(query)
            if sql:
                pg_result = run_postgres_query(sql, params)
                if isinstance(pg_result, str) and pg_result.startswith("❌"):
                    answer = pg_result
                elif isinstance(pg_result, list) and pg_result:
                    count_val = pg_result[0][0]
                    answer = f"📊 Based on PostgreSQL data, the result is: **{count_val} customers**."
                else:
                    answer = "I ran the database query but found no matching records."
            else:
                answer = ("I couldn't identify a precise counting pattern in your question. "
                          "Try: 'How many customers are interested in Diamond' or 'How many customers in USA'.")
        else:
            results, applied_filters, reasoning, fallback_used = search_with_filters(query)
            context = "\n\n".join([doc.page_content for doc in results]) if results else "No results found."

            # summary_prompt = f"""
            # You are a friendly customer insights chatbot.
            # The user asked: "{query}"

            # Filters applied: {json.dumps(applied_filters)}
            # Reasoning: {reasoning}
            # Fallback used: {fallback_used}
            # Retrieved Data:
            # {context}

            # Answer clearly, explain patterns, use bullets and emojis.
            # Suggest 1–2 follow-ups at the end.
            # """
            summary_prompt = f"""
            You are a friendly but sharp customer insights chatbot for ATN Unlimited team based on the Knowledge Base that helps the team gain more insights about customers and understand them to improve internal strategy.
            The user asked: "{query}"

            Filters applied: {json.dumps(applied_filters)}
            Reasoning for filters: {reasoning}
            Fallback used: {fallback_used}
            Retrieved Customer Data:
            {context}

             Your role:
            - Directly answer the user’s question first
            - Provide insights, patterns, comparisons, reasioning
            - Use retrieved data to back your answer and use explaining tone
            - If data is unclear, acknowledge and give best interpretation
            - Use bullets/short paragraphs for readability
            - Sparingly add emojis for tone
            - End with  with suggesting a few questions user might ask next like-"💡 Would you also like me to tell you: " suggesting 1–2 follow-ups
            """

            conversation = [{"role": "system", "content": summary_prompt}] + st.session_state.messages
            answer = llm.invoke(conversation).content

    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.rerun()

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

if "last_customer" not in st.session_state:
    st.session_state.last_customer = None  # memory for entity tracking

# ========================
# EXTRA HELPERS (FIXED COLUMN NAME)
# ========================
def get_package_counts():
    sql = """
        SELECT 
            CASE 
                WHEN "Package of Customer Interest" IS NULL OR "Package of Customer Interest" = '' 
                    THEN 'None'
                ELSE "Package of Customer Interest"
            END AS package_name,
            COUNT(*)::int
        FROM atn_table 
        GROUP BY package_name
        ORDER BY package_name;
    """
    result = run_postgres_query(sql)
    if isinstance(result, str):
        return result  # error string
    return [(row[0], row[1]) for row in result]


def get_all_packages():
    sql = """
        SELECT DISTINCT 
            CASE 
                WHEN "Package of Customer Interest" IS NULL OR "Package of Customer Interest" = '' 
                    THEN 'None'
                ELSE "Package of Customer Interest"
            END AS package_name
        FROM atn_table
        ORDER BY package_name;
    """
    result = run_postgres_query(sql)
    if isinstance(result, str):
        return result  # error string
    return [(row[0],) for row in result]

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
        bubble_class, icon_html, row_class = "bubble user", "<div class='icon user'></div>", "message-row user"
    else:
        safe_html = (f"<pre class='code-block'>{html.escape(content)}</pre>"
                     if contains_html(content)
                     else markdown_like_to_html(content))
        bubble_class, icon_html, row_class = "bubble assistant", "<div class='icon assistant'></div>", "message-row assistant"

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
        lower_q = query.lower().strip()

        # --- Pronoun Resolution ---
        pronouns = ["his", "her", "their"]
        if any(p in lower_q for p in pronouns) and st.session_state.last_customer:
            query = query.replace("his", st.session_state.last_customer)
            query = query.replace("her", st.session_state.last_customer)
            query = query.replace("their", st.session_state.last_customer)

        # --- Handle meta-memory queries ---
        if "first question" in lower_q:
            first_q = next((m["content"] for m in st.session_state.messages if m["role"] == "user"), None)
            answer = f"Your first question was: **{first_q}** 💡" if first_q else "I couldn't find your first question."
        
        elif "last question" in lower_q or "previous question" in lower_q:
            user_msgs = [m["content"] for m in st.session_state.messages if m["role"] == "user"]
            if len(user_msgs) >= 2:
                answer = f"Your last question was: **{user_msgs[-2]}** 📝"
            else:
                answer = "You haven't asked any previous questions yet."

        elif "all my questions" in lower_q or "summarize" in lower_q:
            user_msgs = [m["content"] for m in st.session_state.messages if m["role"] == "user"]
            if user_msgs:
                formatted = "\n".join([f"{i+1}. {q}" for i, q in enumerate(user_msgs)])
                answer = f"Here are all the questions you've asked so far:\n\n{formatted}"
            else:
                answer = "You haven't asked any questions yet."
        
        # --- Handle Postgres count queries ---
        elif is_count_query(query):
            sql, params = parse_count_query(query)
            if sql:
                pg_result = run_postgres_query(sql, params)
                if isinstance(pg_result, str) and pg_result.startswith("❌"):
                    answer = pg_result
                elif isinstance(pg_result, list) and pg_result:
                    count_val = pg_result[0][0]
                    answer = f"There are {count_val} records available 📊."
                else:
                    answer = "No matching records found."
            else:
                answer = ("I couldn't identify a counting pattern in your question. "
                          "Try asking: 'How many customers are interested in Diamond?'")

        # --- Division of customers by package (improved detection) ---
        elif any(kw in lower_q for kw in ["division", "divide", "distribution", "breakdown", "split", "group"]) and "package" in lower_q:
            pg_result = get_package_counts()
            if isinstance(pg_result, str):
                answer = pg_result
            elif pg_result:
                answer = "📊 Here's the division of customers by package:\n\n"
                for pkg, count in pg_result:
                    answer += f"- **{pkg}**: {count} customers\n"
            else:
                answer = "No package data found."

        # --- List all packages ---
        elif "list" in lower_q and "package" in lower_q:
            pg_result = get_all_packages()
            if isinstance(pg_result, str):
                answer = pg_result
            elif pg_result:
                answer = "📦 Here's a list of all the packages mentioned:\n\n"
                for row in pg_result:
                    answer += f"- {row[0]}\n"
            else:
                answer = "No packages found."

        # --- Handle Pinecone search queries (ID/email/insights) ---
        else:
            results, applied_filters, reasoning, fallback_used = search_with_filters(query)
            context = "\n\n".join([doc.page_content for doc in results]) if results else "No results found."

            # update last_customer if a name was detected
            if results:
                first_doc = results[0].page_content
                for token in first_doc.split():
                    if token.istitle():  
                        st.session_state.last_customer = token
                        break

            summary_prompt = f"""
                You are a friendly but sharp customer insights chatbot for ATN Unlimited team based on the Knowledge Base that helps the team gain more insights about customers and understand them to improve internal strategy.
                The user asked: "{query}"  

                Retrieved Data:
                {context}

                👉 Guidelines:
                - If the query asks for email/ID, return it directly if present.
                - If the query asks for insights, summarize trends/preferences.
                - Do NOT guess or invent data.
                - Use relevant emojis .
                - End with a friendly follow-up suggestion.
            """
            conversation = [{"role": "system", "content": summary_prompt}]
            for msg in st.session_state.messages[-10:]:
                conversation.append({"role": msg["role"], "content": msg["content"]})
            conversation.append({"role": "user", "content": query})

            answer = llm.invoke(conversation).content

    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.rerun()

# app.py
import os
import json
import streamlit as st
from dotenv import load_dotenv

from postgres_utils2 import answer_user_question
from orchestrator_utils import orchestrate_query
from pinecone_utils import search_with_filters
from llm_utils import llm

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
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

from postgres_utils import answer_user_question

# ========================
# 4. USER INPUT HANDLING
# ========================
if query := st.chat_input("Ask me about customer insights..."):
    # Show user message in chat
    st.session_state.messages.append({"role": "user", "content": query})
    st.chat_message("user").markdown(query)


    with st.spinner("🔎 Thinking..."):
        # 🔹 Try Postgres/NL → SQL pipeline first
        meta_triggers = ["suggest", "what can i ask", "example questions", "help me explore", "ideas to ask"]
        if any(t in query.lower() for t in meta_triggers):
            answer = """
            Here are a few useful questions you can ask me:
            - How many customers have the Diamond package?
            - How many customers are Entrepreneurs vs Employees?
            - How many customers joined after 2023?
            - How many customers with investable assets > 50,000?
            """
        else:
            answer = answer_user_question(query)

        # 🔹 If Postgres didn't give a useful answer → fallback to Pinecone
        if not answer or answer.strip() in ["No results.", "📋 Retrieved 0 rows (showing 0)."]:
            results, applied_filters, reasoning, fallback_used = search_with_filters(query)
            context = "\n\n".join([doc.page_content for doc in results]) if results else "No results found."

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
            - Provide insights, patterns, comparisons, reasoning
            - Use retrieved data to back your answer and use explaining tone
            - If data is unclear, acknowledge and give best interpretation
            - Use bullets/short paragraphs for readability
            - Sparingly add emojis for tone
            - End with suggesting a few follow-ups
            """

            conversation = [{"role": "system", "content": summary_prompt}] + st.session_state.messages
            answer = llm.invoke(conversation).content

    # Show assistant reply in chat
    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.chat_message("assistant").markdown(answer)





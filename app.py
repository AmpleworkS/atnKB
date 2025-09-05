import os
import html
from flask import Flask, render_template, request, session, jsonify
from dotenv import load_dotenv

from postgres_utils import run_postgres_query, is_count_query, parse_count_query
from pinecone_utils import search_with_filters
from llm_utils import llm
from ui_utils import contains_html, markdown_like_to_html

# ========================
# 1. ENV + APP SETUP
# ========================
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

if not OPENAI_API_KEY or not PINECONE_API_KEY:
    raise RuntimeError("Please set OPENAI_API_KEY and PINECONE_API_KEY in .env")

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecret")

# small helper for session init
def ensure_session():
    if "messages" not in session:
        session["messages"] = [
            {"role": "assistant", "content": "Hi — ask me anything about customer insights."}
        ]
    if "last_customer" not in session:
        session["last_customer"] = None

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
        return result
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
        return result
    return [(row[0],) for row in result]

# ========================
# 2. ROUTES
# ========================
@app.route("/", methods=["GET"])
def index():
    ensure_session()
    return render_template("chat.html", messages=session["messages"])

@app.route("/chat", methods=["POST"])
def chat():
    ensure_session()
    data = request.get_json(silent=True) or request.form
    user_query = (data.get("message") or "").strip()
    if not user_query:
        return jsonify({"ok": False, "error": "Empty message"}), 400

    msgs = session["messages"]
    msgs.append({"role": "user", "content": user_query})

    lower_q = user_query.lower().strip()
    answer = ""

    # --- Pronoun Resolution ---
    pronouns = ["his", "her", "their"]
    resolved_query = user_query
    if any(p in lower_q for p in pronouns) and session.get("last_customer"):
        for p in pronouns:
            resolved_query = resolved_query.replace(p, session["last_customer"])

    # --- Meta-memory queries ---
    if "first question" in lower_q:
        first_q = next((m["content"] for m in msgs if m["role"] == "user"), None)
        answer = f"Your first question was: **{first_q}** 💡" if first_q else "I couldn't find your first question."

    elif "last question" in lower_q or "previous question" in lower_q:
        user_msgs = [m["content"] for m in msgs if m["role"] == "user"]
        answer = f"Your last question was: **{user_msgs[-2]}** 📝" if len(user_msgs) >= 2 else "You haven't asked any previous questions yet."

    elif "all my questions" in lower_q or "summarize" in lower_q:
        user_msgs = [m["content"] for m in msgs if m["role"] == "user"]
        if user_msgs:
            formatted = "\n".join([f"{i+1}. {q}" for i, q in enumerate(user_msgs)])
            answer = f"Here are all the questions you've asked so far:\n\n{formatted}"
        else:
            answer = "You haven't asked any questions yet."

    # --- Postgres count queries ---
    elif is_count_query(resolved_query):
        sql, params = parse_count_query(resolved_query)
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

    # --- Division of customers by package ---
    elif any(kw in lower_q for kw in ["division", "divide", "distribution", "breakdown", "split", "group"]) and "package" in lower_q:
        pg_result = get_package_counts()
        if isinstance(pg_result, str):
            answer = pg_result
        elif pg_result:
            lines = [f"- **{pkg}**: {count} customers" for pkg, count in pg_result]
            answer = "📊 Here's the division of customers by package:\n\n" + "\n".join(lines)
        else:
            answer = "No package data found."

    # --- List all packages ---
    elif "list" in lower_q and "package" in lower_q:
        pg_result = get_all_packages()
        if isinstance(pg_result, str):
            answer = pg_result
        elif pg_result:
            lines = [f"- {row[0]}" for row in pg_result]
            answer = "📦 Here's a list of all the packages mentioned:\n\n" + "\n".join(lines)
        else:
            answer = "No packages found."

    # --- Pinecone search ---
    else:
        results, applied_filters, reasoning, fallback_used = search_with_filters(resolved_query)
        context = "\n\n".join([doc.page_content for doc in results]) if results else "No results found."

        if results:
            first_doc = results[0].page_content
            for token in first_doc.split():
                if token.istitle():
                    session["last_customer"] = token
                    break

        summary_prompt = f"""
You are a concise **Customer Insights Chatbot**.

The user asked: "{resolved_query}"

Retrieved Data:
{context}

👉 Guidelines:
- If the query asks for email/ID, return it directly if present.
- If the query asks for insights, summarize trends/preferences.
- Do NOT guess or invent data.
- Use relevant emojis (📊✨💡🎯).
- End with a friendly follow-up suggestion.
"""
        conversation = [{"role": "system", "content": summary_prompt}]
        for m in msgs[-10:]:
            conversation.append({"role": m["role"], "content": m["content"]})
        conversation.append({"role": "user", "content": resolved_query})

        answer = llm.invoke(conversation).content

    msgs.append({"role": "assistant", "content": answer})
    session["messages"] = msgs

    return jsonify({"ok": True, "reply": answer})

# ------------- run -------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)

import os
import psycopg2
import json
from flask import Flask, render_template, request, session, jsonify
from dotenv import load_dotenv

from postgres_utils import run_postgres_query
from pinecone_utils import search_with_filters
from llm_utils import llm
from ui_utils import markdown_like_to_html

# ========================
# 1. ENV + APP SETUP
# ========================
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

# PostgreSQL connection details from .env
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT")
}

# Test connection at startup
try:
    conn = psycopg2.connect(**DB_CONFIG)
    conn.close()
except Exception as e:
    raise RuntimeError(f"Database connection failed: {e}")

if not OPENAI_API_KEY or not PINECONE_API_KEY:
    raise RuntimeError("Please set OPENAI_API_KEY and PINECONE_API_KEY in .env")

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecret")


def ensure_session():
    """Make sure session has default state."""
    if "messages" not in session:
        session["messages"] = []
    if "last_customer" not in session:
        session["last_customer"] = None


# ========================
# 2. TOOL DEFINITIONS
# ========================
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "postgres_tool",
            "description": """
Run SQL queries on the atn_table.

Schema:
Table: atn_table
Important Columns:

    "Customer ID" TEXT,
    "Sales_Rep Name" TEXT,
    "Customer Name" TEXT,
    "Email" TEXT,
    "Qualifying Lead" BOOLEAN,
    "Lead qualification Reason" TEXT,
    "Ad Lead" BOOLEAN,
    "Ad Lead Qualification Reason" TEXT,
    "Package of Customer Interest" TEXT,
    "Tags from GHL" TEXT,
    "Phone Number" TEXT,
    "country" TEXT,
    "Pain points Objections Outcomes" TEXT,
    "Investment Level" TEXT,
    "Investable Assets" TEXT,
    "Engagement Level" TEXT,
    "Risk Profile" TEXT,
    "Persona Type" TEXT,
    "Postal Code" VARCHAR(200),
    "Package Purchased" TEXT

Rules for SQL:
- Always wrap column names in double quotes (" ") because they contain spaces.
- Table name is always atn_table.
- Example queries:
    - Get customer ID for Louis Davis → SELECT "Customer ID" FROM atn_table WHERE "Customer Name" ILIKE '%Louis Davis%';
    - Count customers in Diamond Package → SELECT COUNT(*) FROM atn_table WHERE "Package of Customer Interest" ILIKE '%Diamond%';
    - List all customer names → SELECT "Customer Name" FROM atn_table LIMIT 456;
""",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "A valid SQL query using atn_table."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "pinecone_tool",
            "description": "Search semantic knowledge base for customer insights, preferences, or unstructured data like pain points.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search string or natural language query."
                    }
                },
                "required": ["query"]
            }
        }
    }
]


# ========================
# 3. ROUTES
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

    # ========== STEP 1: Call LLM with tools ==========
    conversation = [
        {"role": "system", "content": """
You are a friendly but sharp customer insights chatbot for ATN Unlimited team based on the Knowledge Base that helps the team gain more insights about customers and understand them to improve internal strategy.
You have access to two tools:
- postgres_tool → for structured data like customer_id, number of customers, filtering by attributes.
- pinecone_tool → for semantic insights like customer pain points, goals, or free-text knowledge base queries.

Rules:
1. Always try postgres_tool when customer_id, counts, or structured fields are requested.
2. Use pinecone_tool when the query is about pain points, unstructured notes, or insights.
3. Always return clear, natural answers using tool results. Never say "I cannot access". If a query fails, retry with simpler SQL.
4. Keep answers concise and human-friendly.
5. At the end of your response, suggest 1-2 relevant follow-up question the team might ask next.
"""}
    ] + msgs[-10:]

    response = llm.invoke(conversation, tools=TOOLS)

    answer = ""
    tool_results = {}

    # ========== STEP 2: Handle tool calls ==========
    if getattr(response, "tool_calls", None):
        followup_conversation = conversation + [response]

        for call in response.tool_calls:
            fn_name = call.function.name
            args = json.loads(call.function.arguments)

            if fn_name == "postgres_tool":
                result = run_postgres_query(args["query"])
                tool_results[call.id] = result

            elif fn_name == "pinecone_tool":
                results, _, _, _ = search_with_filters(args["query"])
                result_text = "\n".join(
                    [doc.page_content for doc in results]
                ) if results else "No results found."
                tool_results[call.id] = result_text

        # Add tool outputs back into conversation
        for tool_id, result in tool_results.items():
            followup_conversation.append({
                "role": "tool",
                "tool_call_id": tool_id,
                "content": result
            })

        # Final LLM response
        final_response = llm.invoke(followup_conversation)
        answer = final_response.content

    else:
        answer = response.content

    # Save assistant reply
    msgs.append({"role": "assistant", "content": answer})
    session["messages"] = msgs

    return jsonify({"ok": True, "reply": answer})


# ------------- run -------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)

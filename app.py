import os
import psycopg2
import json
from flask import Flask, render_template, request, session, jsonify
from dotenv import load_dotenv

# === Imports for charting ===
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import uuid

from postgres_utils import run_postgres_query
from pinecone_utils import search_with_filters
from llm_utils import llm

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


def generate_chart(data_json, chart_type, x_col, y_col, title):
    """
    Generates a chart from data and saves it as a PNG image.
    Returns the web-accessible path to the chart.
    """
    try:
        charts_dir = os.path.join('static', 'charts')
        os.makedirs(charts_dir, exist_ok=True)

        data = json.loads(data_json)
        if not data:
            return None
        
        if not isinstance(data, list) or not all(isinstance(d, dict) for d in data):
            print("Error: data must be a list of dictionaries.")
            return None

        df = pd.DataFrame(data)

        if x_col not in df.columns or y_col not in df.columns:
            print(f"Error: Columns '{x_col}' or '{y_col}' not in data.")
            return None

        plt.figure(figsize=(8, 5))

        if chart_type == 'bar':
            plt.bar(df[x_col], df[y_col], color='skyblue')
        elif chart_type == 'line':
            plt.plot(df[x_col], df[y_col], marker='o', linestyle='-')
        elif chart_type == 'pie':
            if len(df) > 10:
                df = df.nlargest(10, y_col)
            plt.pie(df[y_col], labels=df[x_col], autopct='%1.1f%%', startangle=90)
        else:
            return None

        plt.title(title, fontsize=16)
        plt.xlabel(str(x_col).replace('_', ' ').title())
        plt.ylabel(str(y_col).replace('_', ' ').title())
        plt.grid(True, which='both', linestyle='--', linewidth=0.5)
        plt.gca().spines['top'].set_visible(False)
        plt.gca().spines['right'].set_visible(False)
        plt.tight_layout()

        filename = f"{uuid.uuid4()}.png"
        filepath = os.path.join(charts_dir, filename)
        plt.savefig(filepath)
        plt.close()

        return f"/static/charts/{filename}"

    except Exception as e:
        print(f"Error generating chart: {e}")
        return None

# ========================
# 2. TOOL DEFINITIONS
# ========================
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "postgres_tool",
            "description": """
Run SQL queries on the kb_table.

Schema:
Table: kb_table
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
- Table name is always kb_table.
- Example queries:
    - Get customer ID for Louis Davis → SELECT "Customer ID" FROM kb_table WHERE "Customer Name" ILIKE '%Louis Davis%';
    - Count customers in Diamond Package → SELECT COUNT(*) FROM kb_table WHERE "Package of Customer Interest" ILIKE '%Diamond%';
    - List all customer names → SELECT "Customer Name" FROM kb_table LIMIT 456;
""",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "A valid SQL query using kb_table."
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
    },
    {
        "type": "function",
        "function": {
            "name": "chart_generator_tool",
            "description": "Generates a chart image from structured data when a user asks for a visual representation, graph, or chart. Use this tool AFTER getting the data from postgres_tool.",
            "parameters": {
                "type": "object",
                "properties": {
                    "data": {
                        "type": "string",
                        "description": "A JSON string representing the data to plot. Must be a list of objects. Example: '[{\"country\": \"USA\", \"count\": 150}, {\"country\": \"Canada\", \"count\": 75}]'"
                    },
                    "chart_type": {
                        "type": "string",
                        "description": "The type of chart to generate. Supported types: 'bar', 'line', 'pie'.",
                        "enum": ["bar", "line", "pie"]
                    },
                    "x_col": {
                        "type": "string",
                        "description": "The column name from the data to be used for the x-axis or labels."
                    },
                    "y_col": {
                        "type": "string",
                        "description": "The column name from the data to be used for the y-axis or values."
                    },
                    "title": {
                        "type": "string",
                        "description": "The title for the chart."
                    }
                },
                "required": ["data", "chart_type", "x_col", "y_col", "title"]
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

    # === UPDATED PROMPT: Instruct LLM not to generate a chart unless asked ===
    conversation = [
        {"role": "system", "content": """
You are a friendly but sharp customer insights chatbot for kb Unlimited team.
You have access to three tools:
- postgres_tool: For querying structured data (counts, names, filters).
- pinecone_tool: For semantic search on unstructured data (pain points, notes).
- chart_generator_tool: For creating visual charts from data.

**General Rules:**
- Keep answers concise.
- If a query fails, explain why and suggest a simpler alternative.
- After answering, always suggest 1-2 relevant follow-up questions.
- When you answered the Query using a tool, if there is need for generate a graph, chart so please give suggestion to user to ask for a chart or graph.
- **IMPORTANT**: Only use the `chart_generator_tool` when the user explicitly asks for a "chart," "graph," "visualization," or similar visual representation. If they only ask for data, provide the data in a list or summary format.
- Do not mention creating a chart or providing a link to a file in your conversational response. The chart should appear directly in the UI.
"""}
    ] + msgs[-10:]

    answer = ""
    chart_url = None
    max_tool_calls = 5
    
    while True:
        response = llm.invoke(conversation, tools=TOOLS)
        
        if not getattr(response, "tool_calls", None):
            answer = response.content
            break
        
        conversation.append(response)
        
        tool_results = {}
        for call in response.tool_calls:
            fn_name = call.function.name
            args = json.loads(call.function.arguments)

            if fn_name == "postgres_tool":
                result = run_postgres_query(args["query"])
                
                if isinstance(result, str):
                    tool_results[call.id] = result
                elif isinstance(result, dict) and 'cursor' in result and result['cursor'] and result['cursor'].description:
                    columns = [desc[0] for desc in result['cursor'].description]
                    data_dicts = [dict(zip(columns, row)) for row in result['data']]
                    tool_results[call.id] = json.dumps(data_dicts)
                else:
                    tool_results[call.id] = "No data or a valid cursor found."
                
            elif fn_name == "pinecone_tool":
                results, _, _, _ = search_with_filters(args["query"])
                result_text = "\n".join(
                    [doc.page_content for doc in results]
                ) if results else "No results found."
                tool_results[call.id] = result_text
            
            elif fn_name == "chart_generator_tool":
                chart_path = generate_chart(
                    data_json=args["data"],
                    chart_type=args["chart_type"],
                    x_col=args["x_col"],
                    y_col=args["y_col"],
                    title=args["title"]
                )
                if chart_path:
                    chart_url = chart_path
                    # Do NOT put the chart path in the content string
                    tool_results[call.id] = "Chart successfully generated."
                else:
                    tool_results[call.id] = "Failed to generate the chart."

        for tool_id, result in tool_results.items():
            conversation.append({
                "role": "tool",
                "tool_call_id": tool_id,
                "content": result
            })
        
        max_tool_calls -= 1
        if max_tool_calls == 0:
            answer = "I'm sorry, I couldn't generate a final response after multiple attempts. The tool chain may be broken."
            break
            
    if not answer:
        answer = "I'm sorry, I couldn't generate a final response. Please try rephrasing your request."
        
    msgs.append({"role": "assistant", "content": answer})
    session["messages"] = msgs

    # === UPDATED RESPONSE: Only return the reply and chart URL ===
    return jsonify({"ok": True, "reply": answer, "chart_url": chart_url})

# ------------- run -------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
# orchestrator_utils.py
import json
from postgres_utils import answer_user_question
from pinecone_utils import search_with_filters
from llm_utils import llm

# --------------------------
# Intent classification
# --------------------------
def classify_intent(query: str) -> str:
    q = query.lower()

    # META queries (help / suggestions)
    if any(t in q for t in ["suggest", "example", "what can i ask", "help me explore", "ideas"]):
        return "meta"

    # SQL queries (numbers, filters, aggregates)
    if any(t in q for t in ["how many", "count", "average", "sum", "group by", "top", "filter", "date after", "date before"]):
        return "sql"

    # Pinecone queries (descriptive info)
    if any(t in q for t in ["who is", "what is", "tell me about", "explain", "details of"]):
        return "pinecone"

    # Hybrid (mix of numbers + explanations)
    if "and" in q and any(t in q for t in ["count", "how many"]) and any(t in q for t in ["explain", "details", "pattern"]):
        return "hybrid"

    return "pinecone"  # default fallback


# --------------------------
# Meta / Suggestion handler
# --------------------------
def generate_meta_suggestions() -> dict:
    answer = """Here are some questions you can ask me:

🔹 Customer Numbers
- How many customers joined in 2024?
- How many customers have > 100,000 investable assets?

🔹 Segmentation
- How many customers are Entrepreneurs vs Employees?
- How many Growth-minded vs Conservative investors?

🔹 Packages
- How many customers are in Gold vs Diamond package?
- Who upgraded their package in the last 6 months?

🔹 Insights
- What is the most common objection in sales calls?
- Which videos are recommended for Entrepreneurs?
"""
    return {"answer": answer, "related": []}


# --------------------------
# SQL (Postgres) handler
# --------------------------
def run_sql_pipeline(query: str) -> dict:
    ans = answer_user_question(query)
    related = [
        "Break it down by package type?",
        "How many are qualifying leads?",
        "Compare this year vs last year?",
    ]
    return {"answer": ans, "related": related}


# --------------------------
# Pinecone handler
# --------------------------
def run_pinecone_pipeline(query: str) -> dict:
    results, applied_filters, reasoning, fallback_used = search_with_filters(query)
    context = "\n\n".join([doc.page_content for doc in results]) if results else "No results found."

    summary_prompt = f"""
    You are a friendly customer insights chatbot for ATN Unlimited.
    The user asked: "{query}"

    Filters applied: {json.dumps(applied_filters)}
    Reasoning: {reasoning}
    Fallback used: {fallback_used}
    Retrieved Knowledge:
    {context}

    Please:
    - Directly answer the user’s query
    - Add insights or patterns if possible
    - Be clear and structured
    - End with 2-3 suggested follow-up questions
    """

    conversation = [{"role": "system", "content": summary_prompt}]
    answer = llm.invoke(conversation).content

    return {"answer": answer, "related": []}


# --------------------------
# Hybrid handler
# --------------------------
def run_hybrid_pipeline(query: str) -> dict:
    sql_ans = answer_user_question(query)
    pinecone = run_pinecone_pipeline(query)
    combined = f"{sql_ans}\n\n📖 Context:\n{pinecone['answer']}"
    return {"answer": combined, "related": ["Want me to break it down further?", "Should I compare with last month?"]}


# --------------------------
# Main Orchestrator
# --------------------------
def orchestrate_query(query: str) -> dict:
    intent = classify_intent(query)

    if intent == "meta":
        return generate_meta_suggestions()
    elif intent == "sql":
        return run_sql_pipeline(query)
    elif intent == "pinecone":
        return run_pinecone_pipeline(query)
    elif intent == "hybrid":
        return run_hybrid_pipeline(query)
    else:
        return {"answer": "❌ Sorry, I couldn’t understand that.", "related": []}

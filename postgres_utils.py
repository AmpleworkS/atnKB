import psycopg2
import re
import os
import json
from dotenv import load_dotenv
from openai import OpenAI

# ------------------------
# 0. Setup
# ------------------------
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT")
}

# ------------------------
# 1. Run query helper
# ------------------------
def run_postgres_query(query: str, params: tuple = ()):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(query, params)
        result = cur.fetchall()
        cur.close()
        conn.close()
        return result
    except Exception as e:
        return f"❌ PostgreSQL Error: {str(e)}"

# ------------------------
# 2. Get all column names
# ------------------------
def get_table_columns(table_name: str = "atn_table"):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = %s;
        """, (table_name,))
        cols = [row[0] for row in cur.fetchall()]
        cur.close()
        conn.close()
        return cols
    except Exception:
        return []

# ------------------------
# 2b. Get column types
# ------------------------
def get_column_types(table_name: str = "atn_table"):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = %s;
        """, (table_name,))
        types = {row[0]: row[1] for row in cur.fetchall()}
        cur.close()
        conn.close()
        return types
    except Exception:
        return {}

# ------------------------
# 3. Detect count queries
# ------------------------
def is_count_query(query: str):
    keywords = ["how many", "count", "total", "number of"]
    return any(k in query.lower() for k in keywords)

# ------------------------
# 4. Fuzzy column mapping via LLM
# ------------------------
def map_query_to_columns(user_query: str, columns: list[str]):
    prompt = f"""
    You are a SQL assistant. 
    Map the user query to filters on these SQL columns: {columns}.
    
    User query: "{user_query}"
    
    Return ONLY a valid JSON list of objects like this:
    [
      {{"column": "<column_name>", "value": "<value>"}}
    ]
    Multiple filters are allowed (e.g. package AND sales rep).
    """

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You map NL queries to SQL column filters."},
            {"role": "user", "content": prompt},
        ],
        temperature=0
    )

    try:
        text = resp.choices[0].message.content.strip()
        return json.loads(text)
    except Exception:
        return []

# ------------------------
# 5. Build SQL from user query
# ------------------------
def parse_count_query(query: str, table_name: str = "atn_table"):
    q_lower = query.lower()
    columns = get_table_columns(table_name)
    col_types = get_column_types(table_name)

    # Base query
    sql = f'SELECT COUNT(*) FROM "{table_name}"'
    conditions = []
    params = []

    mappings = []

    # Regex attempt
    for col in columns:
        col_lower = col.lower()
        if col_lower in q_lower:
            pattern = col_lower + r"(?:\s+as|\s+is|\s*=)?\s+([a-z0-9 &\-\+]+)"
            m = re.search(pattern, q_lower)
            if m:
                val = m.group(1).strip()
                mappings.append({"column": col, "value": val})

    # Always include LLM mappings too
    llm_mappings = map_query_to_columns(query, columns)
    mappings.extend(llm_mappings)

    # Deduplicate
    seen = set()
    unique_mappings = []
    for m in mappings:
        col = m.get("column")
        val = m.get("value")
        if (col, val) not in seen and col and val:
            unique_mappings.append(m)
            seen.add((col, val))

    # Apply conditions
    for m in unique_mappings:
        col = m["column"]
        val = m["value"]
        if col_types.get(col) == "boolean":
            if val.lower() in ["true", "yes", "1"]:
                conditions.append(f'"{col}" = TRUE')
            elif val.lower() in ["false", "no", "0"]:
                conditions.append(f'"{col}" = FALSE')
        else:
            cond = f'LOWER("{col}") LIKE %s'
            conditions.append(cond)
            params.append(f'%{val.lower()}%')

    # Final SQL
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)

    return sql + ";", tuple(params)
# postgres_utils.py
import os
import re
import json
import psycopg2
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Tuple, Optional
from dotenv import load_dotenv
from openai import OpenAI

# =========================
# 0) Setup
# =========================
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT")
}

DEFAULT_TABLE = "atn_table"
DEFAULT_LIST_LIMIT = 100

# =========================
# 1) DB helpers
# =========================
def run_postgres_query(query: str, params: Tuple = ()):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(query, params)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows
    except Exception as e:
        return f"❌ PostgreSQL Error: {str(e)}"

def get_table_columns(table_name: str = DEFAULT_TABLE) -> List[str]:
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = %s;
        """, (table_name,))
        cols = [r[0] for r in cur.fetchall()]
        cur.close()
        conn.close()
        return cols
    except Exception:
        return []

def get_column_types(table_name: str = DEFAULT_TABLE) -> Dict[str,str]:
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = %s;
        """, (table_name,))
        d = {r[0]: r[1] for r in cur.fetchall()}
        cur.close()
        conn.close()
        return d
    except Exception:
        return {}

# =========================
# 2) NL → SQL (via LLM)
# =========================
LLM_JSON_SPEC = """
Return ONLY valid compact JSON (no prose) with this schema:
{
  "intent": "count | group_by | top_n | list",
  "filters": [
    {"column": "<col>", "op": "contains|=|>|<|>=|<=|between|on|after|before|between_dates|is_true|is_false", "value": "<v1>", "value2": "<v2 if needed>"}
  ],
  "group_by": ["<col1>"],
  "top_n": 5,
  "order_by": {"column": "<col>", "direction": "desc"},
  "select": ["<cols>"]
}
"""

def map_query_to_spec(user_query: str, columns: List[str]) -> Dict[str, Any]:
    prompt = f"""
You are mapping a natural language analytics question to a SQL-ready JSON plan.
Columns available: {columns}
User query: "{user_query}"
{LLM_JSON_SPEC}
"""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role":"system","content":"You output JSON-only plans for SQL over a known schema."},
            {"role":"user","content":prompt}
        ],
        temperature=0
    )
    try:
        text = resp.choices[0].message.content.strip()
        plan = json.loads(text)
        plan.setdefault("filters", [])
        plan.setdefault("group_by", [])
        plan.setdefault("select", [])
        return plan
    except Exception:
        return {"intent":"count","filters":[],"group_by":[],"top_n":0,"order_by":{},"select":[]}

# =========================
# 3) Build SQL
# =========================
def build_sql_from_nl(user_query: str, table_name: str = DEFAULT_TABLE) -> Dict[str,Any]:
    columns = get_table_columns(table_name)
    plan = map_query_to_spec(user_query, columns)

    intent = plan.get("intent","count")
    filters = plan.get("filters",[])
    group_by = plan.get("group_by",[])
    top_n = int(plan.get("top_n") or 0)
    order_by = plan.get("order_by") or {}
    select_cols = plan.get("select") or []

    where_sql: List[str] = []
    params: List[Any] = []

    for f in filters:
        col, op, v1, v2 = f.get("column"), f.get("op"), f.get("value"), f.get("value2")
        if not col or col not in columns:
            continue
        if op in {"contains","="}:
            where_sql.append(f'LOWER("{col}") LIKE %s')
            params.append(f'%{str(v1).lower()}%')
        elif op in {">","<",">=","<=","="}:
            where_sql.append(f'"{col}" {op} %s')
            params.append(v1)
        elif op == "between":
            where_sql.append(f'"{col}" BETWEEN %s AND %s')
            params.extend([v1, v2])
        elif op in {"on","after","before","between_dates"}:
            if op == "on":
                where_sql.append(f'DATE("{col}") = %s'); params.append(v1)
            elif op == "after":
                where_sql.append(f'DATE("{col}") >= %s'); params.append(v1)
            elif op == "before":
                where_sql.append(f'DATE("{col}") <= %s'); params.append(v1)
            elif op == "between_dates":
                where_sql.append(f'DATE("{col}") BETWEEN %s AND %s')
                params.extend([v1, v2])
        elif op == "is_true":
            where_sql.append(f'"{col}" = TRUE')
        elif op == "is_false":
            where_sql.append(f'"{col}" = FALSE')

    where_clause = " WHERE " + " AND ".join(where_sql) if where_sql else ""

    sql = ""
    if intent == "count":
        sql = f'SELECT COUNT(*) FROM "{table_name}"{where_clause};'
    elif intent == "group_by" and group_by:
        gcols = ", ".join([f'"{g}"' for g in group_by if g in columns])
        sql = f'SELECT {gcols}, COUNT(*) FROM "{table_name}"{where_clause} GROUP BY {gcols} ORDER BY COUNT(*) DESC;'
    elif intent == "top_n" and order_by.get("column") in columns:
        n = top_n if top_n > 0 else 5
        sql = f'SELECT * FROM "{table_name}"{where_clause} ORDER BY "{order_by["column"]}" {order_by.get("direction","DESC")} LIMIT {n};'
    else: # list
        cols_part = "*" if not select_cols else ", ".join([f'"{c}"' for c in select_cols if c in columns])
        sql = f'SELECT {cols_part} FROM "{table_name}"{where_clause} LIMIT {DEFAULT_LIST_LIMIT};'
        intent = "list"

    return {"intent": intent, "sql": sql, "params": tuple(params)}

# =========================
# 4) Format user answer
# =========================
def answer_user_question(user_query: str, table_name: str = DEFAULT_TABLE) -> str:
    plan = build_sql_from_nl(user_query, table_name)
    rows = run_postgres_query(plan["sql"], plan["params"])
    if isinstance(rows, str): return rows

    if plan["intent"] == "count":
        return f"📊 Count result: **{rows[0][0]}** records."
    elif plan["intent"] == "group_by":
        if not rows: return "No results."
        return "📊 Breakdown:\n" + "\n".join([f"- {r[0]}: {r[1]}" for r in rows])
    elif plan["intent"] == "top_n":
        return "📈 Top results:\n" + "\n".join([str(r) for r in rows])
    else:
        return f"📋 Retrieved {len(rows)} rows (showing {min(len(rows),10)})."

import os
import json
from dotenv import load_dotenv
from pinecone import Pinecone
from langchain_pinecone import Pinecone as LangchainPinecone
from langchain_openai import OpenAIEmbeddings
from llm_utils import llm_filter_chain

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX")

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-large",
    openai_api_key=OPENAI_API_KEY
)

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)

vectorstore = LangchainPinecone(
    index,
    embeddings,
    text_key="text"
)

def decide_filters(query: str):
    try:
        response = llm_filter_chain.invoke({"query": query}).content
        parsed = json.loads(response)
    except Exception:
        parsed = {"filters": {}, "reasoning": "LLM returned non-JSON"}
    return parsed.get("filters", {}), parsed.get("reasoning", "")

def search_with_filters(query: str):
    filters, reasoning = decide_filters(query)
    results = vectorstore.similarity_search(query, filter=filters, k=20)
    fallback_used = False
    if not results:
        fallback_used = True
        results = vectorstore.similarity_search(query, k=20)
    return results, filters, reasoning, fallback_used

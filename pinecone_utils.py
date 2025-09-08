import os
from dotenv import load_dotenv
from pinecone import Pinecone
from langchain_pinecone import Pinecone as LangchainPinecone
from langchain_openai import OpenAIEmbeddings

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

def search_with_filters(query: str):
    """
    Just run similarity search on Pinecone.
    We dropped the old llm_filter_chain logic.
    """
    try:
        results = vectorstore.similarity_search(query, k=20)
        return results, {}, "", False
    except Exception as e:
        return [], {}, f"❌ Error in Pinecone search: {str(e)}", True
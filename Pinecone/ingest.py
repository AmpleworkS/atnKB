import os
import json
from pinecone import Pinecone, ServerlessSpec
from openai import OpenAI
from dotenv import load_dotenv

# =========================
# 1. ENV SETUP
# =========================
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX")

client = OpenAI(api_key=OPENAI_API_KEY)

# =========================
# 2. CONNECT TO PINECONE
# =========================
pc = Pinecone(api_key=PINECONE_API_KEY)

# Create index if not exists
if INDEX_NAME not in [i["name"] for i in pc.list_indexes()]:
    pc.create_index(
        name=INDEX_NAME,
        dimension=3072,  # OpenAI embedding dimension
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")  # adjust if needed
    )

index = pc.Index(INDEX_NAME)

# =========================
# 3. HELPER: Build text to embed
# =========================
def build_text(record: dict) -> str:
    """Convert JSON fields into one concatenated string for embeddings."""
    fields = [
        record.get("Customer Name", ""),
        record.get("Email", ""),
        record.get("Phone Number", ""),
        record.get("country", ""),
        record.get("status", ""),
        record.get("Ad Lead Qualification Reason", ""),
        record.get("Decision and liquidity info", ""),
        record.get("Pain points Objections Outcomes", ""),
        record.get("Next Steps", ""),
        record.get("Supporting Justification or Description", ""),
    ]
    return " | ".join([f for f in fields if f])

# =========================
# 4. LOAD DATA
# =========================
with open("data (4).json", "r", encoding="utf-8") as f:
    data = json.load(f)

# =========================
# 5. UPSERT TO PINECONE
# =========================
batch_size = 50
to_upsert = []

for i, record in enumerate(data):
    record_id = record.get("Customer ID", f"cust-{i}")
    text_to_embed = build_text(record)

    # Generate embedding
    response = client.embeddings.create(
        model="text-embedding-3-large",
        input=text_to_embed
    )
    embedding = response.data[0].embedding

    # correct metadata types
    metadata = {}
    for k, v in record.items():
        if isinstance(v, (str, int, float, bool)):
            metadata[k] = v

    to_upsert.append({"id": record_id, "values": embedding, "metadata": metadata})

    # Batch upload
    if len(to_upsert) >= batch_size:
        index.upsert(vectors=to_upsert)
        print(f"Upserted {len(to_upsert)} records")
        to_upsert = []

# Final flush
if to_upsert:
    index.upsert(vectors=to_upsert)
    print(f"Upserted final {len(to_upsert)} records")

print("✅ Data successfully stored in Pinecone!")
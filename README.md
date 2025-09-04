# 📊 Customer Insights Chatbot

An interactive chatbot built with **Streamlit**, **LangChain**, **Pinecone**, and **OpenAI**.  
It provides customer insights using Retrieval-Augmented Generation (RAG) while maintaining **conversation memory**.

---

## 🚀 Features
- Chatbot with memory (conversation history is preserved in session state).
- Uses **Pinecone** for vector search and filtering with metadata.
- Powered by **OpenAI GPT-4o** for natural language answers.
- Custom **Markdown-like renderer** for formatted responses (bold, italics, code blocks, lists).
- Interactive **Streamlit UI** with styled chat bubbles and headers.
- Filter decision chain: extracts metadata filters using an LLM before searching Pinecone.

---

## 🛠️ Setup

### 1. Clone the repo
```bash

git clone https://github.com/your-username/customer-insights-chatbot.git
cd customer-insights-chatbot


2. Create a virtual environment

bash

python -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows


3. Install dependencies
bash

pip install -r requirements.txt


4. Add environment variables

Create a .env file in the project root with:

OPENAI_API_KEY=your_openai_api_key
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX=your_pinecone_index_name


▶️ Run the App

bash

streamlit run app.py
Open your browser at http://localhost:8501.


📂 Tech Stack
Python
Streamlit → Chat UI
LangChain → Orchestration
OpenAI GPT-4o → LLM
Pinecone → Vector DB for embeddings


🧩 How It Works
User asks a question.
The chatbot extracts potential filters from the query.
Searches Pinecone for relevant customer data (with fallback).
Uses GPT-4o to generate an insightful response with reasoning.
Chat history is stored for contextual conversation.


📌 Example Queries
"Show me insights for customers interested in Diamond package."
"How can XYZ sales refine his pitch to make the customers lean towards Diamond Package?"
"Summarize the common pain points of recent leads."


⚠️ Notes
This is a knowledge-assistant for customer insights, not financial advice.
Ensure your Pinecone index is properly populated with structured customer data.
# 🧠 Customer Insights Chatbot  

An **AI-powered Customer Insights Chatbot** that combines **structured SQL queries (PostgreSQL)** with **semantic search (Pinecone)** and **LLMs (OpenAI)** to provide customer insights in natural language.  

This chatbot enables businesses to query customer data, analyze pain points, and retrieve actionable insights seamlessly through a simple **Flask-based web interface**.  

---

## 🚀 Features  
🔹 **Hybrid Querying:** Structured (Postgres) + Semantic (Pinecone).  
🔹 **Natural Language Interface:** Powered by OpenAI GPT models.  
🔹 **Customer Insights:** Retrieve pain points, objections, goals, and structured data.  
🔹 **Web UI:** Clean chat interface built with HTML, CSS, and JS.  
🔹 **Scalable:** Can be deployed on Railway, Render, or any Flask-supported hosting.  

---

## 🛠️ Tech Stack  
- **Backend:** Flask  
- **Database:** PostgreSQL  
- **Vector DB:** Pinecone  
- **LLM Provider:** OpenAI GPT (GPT-4o by default)  
- **Embeddings:** OpenAI `text-embedding-3-large`  
- **Frontend:** HTML, CSS, JavaScript  
- **Environment Management:** `python-dotenv`  

---

## 📂 Project Structure  
project/
│── app.py # Main Flask application
│── llm_utils.py # OpenAI LLM wrapper
│── pinecone_utils.py # Pinecone search integration
│── postgres_utils.py # PostgreSQL query runner
│── ui_utils.py # UI helpers
│── templates/
│ └── chat.html # Frontend chat interface
│── static/
│ ├── style.css # CSS for styling
│ └── script.js # JS for handling chat interactions
│── .env # Environment variables
│── requirements.txt # Dependencies
│── README.md # Documentation

---

## ⚙️ Setup Instructions  

1. Clone the Repository  

git clone <your-repo-url>
cd <repo-name>

2. Install Dependencies

pip install -r requirements.txt

3. Configure Environment Variables

Create a .env file in the root directory:
env

OPENAI_API_KEY = <your_openai_api_key>
PINECONE_API_KEY= <your_pinecone_api_key>
PINECONE_INDEX = <your_index_name>
PINECONE_NAMESPACE = <your_namespace_name>
DB_NAME= <your_db_name>
DB_USER= <your_db_user_name>
DB_PASSWORD= <your_db_password>
DB_HOST= <your_db_host>
DB_PORT= <your_db_port>

4. Run the Application
python app.py
Now visit 👉 http://localhost:5000


## 🔍 How It Works
User sends a query in chat.

LLM decides whether to use:

Postgres Tool → for structured queries.

Pinecone Tool → for semantic insights.

Tool results are added back into the conversation.

LLM returns a human-friendly response.

UI displays the chatbot’s answer.

## 🧪 Example Queries
“List all customers interested in the Diamond package.” → (Postgres)

“What are the top 3 pain points of customers in the USA?” → (Pinecone)

“How many customers are in the Gold package?” → (Postgres)


## ✨ Acknowledgments
OpenAI for LLM APIs

Pinecone for vector database

PostgreSQL for relational database

Flask for backend framework
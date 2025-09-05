import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(model="gpt-4o", temperature=0.6, openai_api_key=OPENAI_API_KEY)

filter_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a smart assistant that extracts filters for Pinecone metadata queries.
    Output JSON in this format:
    {
        "filters": { ... },
        "reasoning": "..."
    }
    Rules:
    - Only use existing fields: Name, Meeting ID, Email, Location, Phone Number, country, Customer Persona ID, Customer ID, Ad Lead, Ad Lead Qualification Reason, Created, Package of Customer Interest, New AdGroup ID, MeetDate, Qualifying Lead, Lead qualification Reason, Tags from GHL, Sels_Rep Name, Investment motivation, buying urgency, sales pitch refinement, Next Steps, Decision liquidity info, Pain points Objections Outcomes, Engagement Level, Investable Assets, Investment Level, Risk Profile , Supporting Justification/Description, Persona Type.
    - If no filters apply, return empty {} for filters.
    - Return ONLY JSON, no extra text.
    """),
    ("human", "{query}")
])
llm_filter_chain = filter_prompt | llm

import streamlit as st
import json
import sqlite3
from openai import OpenAI
import os

# -----------------------------
# Configuration
# -----------------------------
API_KEY = "[CHATGPT-API-KEY]"
MODEL = "gpt-4o"
DB_PATH = "example.db"

# Fix SSL (only if needed)
#os.environ["SSL_CERT_FILE"] = "C:/Users/81014284/AppData/Local/.certifi/cacert.pem"

# Initialize clients
client = OpenAI(api_key=API_KEY)
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()

# -----------------------------
# LLM: Generate SQL
# -----------------------------
def generate_sql(question: str) -> dict:
    """Convert user question into SQL + justification."""

    system_prompt = "You are a helpful database assistant."

    user_prompt = f"""
    Database: SQLite table 'BIandRproject'

    Columns:
    Manager, Department, Deliverables, Data_Sources, Business_Impact,
    KPIs, Project_Name, Objective, Priority, Problem_Solved,
    Project_Type, Responsable, Stakeholders, Business_Unit

    Task:
    - Create a SQL query to answer: "{question}"
    - Database is case-sensitive
    - Return JSON only

    Format:
    {{
        "SQL": "...",
        "Justification": "..."
    }}
    """

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"}
    )

    return json.loads(response.choices[0].message.content)


# -----------------------------
# DB: Execute SQL
# -----------------------------
def run_sql(query: str):
    """Execute SQL query and return results."""
    try:
        result = cursor.execute(query).fetchall()
        return result
    except Exception as e:
        return f"SQL Error: {e}"


# -----------------------------
# LLM: Final Answer
# -----------------------------
def generate_answer(question: str, sql: str, data):
    """Generate final user-friendly answer."""

    system_prompt = "You are a helpful assistant."

    user_prompt = f"""
    Question: {question}

    SQL used:
    {sql}

    Data:
    {data}

    Provide a clear, concise answer.
    """

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )

    return response.choices[0].message.content.strip()


# -----------------------------
# Orchestrator
# -----------------------------
def chatbot_pipeline(question: str) -> str:
    """Full pipeline: question → SQL → DB → answer."""

    sql_response = generate_sql(question)
    sql_query = sql_response["SQL"]

    data = run_sql(sql_query)

    final_answer = generate_answer(question, sql_query, data)

    return final_answer


# -----------------------------
# Streamlit UI
# -----------------------------
st.title("📊 BI Projects Chatbot")

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User input
if prompt := st.chat_input("Ask a question about your projects..."):

    # Save user message
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response
    response = chatbot_pipeline(prompt)

    # Display assistant response
    with st.chat_message("assistant"):
        st.markdown(response)

    # Save assistant response
    st.session_state.messages.append({
        "role": "assistant",
        "content": response
    })






import streamlit as st
import json
import sqlite3
from openai import OpenAI
import os

# -----------------------------
# Configuration
# -----------------------------
API_KEY = "[CHATGTP-API-KEY]"
MODEL = "gpt-4o"
DB_PATH = "example.db"

# Fix SSL (only if needed)
os.environ["SSL_CERT_FILE"] = "C:/Users/81014284/AppData/Local/.certifi/cacert.pem"

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
    Consider the below database descripton.

        Database Description: This a sqlite database that includes a dataset called 'BIandRproject', it contains a list of analytics and reporting projects developed across different departments.  
        Each record represents a project or dashboard initiative designed to improve operational visibility, track key metrics, and support strategic decision-making.

        Dataset Structure:
        - Manager: Manager responsible for the project portfolio.
        - Department: Department or team where the project belongs (e.g., Sales, Supply Chain).
        - Deliverables: Description of the final output or update frequency (e.g., dashboard updated weekly).
        - Data_Sources: Type of data source used (Code, Excel, Database).
        - Business_Impact: Explanation of how the project benefits operations or decision-making.
        - KPIs: Main goal of the KPI and descriptions.
        - Project_Name: Name of the project.
        - Objective: Main goal of the project.
        - Priority	Priority level assigned to the project.
        - Problem_Solved: Operational issue or gap addressed by the project.
        - Project_Type: Type of solution (e.g., Dashboard, Power App).
        - Responsable: Person responsible for developing or maintaining the project.
        - Stakeholders: Groups or roles that use the project outputs.
        - Business_Unit: Business unit associated with the project (e.g., PFNA, PBNA).

        Print a json file that include the SQL query that respond this business question '{question}', and the justification of your query. 
        Consider that the columns in the database are case-sensite which can affect the query you write and consider that Project_Name, Objective, Problem_Solved and KPIs complement each other about project context.

    Task:
    - Create a SQL query to answer: "{question}"
    - Database is case-sensitive
    - Return JSON only
    - Consider that "Problem_Solved" and "KPIs" complement each other to explain project context.

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






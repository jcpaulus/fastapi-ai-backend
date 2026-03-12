from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
from datetime import datetime
import os
import requests

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

class Submission(BaseModel):
    user: str
    task: str
    answer: str

def init_db():
    conn = sqlite3.connect("submissions.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT,
            task TEXT,
            answer TEXT,
            feedback TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.get("/")
def read_root():
    return {"status": "API running"}

@app.post("/submit")
def submit_answer(data: Submission):
    conn = sqlite3.connect("submissions.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO submissions (user, task, answer, feedback, created_at) VALUES (?, ?, ?, ?, ?)",
        (data.user, data.task, data.answer, None, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
    return {"message": "Submission stored"}

@app.post("/evaluate")
def evaluate_answer(data: Submission):
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not set")

    system_prompt = (
        "You are an internship simulation evaluator. "
        "Evaluate the user's answer for clarity, correctness, usefulness, and actionability. "
        "Return concise feedback in plain English."
    )

    user_prompt = f"""
Task:
{data.task}

User answer:
{data.answer}

Please return:
1. Score out of 10
2. Strengths
3. Weaknesses
4. Suggestions to improve
""".strip()

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.3
    }

    try:
        response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        feedback = result["choices"][0]["message"]["content"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM call failed: {str(e)}")

    conn = sqlite3.connect("submissions.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO submissions (user, task, answer, feedback, created_at) VALUES (?, ?, ?, ?, ?)",
        (data.user, data.task, data.answer, feedback, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

    return {"feedback": feedback}

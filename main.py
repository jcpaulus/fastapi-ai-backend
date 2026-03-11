from fastapi import FastAPI
from pydantic import BaseModel
import sqlite3
from datetime import datetime

app = FastAPI()

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
        "INSERT INTO submissions (user, task, answer, created_at) VALUES (?, ?, ?, ?)",
        (data.user, data.task, data.answer, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
    return {"message": "Submission stored"}


@app.post("/evaluate")
def evaluate_answer(data: Submission):

    feedback = """
Score: 8/10

Strengths:
- Clear structure
- Answer addresses the task

Weaknesses:
- Could include more detail

Suggestion:
Add concrete examples.
"""

    return {"feedback": feedback}


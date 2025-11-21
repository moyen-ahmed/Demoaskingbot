# app.py
import os
import json
import random
import string
from typing import List, Dict, Any, Optional, Literal

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# -----------------------------
# Config (env vars)
# -----------------------------
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")  # or deepseek-reasoner

if not DEEPSEEK_API_KEY:
    print("WARNING: DEEPSEEK_API_KEY is not set. LLM calls will fail until you set it.")

# -----------------------------
# FastAPI scaffolding
# -----------------------------
app = FastAPI(title="Interview Chatbot (LLM)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten for prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Types
# -----------------------------
QuestionType = Literal["mcq", "short"]

class Question(BaseModel):
    id: str
    type: QuestionType
    topic: str
    text: str
    choices: Optional[List[str]] = None
    answer: Any = None  # int for mcq (index), or list[str]/str for short

class StartRequest(BaseModel):
    topic: str
    num_questions: int = 5

class StartResponse(BaseModel):
    session_id: str
    first_question: Question

class AnswerRequest(BaseModel):
    session_id: str
    answer: str

class AnswerResponse(BaseModel):
    correct: bool
    feedback: str
    score: int
    total: int
    next_question: Optional[Question] = None
    finished: bool = False

# -----------------------------
# In-memory sessions
# -----------------------------
SESSIONS: Dict[str, Dict[str, Any]] = {}
def _new_session_id(k: int = 24) -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=k))

def _normalize(s: str) -> str:
    return " ".join(str(s).lower().strip().split())

def _evaluate_answer(q: Question, user_answer: str) -> bool:
    if q.type == "mcq":
        ua = _normalize(user_answer)
        # accept index
        try:
            idx = int(ua)
            return isinstance(q.answer, int) and idx == q.answer
        except ValueError:
            pass
        # accept text match
        if q.choices is None:
            return False
        correct_text = q.choices[q.answer] if isinstance(q.answer, int) else str(q.answer)
        return _normalize(correct_text) == ua

    # short answer
    if isinstance(q.answer, list):
        return _normalize(user_answer) in [_normalize(a) for a in q.answer]
    return _normalize(user_answer) == _normalize(q.answer)

# -----------------------------
# LLM question generation
# -----------------------------
QUESTION_SCHEMA_HINT = """
Return ONLY a single JSON object (no prose) with this exact shape:

{
  "type": "mcq" | "short",
  "text": "string",
  "choices": ["A", "B", "C", "D"]  // only if type == "mcq" (2-6 options allowed)
  "answer": 0                      // integer index if mcq, starting at 0
  // OR if type == "short": "answer": ["list", "of", "acceptable", "answers"]
}
"""

SYSTEM_PROMPT = (
    "You are an interview question generator. "
    "Make clear, unambiguous, self-contained questions suitable for a short coding/tech interview. "
    "Prefer concise wording. For MCQ, keep options distinct and non-overlapping. "
    "Output STRICT JSON per the schema."
)

def _extract_json(text: str) -> dict:
    """
    Robustly extract the first {...} JSON object from the model output.
    """
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in model output.")
    snippet = text[start:end+1]
    return json.loads(snippet)

def _call_deepseek(messages: List[Dict[str, str]]) -> str:
    url = f"{DEEPSEEK_BASE_URL}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": messages,
        # Keep it deterministic so answers are stable
        "temperature": 0.2
        # Many OpenAI-compatible stacks support response_format, but not all.
        # We'll parse JSON manually to be safe.
    }
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    if r.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"LLM error: {r.text}")
    data = r.json()
    try:
        return data["choices"][0]["message"]["content"]
    except Exception:
        raise HTTPException(status_code=502, detail=f"LLM malformed response: {data}")

def _gen_one_question(topic: str) -> Question:
    user_prompt = (
        f"Topic: {topic}\n\n"
        f"Generate ONE interview question on this topic. "
        f"Use either 'mcq' (2–6 choices) or 'short'. "
        f"For math/code, keep numbers small and answers unambiguous. "
        f"{QUESTION_SCHEMA_HINT}"
    )
    content = _call_deepseek(
        [{"role": "system", "content": SYSTEM_PROMPT},
         {"role": "user", "content": user_prompt}]
    )
    obj = _extract_json(content)
    qtype = obj.get("type")
    if qtype not in ("mcq", "short"):
        # force fallback to short if unknown
        qtype = "short"

    # normalize fields
    text = str(obj.get("text", "")).strip()
    if not text:
        raise HTTPException(status_code=502, detail="LLM returned empty question text.")

    choices = obj.get("choices") if qtype == "mcq" else None
    answer = obj.get("answer", None)

    # Basic validations
    if qtype == "mcq":
        if not isinstance(choices, list) or len(choices) < 2:
            raise HTTPException(status_code=502, detail="LLM MCQ has insufficient choices.")
        if not isinstance(answer, int) or answer < 0 or answer >= len(choices):
            raise HTTPException(status_code=502, detail="LLM MCQ 'answer' must be an index.")
    else:
        # short
        if isinstance(answer, str):
            answer = [answer]
        if not isinstance(answer, list) or not answer:
            raise HTTPException(status_code=502, detail="LLM short 'answer' must be a non-empty list.")

    return Question(
        id="q_" + _new_session_id(8),
        type=qtype, topic=topic, text=text, choices=choices, answer=answer
    )

def _gen_questions(topic: str, n: int) -> List[Question]:
    return [_gen_one_question(topic) for _ in range(n)]

# -----------------------------
# API
# -----------------------------
@app.post("/api/start", response_model=StartResponse)
def start_quiz(req: StartRequest):
    topic = req.topic.strip()
    if not topic:
        raise HTTPException(status_code=400, detail="Topic is required.")

    session_id = _new_session_id()
    try:
        questions = _gen_questions(topic, max(1, min(req.num_questions, 10)))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to generate questions: {e}")

    SESSIONS[session_id] = {
        "topic": topic,
        "questions": questions,
        "index": 0,
        "score": 0,
        "total": len(questions),
    }

    return StartResponse(session_id=session_id, first_question=questions[0])

@app.post("/api/answer", response_model=AnswerResponse)
def answer(req: AnswerRequest):
    state = SESSIONS.get(req.session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Invalid session_id")

    idx = state["index"]
    questions: List[Question] = state["questions"]
    if idx >= len(questions):
        return AnswerResponse(
            correct=False, feedback="Quiz already finished.",
            score=state["score"], total=state["total"],
            next_question=None, finished=True
        )

    q = questions[idx]
    is_correct = _evaluate_answer(q, req.answer)
    if is_correct:
        state["score"] += 1

    state["index"] += 1
    finished = state["index"] >= len(questions)
    next_q = None if finished else questions[state["index"]]

    # human-friendly correct answer text
    if q.type == "mcq" and isinstance(q.answer, int):
        corr = q.choices[q.answer]
    else:
        corr = q.answer[0] if isinstance(q.answer, list) else q.answer

    feedback = "✅ Correct!" if is_correct else f"❌ Incorrect. Correct: {corr}"

    return AnswerResponse(
        correct=is_correct,
        feedback=feedback,
        score=state["score"],
        total=state["total"],
        next_question=next_q,
        finished=finished
    )

@app.get("/healthz")
def healthz():
    return {"ok": True}

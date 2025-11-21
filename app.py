# app.py  (STATIC, NO LLM, FULLY FREE)

import random
import string
from typing import List, Dict, Any, Optional, Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# -----------------------------
# FastAPI setup
# -----------------------------
app = FastAPI(title="Interview Chatbot (Static)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ok for local dev; tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Types / Models
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
# Static Question Bank (edit/add as you like)
# -----------------------------
QUESTION_BANK: Dict[str, List[Question]] = {
    "AI": [
        Question(
            id="ai1",
            type="mcq",
            topic="AI",
            text="Which learning paradigm uses labeled data?",
            choices=["Unsupervised", "Reinforcement", "Supervised", "Self-supervised"],
            answer=2,
        ),
        Question(
            id="ai2",
            type="short",
            topic="AI",
            text="Name one common activation function used in neural networks.",
            answer=["relu", "sigmoid", "tanh", "leaky relu", "gelu"],
        ),
        Question(
            id="ai3",
            type="mcq",
            topic="AI",
            text="Which of these is a common loss function for classification?",
            choices=["Mean Squared Error", "Cross-Entropy", "Huber", "L1"],
            answer=1,
        ),
        Question(
            id="ai4",
            type="short",
            topic="AI",
            text="What does ‘CNN’ stand for?",
            answer=["convolutional neural network"],
        ),
    ],
    "Data Science": [
        Question(
            id="ds1",
            type="short",
            topic="Data Science",
            text="What does SQL stand for?",
            answer=["structured query language"],
        ),
        Question(
            id="ds2",
            type="mcq",
            topic="Data Science",
            text="Which metric is usually best for imbalanced binary classification?",
            choices=["Accuracy", "Precision", "Recall", "ROC-AUC"],
            answer=3,
        ),
        Question(
            id="ds3",
            type="short",
            topic="Data Science",
            text="Name one common way to handle missing values.",
            answer=[
                "imputation",
                "mean imputation",
                "median imputation",
                "mode imputation",
                "drop rows",
                "drop columns",
            ],
        ),
        Question(
            id="ds4",
            type="mcq",
            topic="Data Science",
            text="Which plot is best to show the distribution of a single numeric variable?",
            choices=["Box plot", "Scatter plot", "Line chart", "Bar chart"],
            answer=0,
        ),
    ],
    "Web Dev": [
        Question(
            id="wd1",
            type="mcq",
            topic="Web Dev",
            text="Which HTTP method is typically used to create a resource?",
            choices=["GET", "POST", "PUT", "DELETE"],
            answer=1,
        ),
        Question(
            id="wd2",
            type="short",
            topic="Web Dev",
            text="Name a CSS layout technique for two-dimensional layouts.",
            answer=["css grid", "grid"],
        ),
        Question(
            id="wd3",
            type="mcq",
            topic="Web Dev",
            text="Which status code means ‘Not Found’?",
            choices=["200", "301", "404", "500"],
            answer=2,
        ),
        Question(
            id="wd4",
            type="short",
            topic="Web Dev",
            text="What does HTML stand for?",
            answer=["hypertext markup language"],
        ),
    ],
    "Algorithms": [
        Question(
            id="alg1",
            type="mcq",
            topic="Algorithms",
            text="What is the time complexity of binary search on a sorted array?",
            choices=["O(1)", "O(log n)", "O(n)", "O(n log n)"],
            answer=1,
        ),
        Question(
            id="alg2",
            type="short",
            topic="Algorithms",
            text="Name a common sorting algorithm with average complexity O(n log n).",
            answer=["quicksort", "merge sort", "merge-sort", "heap sort", "heapsort"],
        ),
        Question(
            id="alg3",
            type="mcq",
            topic="Algorithms",
            text="Which data structure is best for implementing a FIFO queue?",
            choices=["Stack", "Array", "Linked list", "Hash table"],
            answer=2,
        ),
    ],
    "Math": [
        Question(
            id="math1",
            type="mcq",
            topic="Math",
            text="What is the derivative of x^2?",
            choices=["x", "2x", "x^2", "2"],
            answer=1,
        ),
        Question(
            id="math2",
            type="short",
            topic="Math",
            text="What is 7 * 8?",
            answer=["56"],
        ),
        Question(
            id="math3",
            type="mcq",
            topic="Math",
            text="Which of these is a prime number?",
            choices=["15", "21", "23", "25"],
            answer=2,
        ),
    ],
}

# -----------------------------
# Session handling
# -----------------------------
SESSIONS: Dict[str, Dict[str, Any]] = {}

def _new_session_id(k: int = 24) -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=k))

def _normalize(s: str) -> str:
    return " ".join(str(s).lower().strip().split())

def _evaluate_answer(q: Question, user_answer: str) -> bool:
    if q.type == "mcq":
        ua = _normalize(user_answer)
        # allow entering the index (0,1,2,3)
        try:
            idx = int(ua)
            return isinstance(q.answer, int) and idx == q.answer
        except ValueError:
            pass
        # or matching the option text
        if q.choices is None:
            return False
        correct_text = q.choices[q.answer] if isinstance(q.answer, int) else str(q.answer)
        return _normalize(correct_text) == ua

    # short answer
    if isinstance(q.answer, list):
        return _normalize(user_answer) in [_normalize(a) for a in q.answer]
    return _normalize(user_answer) == _normalize(q.answer)

def _pick_questions(topic: str, n: int) -> List[Question]:
    bank = QUESTION_BANK.get(topic)
    if not bank:
        raise HTTPException(status_code=400, detail=f"Unknown topic: {topic}")
    if n > len(bank):
        n = len(bank)
    return random.sample(bank, n)

# -----------------------------
# API endpoints
# -----------------------------
@app.post("/api/start", response_model=StartResponse)
def start_quiz(req: StartRequest):
    topic = req.topic.strip()
    if not topic:
        raise HTTPException(status_code=400, detail="Topic is required.")

    questions = _pick_questions(topic, max(1, min(req.num_questions, 10)))
    session_id = _new_session_id()

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
            correct=False,
            feedback="Quiz already finished.",
            score=state["score"],
            total=state["total"],
            next_question=None,
            finished=True,
        )

    q = questions[idx]
    is_correct = _evaluate_answer(q, req.answer)

    if is_correct:
        state["score"] += 1

    state["index"] += 1
    finished = state["index"] >= len(questions)
    next_q = None if finished else questions[state["index"]]

    # human-readable correct answer
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
        finished=finished,
    )

@app.get("/healthz")
def healthz():
    return {"ok": True}

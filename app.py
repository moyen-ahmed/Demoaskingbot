# app.py  (STATIC, NO LLM, FULLY FREE)

import random
import string
from typing import List, Dict, Any, Optional, Literal
import json
from pathlib import Path


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

# # -----------------------------
# # Static Question Bank (expanded)
# # -----------------------------
# QUESTION_BANK: Dict[str, List[Question]] = {

#     # ==================== AI ====================
#     "AI": [
#         Question(
#             id="ai1", type="mcq", topic="AI",
#             text="Which learning paradigm uses labeled data?",
#             choices=["Unsupervised", "Reinforcement", "Supervised", "Self-supervised"],
#             answer=2,
#         ),
#         Question(
#             id="ai2", type="short", topic="AI",
#             text="Name one activation function used in deep learning.",
#             answer=["relu", "sigmoid", "tanh", "gelu", "selu", "leaky relu"],
#         ),
#         Question(
#             id="ai3", type="mcq", topic="AI",
#             text="Which loss function is commonly used for multi-class classification?",
#             choices=["Binary Cross-Entropy", "Huber Loss", "Categorical Cross-Entropy", "MAE"],
#             answer=2,
#         ),
#         Question(
#             id="ai4", type="short", topic="AI",
#             text="What does CNN stand for?",
#             answer=["convolutional neural network"],
#         ),
#         Question(
#             id="ai5", type="short", topic="AI",
#             text="What does RNN stand for?",
#             answer=["recurrent neural network"],
#         ),
#         Question(
#             id="ai6", type="mcq", topic="AI",
#             text="Which of these is a transformer-based model?",
#             choices=["VGG16", "ResNet", "BERT", "LeNet"],
#             answer=2,
#         ),
#         Question(
#             id="ai7", type="short", topic="AI",
#             text="Name one optimization algorithm used in training neural networks.",
#             answer=["adam", "sgd", "rmsprop", "adagrad"],
#         ),
#            Question(
#             id="ai8",
#             type="short",
#             topic="AI",
#             text=(
#                 "In 3–4 lines, explain the difference between supervised and "
#                 "unsupervised learning.\n"
#                 "Your answer should mention labeled data and that supervised "
#                 "learns a mapping from inputs to outputs, while unsupervised "
#                 "works with unlabeled data."
#             ),
#             answer=[
#                 # we just store key words; user can write full sentences
#                 "labeled data mapping inputs outputs unlabeled data unsupervised",
#                 "supervised uses labeled data unsupervised uses unlabeled data",
#             ],
#         ),
#         Question(
#             id="ai9",
#             type="short",
#             topic="AI",
#             text=(
#                 "In 3–4 lines, describe what overfitting means in machine learning.\n"
#                 "Mention training data, memorizing patterns, and poor "
#                 "generalization to new data."
#             ),
#             answer=[
#                 "memorizes training data poor generalization new data overfitting",
#                 "fits training data too well performs badly on unseen data",
#             ],
#         ),
#     ],


#     # ==================== DATA SCIENCE ====================
#     "Data Science": [
#         Question(
#             id="ds1", type="short", topic="Data Science",
#             text="What does SQL stand for?",
#             answer=["structured query language"],
#         ),
#         Question(
#             id="ds2", type="mcq", topic="Data Science",
#             text="Which metric works best for imbalanced classification?",
#             choices=["Accuracy", "Recall", "MAE", "RMSE"],
#             answer=1,
#         ),
#         Question(
#             id="ds3", type="short", topic="Data Science",
#             text="Name a common missing-value handling method.",
#             answer=["mean imputation", "median imputation", "mode imputation", "drop rows", "drop columns"],
#         ),
#         Question(
#             id="ds4", type="mcq", topic="Data Science",
#             text="Which visualization shows numeric distribution?",
#             choices=["Box Plot", "Pie Chart", "Bar Chart", "Scatter Plot"],
#             answer=0,
#         ),
#         Question(
#             id="ds5", type="short", topic="Data Science",
#             text="Name one Python library used for data analysis.",
#             answer=["pandas", "numpy"],
#         ),
#         Question(
#             id="ds6", type="mcq", topic="Data Science",
#             text="Which step is part of the CRISP-DM process?",
#             choices=["Deployment", "Encryption", "Backpropagation", "Tokenization"],
#             answer=0,
#         ),
#                 Question(
#             id="ds7",
#             type="short",
#             topic="Data Science",
#             text=(
#                 "In 3–4 lines, explain the difference between mean, median, "
#                 "and mode.\nMention that they are measures of central tendency "
#                 "and when median is more robust."
#             ),
#             answer=[
#                 "mean average median middle value mode most frequent value",
#                 "median robust to outliers mean sensitive to outliers",
#             ],
#         ),
#         Question(
#             id="ds8",
#             type="short",
#             topic="Data Science",
#             text=(
#                 "In 3–4 lines, explain what a confusion matrix is and what it "
#                 "shows for a classifier.\nMention true positives, false positives, "
#                 "true negatives and false negatives."
#             ),
#             answer=[
#                 "table of true positives false positives true negatives false negatives",
#                 "matrix showing tp fp tn fn performance of classifier",
#             ],
#         ),

#     ],


#     # ==================== WEB DEVELOPMENT ====================
#     "Web Dev": [
#         Question(
#             id="wd1", type="mcq", topic="Web Dev",
#             text="Which HTTP method is used to create a resource?",
#             choices=["GET", "POST", "PUT", "DELETE"],
#             answer=1,
#         ),
#         Question(
#             id="wd2", type="short", topic="Web Dev",
#             text="Name one 2D CSS layout tool.",
#             answer=["grid", "css grid"],
#         ),
#         Question(
#             id="wd3", type="mcq", topic="Web Dev",
#             text="Which status code means 'Not Found'?",
#             choices=["200", "301", "404", "500"],
#             answer=2,
#         ),
#         Question(
#             id="wd4", type="short", topic="Web Dev",
#             text="What does HTML stand for?",
#             answer=["hypertext markup language"],
#         ),
#         Question(
#             id="wd5", type="short", topic="Web Dev",
#             text="What does CSS stand for?",
#             answer=["cascading style sheets"],
#         ),
#         Question(
#             id="wd6", type="mcq", topic="Web Dev",
#             text="Which tag is used to create a hyperlink?",
#             choices=["<link>", "<a>", "<href>", "<url>"],
#             answer=1,
#         ),
#     ],


#     # ==================== ALGORITHMS ====================
#     "Algorithms": [
#         Question(
#             id="alg1", type="mcq", topic="Algorithms",
#             text="Time complexity of binary search?",
#             choices=["O(1)", "O(log n)", "O(n)", "O(n^2)"],
#             answer=1,
#         ),
#         Question(
#             id="alg2", type="short", topic="Algorithms",
#             text="Give one O(n log n) sorting algorithm.",
#             answer=["quicksort", "merge sort", "heapsort"],
#         ),
#         Question(
#             id="alg3", type="mcq", topic="Algorithms",
#             text="Best structure for FIFO?",
#             choices=["Stack", "Queue", "Graph", "Tree"],
#             answer=1,
#         ),
#         Question(
#             id="alg4", type="short", topic="Algorithms",
#             text="Name the algorithm used to find the shortest path in a weighted graph.",
#             answer=["dijkstra", "dijkstra's algorithm"],
#         ),
#         Question(
#             id="alg5", type="mcq", topic="Algorithms",
#             text="Which of these is a divide-and-conquer algorithm?",
#             choices=["DFS", "BFS", "Merge Sort", "Bubble Sort"],
#             answer=2,
#         ),
#     ],


#     # ==================== MATH ====================
#     "Math": [
#         Question(
#             id="math1", type="mcq", topic="Math",
#             text="Derivative of x^2?",
#             choices=["x", "2x", "x^2", "2"],
#             answer=1,
#         ),
#         Question(
#             id="math2", type="short", topic="Math",
#             text="What is 7 × 8?",
#             answer=["56"],
#         ),
#         Question(
#             id="math3", type="mcq", topic="Math",
#             text="Which is a prime number?",
#             choices=["15", "21", "23", "25"],
#             answer=2,
#         ),
#         Question(
#             id="math4", type="short", topic="Math",
#             text="What is the square root of 81?",
#             answer=["9"],
#         ),
#         Question(
#             id="math5", type="mcq", topic="Math",
#             text="What is 12 / 3?",
#             choices=["4", "3", "6", "2"],
#             answer=0,
#         ),
#     ],
# }
# -----------------------------
# Static Question Bank loaded from JSON file
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent
QUESTION_FILE = BASE_DIR / "questions.json"

if not QUESTION_FILE.exists():
    raise RuntimeError(f"questions.json file not found at: {QUESTION_FILE}")

with QUESTION_FILE.open("r", encoding="utf-8") as f:
    raw_questions = json.load(f)

QUESTION_BANK: Dict[str, List[Question]] = {}
for topic, q_list in raw_questions.items():
    QUESTION_BANK[topic] = [Question(**q) for q in q_list]


# -----------------------------
# Session handling
# -----------------------------
SESSIONS: Dict[str, Dict[str, Any]] = {}

def _new_session_id(k: int = 24) -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=k))

def _normalize(s: str) -> str:
    return " ".join(str(s).lower().strip().split())

def _evaluate_answer(q: Question, user_answer: str) -> bool:
    ua = _normalize(user_answer)

    if q.type == "mcq":
        # allow entering the index number
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

    # ---------- short answer ----------
    # For short answers we treat each candidate as a set of required words.
    # If the user's answer contains ALL words of ANY candidate, we accept it.
    if isinstance(q.answer, list):
        for candidate in q.answer:
            words = _normalize(candidate).split()
            if all(w in ua for w in words):
                return True
        return False

    # single-string answer: just check all words appear
    target_words = _normalize(str(q.answer)).split()
    return all(w in ua for w in target_words)


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

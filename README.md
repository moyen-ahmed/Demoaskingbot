A fully free, LLM-independent, interview-question chatbot built using:

FastAPI (backend API)---should be inastall

Static Question Bank (JSON file) – no paid API

HTML + CSS + JavaScript frontend

Uvicorn server

POST /api/start   → start quiz
POST /api/answer  → submit answer
GET  /healthz     → server health

project/
│
├── app.py                # FastAPI backend
├── questions.json        #Question bank (big file with all topics)
├── index.html            # Frontend UI            # Frontend logic
│
└── myenv/  

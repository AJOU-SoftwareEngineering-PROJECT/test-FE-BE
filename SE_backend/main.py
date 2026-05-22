import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure this file's directory is on sys.path so internal imports work
sys.path.insert(0, os.path.dirname(__file__))

from author.controller import router as author_router
from comment.controller import router as comment_router, subcomment_router
from scrap.controller import router as scrap_router, user_router as scrap_user_router
from alarm.controller import router as alarm_router
from post.controller import router as post_router
from frontend_api.controller import router as frontend_api_router, create_frontend_tables
from db.database import init_db


app = FastAPI(title="SE Interactive Reading Backend")


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "SE Backend API is running",
        "frontend_api": "/api/books",
        "dashboard": "/api/dashboard",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "SE Backend",
    }


app.include_router(frontend_api_router)

app.include_router(author_router)
app.include_router(comment_router)
app.include_router(subcomment_router)
app.include_router(scrap_router)
app.include_router(scrap_user_router)
app.include_router(alarm_router)
app.include_router(post_router)


@app.on_event("startup")
def on_startup():
    init_db()
    create_frontend_tables()
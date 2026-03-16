"""
FinVise AI - Indian Stock Market Intelligence Platform
FastAPI Backend
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import uvicorn
import os
import logging

from routers import stock, news, ai_brief, video

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="FinVise AI - Stock Intelligence API",
    description="Indian Stock Market Intelligence Platform with AI Video Brief Generation",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stock.router, prefix="/api/stock", tags=["Stock Data"])
app.include_router(news.router, prefix="/api/news", tags=["News"])
app.include_router(ai_brief.router, prefix="/api/brief", tags=["AI Brief"])
app.include_router(video.router, prefix="/api/video", tags=["Video Generation"])


@app.get("/")
async def root():
    return {
        "message": "FinVise AI Stock Intelligence API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

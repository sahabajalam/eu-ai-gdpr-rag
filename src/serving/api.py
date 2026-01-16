
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
import logging

from src.generation.generator import RAGGenerator

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api")

app = FastAPI(title="EU AI Act & GDPR RAG API")

# CORS for Vite (Localhost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Generator (Cold Start)
# We initialize it at module level so it loads once
try:
    generator = RAGGenerator()
except Exception as e:
    logger.error(f"Failed to initialize RAGGenerator: {e}")
    generator = None

class ChatRequest(BaseModel):
    query: str
    regulation: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    confidence: float
    context: List[Dict[str, Any]]
    graph_data: Dict[str, Any]

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not generator:
        raise HTTPException(status_code=500, detail="RAG Generator not initialized")
        
    logger.info(f"Received query: {request.query}")
    try:
        result = generator.generate_answer(request.query, regulation_filter=request.regulation)
        return ChatResponse(
            answer=result['answer'],
            confidence=result.get('confidence', 0),
            context=result.get('context', []),
            graph_data=result.get('graph_data', {"nodes": [], "edges": []})
        )
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    if not generator:
        raise HTTPException(status_code=500, detail="RAG Generator not initialized")
        
    logger.info(f"Received streaming query: {request.query} (Filter: {request.regulation})")
    return StreamingResponse(
        generator.generate_answer_stream(request.query, regulation_filter=request.regulation),
        media_type="application/x-ndjson"
    )

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("src.serving.api:app", host="0.0.0.0", port=8000, reload=True)

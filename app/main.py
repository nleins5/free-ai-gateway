import time
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1 import chat, images, rag, audio, conversations, users
from app.api import admin
from app.config import settings, RAG_STORE_PATH
from app.core.state import StateStore
from app.services.rag import SimpleRAGStore, RAGService
from app.services.router import RouterService
from app.database import init_db

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize Database
    await init_db()
    
    # Initialize StateStore
    state_store = StateStore()
    app.state.state_store = state_store
    
    # Initialize RouterService
    app.state.router_service = RouterService(state_store)
    
    # Initialize RAG Store and Service
    rag_store = SimpleRAGStore(RAG_STORE_PATH)
    await rag_store.initialize()
    app.state.rag_service = RAGService(rag_store)
    
    yield
    # Any cleanup can go here

app = FastAPI(
    title="Aether AI Gateway",
    description="Modular, high-availability AI provider routing gateway.",
    version="2.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(chat.router, prefix="/v1/chat", tags=["Chat"])
app.include_router(images.router, prefix="/v1/images", tags=["Images"])
app.include_router(rag.router, prefix="/v1/rag", tags=["RAG"])
app.include_router(audio.router, prefix="/v1/audio", tags=["Audio"])
app.include_router(conversations.router, prefix="/v1/conversations", tags=["Conversations"])
app.include_router(users.router, prefix="/v1/users", tags=["Users"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])



@app.get("/health")
async def health_check():
    return {
        "status": "online",
        "timestamp": time.time(),
        "version": "2.0.0"
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log the exception here
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {str(exc)}"}
    )

# Serve UI
ui_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ui", "dist")
if os.path.exists(ui_path):
    assets_path = os.path.join(ui_path, "assets")
    if os.path.exists(assets_path):
        app.mount("/assets", StaticFiles(directory=assets_path), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_ui(full_path: str):
        file_path = os.path.join(ui_path, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(ui_path, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

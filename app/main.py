import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import chat, images, rag
from app.api import admin
from app.config import settings

app = FastAPI(
    title="Aether AI Gateway",
    description="Modular, high-availability AI provider routing gateway.",
    version="2.0.0"
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

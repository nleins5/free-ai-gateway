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

from fastapi.responses import HTMLResponse

app = FastAPI(
    title="Aether AI Gateway",
    description="Modular, high-availability AI provider routing gateway.",
    version="2.0.0",
    lifespan=lifespan,
    docs_url=None,  # Disable default swagger
    redoc_url=None  # Disable default redoc
)

@app.get("/docs", include_in_schema=False)
async def custom_api_docs():
    html_content = """
    <!DOCTYPE html>
    <html>
      <head>
        <title>Aether AI Gateway - API Reference</title>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <style>
          body { 
            margin: 0; 
            background-color: #0D0D12 !important; 
            color: #FAF8F5 !important;
          }
          
          /* Ambient Gold Glow Overlay */
          body::before {
            content: '';
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background-image: radial-gradient(circle at top right, rgba(201, 168, 76, 0.15), transparent 40%),
                              radial-gradient(circle at bottom left, rgba(201, 168, 76, 0.08), transparent 40%);
            pointer-events: none;
            z-index: 9999;
          }
          
          /* Force Midnight Luxe Theme for all modes */
          .light-mode, .dark-mode, :root {
            /* Theme Base Colors */
            --theme-color-1: #FAF8F5 !important;
            --theme-color-2: rgba(250, 248, 245, 0.7) !important;
            --theme-color-3: rgba(250, 248, 245, 0.4) !important;
            --theme-color-accent: #C9A84C !important;
            
            /* Scalar Text Colors */
            --scalar-color-1: #FAF8F5 !important;
            --scalar-color-2: rgba(250, 248, 245, 0.7) !important;
            --scalar-color-3: rgba(250, 248, 245, 0.4) !important;
            --scalar-color-accent: #C9A84C !important;
            
            /* Theme Backgrounds - Solid to prevent modal overlap */
            --theme-background-1: #0D0D12 !important;
            --theme-background-2: #14141B !important;
            --theme-background-3: #1A1A24 !important;
            --theme-background-accent: #C9A84C !important;
            --theme-border-color: rgba(255, 255, 255, 0.05) !important;
            
            /* Scalar Backgrounds - Solid to prevent modal overlap */
            --scalar-background-1: #0D0D12 !important;
            --scalar-background-2: #14141B !important;
            --scalar-background-3: #1A1A24 !important;
            --scalar-border-color: rgba(255, 255, 255, 0.05) !important;
            
            /* Sidebar Variables */
            --scalar-sidebar-color-1: #FAF8F5 !important;
            --scalar-sidebar-color-2: rgba(250, 248, 245, 0.7) !important;
            --scalar-sidebar-background-1: #0D0D12 !important;
            
            /* Method Colors */
            --theme-color-green: #C9A84C !important;
            --theme-color-blue: #C9A84C !important;
            --theme-color-orange: #C9A84C !important;
          }
          
          .scalar-app {
            font-family: 'Inter', sans-serif !important;
          }
          
          /* Custom font styling */
          .scalar-app * {
            font-family: 'Inter', sans-serif !important;
          }
          
          /* Force heading and text colors manually if variables fail */
          .scalar-app h1, .scalar-app h2, .scalar-app h3, .scalar-app h4, .scalar-app h5, .scalar-app h6, .scalar-app p, .scalar-app span, .scalar-app div {
            color: var(--scalar-color-1);
          }
        </style>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
      </head>
      <body>
        <script id="api-reference" data-url="/openapi.json" data-theme="moon"></script>
        <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference"></script>
        <script>
          // Intercept clicks to force them to open in a new web tab
          document.addEventListener('click', function(e) {
            const el = e.target.closest('a') || e.target.closest('div.sidebar-item') || e.target;
            const text = el.innerText || el.textContent || '';
            
            if (text.includes('VS Code')) {
              e.preventDefault();
              e.stopPropagation();
              window.open('https://vscode.dev', '_blank');
            }
            else if (text.includes('Cursor')) {
              e.preventDefault();
              e.stopPropagation();
              window.open('https://cursor.com', '_blank');
            }
            else if (text.includes('Generate MCP')) {
              e.preventDefault();
              e.stopPropagation();
              window.open('https://scalar.com/mcp', '_blank'); // Hoặc link tải MCP của Scalar
            }
          }, true);
        </script>
      </body>
    </html>
    """
    return HTMLResponse(content=html_content)

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
app.include_router(admin.router, prefix="/v1/admin", tags=["Admin"])



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
    ssl_keyfile = os.path.join(os.path.dirname(__file__), "..", "localhost.key")
    ssl_certfile = os.path.join(os.path.dirname(__file__), "..", "localhost.crt")

    if os.path.exists(ssl_keyfile) and os.path.exists(ssl_certfile):
        print("Starting with HTTPS...")
        uvicorn.run(app, host="0.0.0.0", port=8443, ssl_keyfile=ssl_keyfile, ssl_certfile=ssl_certfile)
    else:
        print("Starting with HTTP...")
        uvicorn.run(app, host="0.0.0.0", port=8000)

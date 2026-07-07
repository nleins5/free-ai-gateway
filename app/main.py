import time
import os
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

# ── Structured Logging ────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-5s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
# Silence noisy libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logger = logging.getLogger("gateway")

from app.api.v1 import chat, images, rag, audio, conversations, users
from app.api import admin
from app.api import ollama
from app.config import settings, RAG_STORE_PATH, ALLOWED_ORIGINS
from app.core.state import StateStore
from app.services.rag import SimpleRAGStore, RAGService
from app.services.router import RouterService
from app.database import init_db
from app.dependencies import verify_gateway

from contextlib import asynccontextmanager


async def load_custom_providers_from_db():
    """Load dynamically-added providers from DB and register them into the routing chain."""
    try:
        from app.database import AsyncSessionLocal
        from app.db_models import CustomProvider
        from app.core.providers import PROVIDER_REGISTRY, Provider
        from app.config import settings

        async with AsyncSessionLocal() as db:
            from sqlalchemy import select
            result = await db.execute(select(CustomProvider).where(CustomProvider.is_active == True))
            custom_providers = result.scalars().all()

        for cp in custom_providers:
            if cp.key in PROVIDER_REGISTRY:
                continue  # Skip if already registered (e.g., after hot-reload)

            # Inject API key into environment (decrypt from DB)
            from app.core.encryption import decrypt_key
            env_key = f"CUSTOM_{cp.key.upper()}_API_KEY"
            os.environ[env_key] = decrypt_key(cp.api_key)

            PROVIDER_REGISTRY[cp.key] = Provider(
                key=cp.key,
                name=cp.name,
                base_url=cp.base_url,
                api_key_env=env_key,
                model_env=f"CUSTOM_{cp.key.upper()}_MODEL",
                default_model=cp.default_model,
            )

            if cp.key not in settings.provider_chain:
                settings.provider_chain.append(cp.key)
            settings.dynamic_weights[cp.key] = cp.weight

            for task in (cp.tasks or []):
                if task in settings.task_tiers and cp.key not in settings.task_tiers[task]:
                    settings.task_tiers[task].append(cp.key)

        if custom_providers:
            logger.info(f"Loaded {len(custom_providers)} custom provider(s) from DB: {[p.key for p in custom_providers]}")

    except Exception as e:
        logger.warning(f"Could not load custom providers from DB: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Skip DB initialization in serverless environments
    is_serverless = os.getenv('VERCEL') == '1'
    db_available = False

    if not is_serverless:
        # Initialize Database — graceful failure so app doesn't crash
        try:
            await init_db()
            db_available = True
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.warning(f"Database unavailable — running without persistence: {e}")

        if db_available:
            # ── Load persisted custom providers from DB ──────────────────
            await load_custom_providers_from_db()

        # Initialize RAG Store and Service (local only)
        try:
            rag_store = SimpleRAGStore(RAG_STORE_PATH)
            await rag_store.initialize()
            app.state.rag_service = RAGService(rag_store)
        except Exception as e:
            logger.warning(f"RAG store init failed: {e}")
            app.state.rag_service = None
    else:
        # Serverless: use in-memory storage
        app.state.rag_service = None

    app.state.db_available = db_available

    # Initialize StateStore and RouterService (these work without DB)
    state_store = StateStore()
    app.state.state_store = state_store
    app.state.router_service = RouterService(state_store)

    yield
    # Cleanup

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

# CORS — locked to allowed origins (set ALLOWED_ORIGINS env var in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes — all /v1/* routes require gateway secret in production
from fastapi import Depends

app.include_router(chat.router, prefix="/v1/chat", tags=["Chat"], dependencies=[Depends(verify_gateway)])
app.include_router(images.router, prefix="/v1/images", tags=["Images"], dependencies=[Depends(verify_gateway)])
app.include_router(rag.router, prefix="/v1/rag", tags=["RAG"], dependencies=[Depends(verify_gateway)])
app.include_router(audio.router, prefix="/v1/audio", tags=["Audio"], dependencies=[Depends(verify_gateway)])
app.include_router(conversations.router, prefix="/v1/conversations", tags=["Conversations"], dependencies=[Depends(verify_gateway)])
app.include_router(users.router, prefix="/v1/users", tags=["Users"], dependencies=[Depends(verify_gateway)])
app.include_router(admin.router, prefix="/v1/admin", tags=["Admin"])

# Ollama-compatible endpoints — no auth required, drop-in replacement
app.include_router(ollama.router, prefix="/api", tags=["Ollama Compat"])



@app.get("/health")
async def health_check(request: Request):
    state_store = request.app.state.state_store
    all_states = state_store.get_all_states()
    providers = all_states.get("providers", {})
    healthy = sum(1 for p in providers.values() if not p.get("on_cooldown", False))
    total = len(providers)
    db_ok = getattr(request.app.state, 'db_available', False)
    return {
        "status": "online",
        "timestamp": time.time(),
        "version": "2.2.0",
        "database": "connected" if db_ok else "disconnected",
        "providers": {"healthy": healthy, "total": total},
        "daily_cost_usd": all_states.get("total_cost_usd", 0),
    }

@app.middleware("http")
async def add_request_timing(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = (time.perf_counter() - start) * 1000
    response.headers["X-Response-Time"] = f"{elapsed:.0f}ms"
    if elapsed > 5000:  # Log slow requests (>5s)
        logger.warning(f"Slow request: {request.method} {request.url.path} took {elapsed:.0f}ms")
    return response

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error. Please try again later."}
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

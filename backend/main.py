from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.api.routes import router
from backend.api.auth_routes import router as auth_router
from backend.utils.config import get_settings
from backend.utils.db import init_db
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the database on startup (idempotent)."""
    init_db()
    yield


# Create app
app = FastAPI(
    title="Prelegal NDA Generator API",
    description="API for generating NDA documents from templates",
    version="1.0.0",
    lifespan=lifespan,
)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)
app.include_router(auth_router)

# Serve the statically exported frontend (frontend/out) when it exists.
# Mounted last so /api/* and /docs keep matching first; `html=True` resolves
# directory requests (e.g. /nda-creator/) to their index.html.
if settings.frontend_path.is_dir():
    app.mount("/", StaticFiles(directory=str(settings.frontend_path), html=True), name="frontend")
else:
    @app.get("/")
    async def root():
        """Fallback root when the frontend has not been built."""
        return {
            "message": "Prelegal NDA Generator API",
            "docs": "/docs",
            "openapi": "/openapi.json",
            "hint": "Frontend not built: run `npm run build` in frontend/ to serve the app here.",
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=True,
    )

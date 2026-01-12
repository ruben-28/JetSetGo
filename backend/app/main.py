"""
JetSetGo API - Main Application
FastAPI backend with API Gateway pattern.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.db import Base, engine
from app.auth.routes import router as auth_router
from app.travel.routes import router as travel_router
from app.ai.routes import router as ai_router


# ============================================================================
# Application Setup
# ============================================================================

app = FastAPI(
    title="JetSetGo API",
    description="Travel search platform with AI assistance",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ============================================================================
# CORS Middleware (for Desktop App Integration)
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Database Initialization
# ============================================================================

Base.metadata.create_all(bind=engine)

# ============================================================================
# Router Registration
# ============================================================================

app.include_router(auth_router)
app.include_router(travel_router)
app.include_router(ai_router)

# ============================================================================
# Health Check
# ============================================================================

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "JetSetGo API",
        "version": "1.0.0"
    }


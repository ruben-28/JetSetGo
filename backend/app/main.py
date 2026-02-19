"""
Fichier: backend/app/main.py
Objectif: Point d'entrée principal de l'API FastAPI.
Responsabilités: 
- Configuration de l'application (CORS, Middleware).
- Enregistrement des routeurs (Auth, Travel, AI).
- Gestion globale des erreurs.
- Vérification de l'état (Health Check).
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()

from app.auth.db import Base, engine
from app.auth.routes import router as auth_router
from app.travel.routes import router as travel_router
from app.ai.routes import router as ai_router


# ============================================================================
# Configuration de l'Application
# ============================================================================

app = FastAPI(
    title="JetSetGo API",
    description="Plateforme de recherche de voyage avec assistance IA",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ============================================================================
# Middleware CORS (Intégration App Desktop)
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restreindre en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Initialisation de la Base de Données
# ============================================================================

# Base.metadata.create_all(bind=engine)

# ============================================================================
# Enregistrement des Routeurs
# ============================================================================

app.include_router(auth_router)
app.include_router(travel_router)
app.include_router(ai_router)

# ============================================================================
# Vérification de l'État (Health Check)
# ============================================================================

@app.get("/health")
async def health():
    """
    Endpoint de vérification de l'état de l'API.
    Retourne le statut, le nom du service et la version.
    """
    return {
        "status": "ok",
        "service": "JetSetGo API",
        "version": "1.0.0"
    }


# ============================================================================
# Débogage : Logs des Erreurs de Validation
# ============================================================================
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import logging

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """
    Gestionnaire global des erreurs de validation (422).
    Loggue les détails de l'erreur et le corps de la requête pour faciliter le débogage.
    """
    logging.error(f"Erreur de Validation : {exc.errors()}")
    logging.error(f"Corps de la requête : {exc.body}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": str(exc.body)},
    )


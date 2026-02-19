"""
Module de Schémas AI
Modèles Pydantic pour les requêtes et réponses de consultation AI.
"""

import os
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Literal, Dict, Any, List, Optional


# ============================================================================
# DTOs (Data Transfer Objects) pour le Contexte
# ============================================================================

class OfferDTO(BaseModel):
    """DTO stable pour le contexte d'offre de vol"""
    id: str
    price: float
    currency: str = "EUR"
    airline: str
    departure: str
    destination: str
    depart_date: str
    return_date: Optional[str] = None
    duration_min: int
    stops: int
    baggage: Optional[str] = None
    refund_policy: Optional[str] = None


class BookingDTO(BaseModel):
    """DTO stable pour le contexte de réservation"""
    booking_id: str
    offer_id: str
    status: str
    user_id: Optional[int] = None
    created_at: str
    price: float
    adults: int


class ConsultContext(BaseModel):
    """
    Contexte typé pour la consultation LLM.
    Valide les champs requis en fonction du mode de consultation.
    """
    selected_offers: Optional[List[OfferDTO]] = None
    booking_info: Optional[BookingDTO] = None
    budget_max: Optional[int] = None
    user_prefs: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Modèles de Requête/Réponse
# ============================================================================

class ConsultRequest(BaseModel):
    """Modèle de requête pour la consultation LLM"""
    mode: Literal["compare", "budget", "policy", "free"]
    message: str = Field(..., min_length=1)
    context: ConsultContext = Field(default_factory=ConsultContext)
    language: str = Field(default="fr", pattern="^(fr|en)$")
    stream: bool = Field(default=False)  # Préparé pour le streaming futur
    
    @field_validator("message")
    @classmethod
    def validate_message_length(cls, v: str) -> str:
        """Valider la longueur du message par rapport à MAX_PROMPT_CHARS"""
        max_chars = int(os.getenv("MAX_PROMPT_CHARS", "8000"))
        if len(v) > max_chars:
            raise ValueError(f"Message trop long (max {max_chars} caractères)")
        return v
    
    @model_validator(mode="after")
    def validate_context_for_mode(self):
        """Valider que le contexte contient les champs requis pour le mode"""
        if self.mode == "compare":
            if not self.context.selected_offers or len(self.context.selected_offers) < 2:
                raise ValueError("Le mode 'compare' nécessite au moins 2 offres dans context.selected_offers")
        elif self.mode == "budget":
            if self.context.budget_max is None:
                raise ValueError("Le mode 'budget' nécessite context.budget_max")
        return self
    
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "mode": "compare",
                "message": "Quelle offre choisir pour un voyage en famille?",
                "context": {
                    "selected_offers": [
                        {
                            "id": "A1", "price": 250, "currency": "EUR", "airline": "AirFrance",
                            "departure": "Paris", "destination": "Rome", "depart_date": "2026-02-15",
                            "return_date": "2026-02-22", "duration_min": 120, "stops": 0
                        },
                        {
                            "id": "B2", "price": 180, "currency": "EUR", "airline": "RyanAir",
                            "departure": "Paris", "destination": "Rome", "depart_date": "2026-02-15",
                            "return_date": "2026-02-22", "duration_min": 180, "stops": 1
                        }
                    ]
                },
                "language": "fr"
            }]
        }
    }


class ConsultResponse(BaseModel):
    """Modèle de réponse pour la consultation LLM"""
    answer: str
    model: str  # Toujours présent (ex: "qwen2.5:3b" ou "mock-ollama")
    tokens_estimate: Optional[int] = None
    sources: List[str] = Field(default_factory=list)  # RAG futur
    meta: Dict[str, Any] = Field(
        default_factory=lambda: {"mock": False}
    )  # DOIT inclure le booléen "mock" et le "reason" optionnel
    
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "answer": "Je recommande l'offre AirFrance car...",
                "model": "qwen2.5:3b",
                "tokens_estimate": 145,
                "sources": [],
                "meta": {
                    "mock": False,
                    "mode": "compare",
                    "offers_compared": 2
                }
            }]
        }
    }

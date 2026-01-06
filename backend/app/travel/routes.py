from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import List, Optional
from app.gateway.travel_provider import TravelProviderGateway

router = APIRouter(prefix="/travel", tags=["travel"])
gateway = TravelProviderGateway()

class OfferOut(BaseModel):
    id: str
    destination: str
    depart_date: str
    return_date: str
    airline: str
    price: int
    duration_min: int
    stops: int
    score: float

class OfferDetailsOut(BaseModel):
    id: str
    baggage: str
    refund_policy: str
    notes: str
    hotel_suggestion: dict

@router.get("/search", response_model=List[OfferOut])
def search(
    destination: str = Query(..., min_length=2),
    depart_date: str = Query(..., description="YYYY-MM-DD"),
    return_date: str = Query(..., description="YYYY-MM-DD"),
    budget: Optional[int] = Query(None, ge=0)
):
    return gateway.search_offers(destination, depart_date, return_date, budget or 0)

@router.get("/details/{offer_id}", response_model=OfferDetailsOut)
def details(offer_id: str):
    return gateway.get_details(offer_id)

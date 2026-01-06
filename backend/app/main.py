from fastapi import FastAPI
from app.auth.db import Base, engine
from app.auth.routes import router as auth_router
from app.travel.routes import router as travel_router



app = FastAPI(title="JetsetGo API")

Base.metadata.create_all(bind=engine)

app.include_router(auth_router)
app.include_router(travel_router)

@app.get("/health")
def health():
    return {"status": "ok"}

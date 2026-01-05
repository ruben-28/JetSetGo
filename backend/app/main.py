from fastapi import FastAPI
from app.auth.db import Base, engine
from app.auth.routes import router as auth_router

app = FastAPI(title="JetsetGo API")

Base.metadata.create_all(bind=engine)

app.include_router(auth_router)

@app.get("/health")
def health():
    return {"status": "ok"}

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import Base, engine
from app.models import models
from app.api.routes import router
Base.metadata.create_all(bind=engine)
app=FastAPI(title="UniVerse AI API",version="1.0.0",description="Multi-agent academic workflow platform")
app.add_middleware(CORSMiddleware,allow_origins=settings.cors_origins,allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
app.include_router(router)
@app.get('/health')
def health(): return {"status":"ok","service":"universe-ai-api","mode":"deterministic-demo" if settings.demo_mode else "configured"}

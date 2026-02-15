from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.chat_stream import router as chat_stream_router
from app.api.session import router as sessions_router



from app.config import settings
from app.db.database import Base, engine
from app.api.chat import router as chat_router

def create_app() -> FastAPI:
    app = FastAPI(title="Live AI Assistant API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(chat_router)
    app.include_router(chat_stream_router)
    app.include_router(sessions_router)



    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app

app = create_app()

# Create tables on startup (simple MVP)
Base.metadata.create_all(bind=engine)

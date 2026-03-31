from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.services.seed import seed_demo_content

# Import SQLAlchemy models before create_all so metadata is populated.
from app import models  # noqa: F401


app = FastAPI(title=settings.project_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_demo_content(db)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Ai Assistant Web API is running."}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(api_router, prefix=settings.api_prefix)


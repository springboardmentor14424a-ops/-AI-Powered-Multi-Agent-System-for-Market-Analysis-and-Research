import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from app.database import Base, engine
from app.models import user as models_user  # noqa: F401
from app.api import auth, workspace, research

load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI(title="R-AIstock API", version="1.0.0")

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "dev-secret-change-in-production"),
    same_site="lax",
    
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(workspace.router)
app.include_router(research.router)

@app.get("/")
def root():
    return {"status": "ok", "platform": "R-AIstock"}
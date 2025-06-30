from fastapi import FastAPI
from app.routes import logs
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = ["http://localhost:4173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(logs.router)

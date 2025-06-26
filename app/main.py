from fastapi import FastAPI
from app.routes import logs

app = FastAPI()

app.include_router(logs.router)

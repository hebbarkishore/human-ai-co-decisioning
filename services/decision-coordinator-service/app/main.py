from fastapi import FastAPI
from routes import router

app = FastAPI(
    title="Decision Coordinator Service",
    version="1.0"
)

app.include_router(router)
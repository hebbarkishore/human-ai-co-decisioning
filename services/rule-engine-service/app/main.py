from fastapi import FastAPI
from routes import router

app = FastAPI(
    title="Rule Engine Service",
    version="1.0"
)

app.include_router(router)
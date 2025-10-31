from fastapi import FastAPI
from routes import router

app = FastAPI(
    title="Underwriter Helper Service",
    version="1.0"
)

app.include_router(router)
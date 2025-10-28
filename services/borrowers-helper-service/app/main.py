from fastapi import FastAPI
from routes import router

app = FastAPI(
    title="Borrowers Helper Service",
    version="1.0"
)

app.include_router(router)
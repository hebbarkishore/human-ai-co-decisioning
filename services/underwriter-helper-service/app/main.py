from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import router

app = FastAPI(
    title="Underwriter Helper Service",
    version="1.0"
)


origins = [
    "http://localhost:3000",   # React App
    "http://localhost",        # optional
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,        # allow React
    allow_credentials=True,
    allow_methods=["*"],          # GET, POST, etc.
    allow_headers=["*"],          # all headers including Authorization
)

app.include_router(router)
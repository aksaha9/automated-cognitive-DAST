from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import endpoints

app = FastAPI(
    title="Automated Cognitive DAST API",
    description="API for managing DAST scans using OWASP ZAP",
    version="1.0.0"
)

# Configure CORS
origins = [
    "http://localhost:5173",  # Local React Frontend
    "http://localhost:3000",
    "*" # For MVP, allow all
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(endpoints.router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Automated Cognitive DAST API is running"}

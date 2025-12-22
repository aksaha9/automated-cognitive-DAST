from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
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

# Mount assets directory (Vite puts assets here)
# We check if directory exists to avoid errors during local dev if dist isn't generated
if os.path.exists("/app/static/assets"):
    app.mount("/assets", StaticFiles(directory="/app/static/assets"), name="assets")

# SPA Catch-All Handler
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    # Allow API routes to pass through (just in case)
    if full_path.startswith("api/"):
         return {"error": "API route not found"}

    # specific file check in static (e.g. favicon.ico)
    static_file_path = os.path.join("/app/static", full_path)
    if os.path.isfile(static_file_path):
        return FileResponse(static_file_path)
    
    # Fallback to index.html
    index_path = "/app/static/index.html"
    if os.path.exists(index_path):
        return FileResponse(index_path)
        
    return {"message": "Frontend not found. Please ensure the container was built with frontend artifacts."}

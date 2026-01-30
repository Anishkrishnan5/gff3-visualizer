from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.routes import router

app = FastAPI(title="GFF3 Visualizer", version="1.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api", tags=["api"])

# Serve static files (frontend) if needed
# app.mount("/", StaticFiles(directory="../frontend", html=True), name="static")

@app.get("/")
def root():
    return {"message": "GFF3 Visualizer API", "version": "1.0.0"}


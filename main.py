from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Import routes
from backend.routes import auth, reports

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Stock Market Analysis Platform",
    description="API for stock market data analysis and user management",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(reports.router, prefix="/reports", tags=["Reports"])

# Health check endpoint

@app.get("/")
async def root():
    return {"status": "healthy", "message": "Stock Market Analysis Platform API"}
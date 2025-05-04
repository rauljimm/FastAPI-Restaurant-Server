"""
Run script for the FastAPI Restaurant Management System
"""
import uvicorn
from app.core.config import SQLALCHEMY_DATABASE_URL, create_tables
from app.db.database import engine

if __name__ == "__main__":
    # Create tables before starting the app
    create_tables()
    
    # Run the FastAPI application
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 
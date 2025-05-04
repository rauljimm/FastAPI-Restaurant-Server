"""
Main entry point for the application.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys

from app.core.config import (
    PROJECT_NAME, DESCRIPTION, VERSION, 
    ALLOWED_ORIGINS, ALLOWED_METHODS, ALLOWED_HEADERS
)
from app.db.database import engine, Base

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)
logger.debug("Iniciando aplicación")

# Import all models to ensure they are registered for table creation
from app.models import *

# Create FastAPI application
app = FastAPI(
    title=PROJECT_NAME,
    description=DESCRIPTION,
    version=VERSION
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=ALLOWED_METHODS,
    allow_headers=ALLOWED_HEADERS,
)

# Create database tables
Base.metadata.create_all(bind=engine)
logger.debug("Tablas de base de datos creadas")

# Import and include routers
from app.api.endpoints import (
    usuarios, categorias, productos, mesas, pedidos, reservas, auth, websockets
)

app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(categorias.router)
app.include_router(productos.router)
app.include_router(mesas.router)
app.include_router(pedidos.router)
app.include_router(reservas.router)
app.include_router(websockets.router)
logger.debug("Routers configurados")

@app.get("/")
def root():
    """Health check endpoint"""
    return {"message": "API de Gestión de Restaurante"} 
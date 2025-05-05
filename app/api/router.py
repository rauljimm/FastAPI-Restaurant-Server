"""
Router principal de la API.
"""
from fastapi import APIRouter
from app.api.endpoints import auth, usuarios, categorias, productos, mesas, pedidos, reservas, cuentas, websockets

api_router = APIRouter()

# Incluir los routers de cada endpoint
api_router.include_router(auth.router)
api_router.include_router(usuarios.router)
api_router.include_router(categorias.router)
api_router.include_router(productos.router)
api_router.include_router(mesas.router)
api_router.include_router(pedidos.router)
api_router.include_router(reservas.router)
api_router.include_router(cuentas.router)
api_router.include_router(websockets.router) 
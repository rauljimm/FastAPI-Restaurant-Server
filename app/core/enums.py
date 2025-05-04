"""
Enumerations used throughout the application.
"""
from enum import Enum

class RolUsuario(str, Enum):
    """Roles de usuario en el sistema"""
    ADMIN = "admin"
    CAMARERO = "camarero"
    COCINERO = "cocinero"

class EstadoPedido(str, Enum):
    """Estados posibles de un pedido"""
    RECIBIDO = "recibido"
    EN_PREPARACION = "en_preparacion"
    LISTO = "listo"
    ENTREGADO = "entregado"
    CANCELADO = "cancelado"

class EstadoReserva(str, Enum):
    """Estados posibles de una reserva"""
    PENDIENTE = "pendiente"
    CONFIRMADA = "confirmada"
    CANCELADA = "cancelada"
    COMPLETADA = "completada"

class EstadoMesa(str, Enum):
    """Estados posibles de una mesa"""
    LIBRE = "libre"
    OCUPADA = "ocupada"
    RESERVADA = "reservada"
    MANTENIMIENTO = "mantenimiento"

class TipoProducto(str, Enum):
    """Tipos de productos disponibles"""
    COMIDA = "comida"
    BEBIDA = "bebida"
    POSTRE = "postre"
    ENTRADA = "entrada"
    COMPLEMENTO = "complemento" 
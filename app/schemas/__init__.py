"""
Esquemas Pydantic para peticiones y respuestas de la API.
"""
from app.schemas.usuario import (
    UsuarioCreate, UsuarioUpdate, UsuarioResponse, 
    Token, TokenData
)
from app.schemas.categoria import (
    CategoriaCreate, CategoriaUpdate, CategoriaResponse
)
from app.schemas.producto import (
    ProductoCreate, ProductoUpdate, ProductoResponse, ProductoDetallado
)
from app.schemas.mesa import (
    MesaCreate, MesaUpdate, MesaResponse
)
from app.schemas.pedido import (
    DetallePedidoCreate, DetallePedidoUpdate, DetallePedidoResponse, DetallePedidoDetallado,
    PedidoCreate, PedidoUpdate, PedidoResponse, PedidoDetallado
)
from app.schemas.reserva import (
    ReservaCreate, ReservaUpdate, ReservaResponse, ReservaDetallada
) 
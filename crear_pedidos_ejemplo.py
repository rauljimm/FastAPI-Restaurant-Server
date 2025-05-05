from app.db.database import create_tables, get_engine
from app.models.mesa import Mesa
from app.models.producto import Producto
from app.models.usuario import Usuario
from app.models.pedido import Pedido, DetallePedido
from app.core.enums import EstadoMesa, EstadoPedido
from sqlalchemy.orm import sessionmaker
import datetime

def crear_pedidos_ejemplo():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Verificar el estado de la mesa
        mesa = session.query(Mesa).filter(Mesa.id == 1).first()
        if not mesa:
            print("La mesa con id=1 no existe")
            return
        
        print(f"Estado de la mesa: {mesa.estado}")
        
        # Obtener productos disponibles
        productos = session.query(Producto).filter(Producto.disponible == True).limit(3).all()
        if not productos:
            print("No hay productos disponibles")
            return
        
        print(f"Productos disponibles: {[p.nombre for p in productos]}")
        
        # Obtener camarero
        camarero = session.query(Usuario).filter(Usuario.username == 'camarero').first()
        if not camarero:
            print("No se encontró el usuario 'camarero'")
            return
        
        print(f"Camarero ID: {camarero.id}")
        
        # Crear un pedido de ejemplo si no existe ninguno
        existing_pedidos = session.query(Pedido).filter(Pedido.mesa_id == 1).all()
        if not existing_pedidos:
            nuevo_pedido = Pedido(
                mesa_id=1,
                camarero_id=camarero.id,
                estado=EstadoPedido.ENTREGADO,
                total=0,
                fecha_creacion=datetime.datetime.now()
            )
            session.add(nuevo_pedido)
            session.commit()
            print(f"Nuevo pedido creado, ID: {nuevo_pedido.id}")
            
            # Agregar detalles al pedido
            total = 0
            for producto in productos:
                detalle = DetallePedido(
                    pedido_id=nuevo_pedido.id,
                    producto_id=producto.id,
                    cantidad=1,
                    precio_unitario=producto.precio,
                    subtotal=producto.precio,
                    estado=EstadoPedido.ENTREGADO
                )
                session.add(detalle)
                total += producto.precio
            
            session.commit()
            
            # Actualizar el total del pedido
            nuevo_pedido.total = total
            session.commit()
            print(f"Detalles agregados, total: {total}")
        else:
            print(f"Ya existen {len(existing_pedidos)} pedidos para esta mesa")
            for p in existing_pedidos:
                print(f"  Pedido #{p.id}, estado: {p.estado}, total: {p.total}")
        
        # Marcar la mesa como ocupada
        mesa.estado = EstadoMesa.OCUPADA
        session.commit()
        print("Mesa marcada como ocupada")
        
        # Mostrar todos los pedidos existentes
        pedidos = session.query(Pedido).filter(Pedido.mesa_id == 1).all()
        print(f"Pedidos existentes: {[(p.id, p.estado, p.total) for p in pedidos]}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    crear_pedidos_ejemplo() 
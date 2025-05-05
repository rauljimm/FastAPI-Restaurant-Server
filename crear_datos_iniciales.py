import sys
import os
import json

# Asegurarse de que el directorio actual está en el path
sys.path.append(os.path.abspath('.'))

from app.db.database import Base, engine, get_db
from app.models.mesa import Mesa
from app.models.producto import Producto
from app.models.categoria import Categoria
from app.models.usuario import Usuario
from app.models.pedido import Pedido, DetallePedido
from app.models.cuenta import Cuenta
from app.core.enums import EstadoMesa, EstadoPedido, RolUsuario
from sqlalchemy.orm import Session
import datetime

def crear_datos_iniciales():
    print("Creando datos iniciales para el restaurante...")
    db = next(get_db())
    
    try:
        # 1. Crear categorías si no existen
        categorias = [
            {"nombre": "Entrantes", "descripcion": "Platos para compartir"},
            {"nombre": "Principales", "descripcion": "Platos principales"},
            {"nombre": "Postres", "descripcion": "Platos dulces para terminar"},
            {"nombre": "Bebidas", "descripcion": "Bebidas frías y calientes"}
        ]
        
        categorias_creadas = []
        for cat_data in categorias:
            if not db.query(Categoria).filter(Categoria.nombre == cat_data["nombre"]).first():
                cat = Categoria(**cat_data)
                db.add(cat)
                db.commit()
                db.refresh(cat)
                categorias_creadas.append(cat)
                print(f"Categoría creada: {cat.nombre} (ID: {cat.id})")
            else:
                cat = db.query(Categoria).filter(Categoria.nombre == cat_data["nombre"]).first()
                categorias_creadas.append(cat)
                print(f"Categoría ya existe: {cat.nombre} (ID: {cat.id})")
        
        # 2. Crear productos si no existen
        productos = [
            {"nombre": "Patatas Bravas", "descripcion": "Patatas fritas con salsa picante", "precio": 6.50, "categoria_id": categorias_creadas[0].id, "tipo": "comida", "disponible": True},
            {"nombre": "Calamares a la Romana", "descripcion": "Calamares fritos con rebozado", "precio": 9.90, "categoria_id": categorias_creadas[0].id, "tipo": "comida", "disponible": True},
            {"nombre": "Croquetas de Jamón", "descripcion": "Croquetas caseras de jamón ibérico", "precio": 8.50, "categoria_id": categorias_creadas[0].id, "tipo": "comida", "disponible": True},
            
            {"nombre": "Solomillo a la Pimienta", "descripcion": "Solomillo con salsa de pimienta y guarnición", "precio": 16.50, "categoria_id": categorias_creadas[1].id, "tipo": "comida", "disponible": True},
            {"nombre": "Paella Mixta", "descripcion": "Paella con mariscos y carne", "precio": 14.00, "categoria_id": categorias_creadas[1].id, "tipo": "comida", "disponible": True},
            {"nombre": "Lasaña Casera", "descripcion": "Lasaña de carne con bechamel", "precio": 12.75, "categoria_id": categorias_creadas[1].id, "tipo": "comida", "disponible": True},
            
            {"nombre": "Tarta de Queso", "descripcion": "Tarta de queso con coulis de frutos rojos", "precio": 5.90, "categoria_id": categorias_creadas[2].id, "tipo": "comida", "disponible": True},
            {"nombre": "Tiramisú", "descripcion": "Postre italiano con mascarpone y café", "precio": 6.20, "categoria_id": categorias_creadas[2].id, "tipo": "comida", "disponible": True},
            
            {"nombre": "Refresco", "descripcion": "Varias opciones disponibles", "precio": 2.50, "categoria_id": categorias_creadas[3].id, "tipo": "bebida", "disponible": True},
            {"nombre": "Cerveza", "descripcion": "Caña de cerveza", "precio": 2.80, "categoria_id": categorias_creadas[3].id, "tipo": "bebida", "disponible": True},
            {"nombre": "Vino de la Casa", "descripcion": "Copa de vino tinto, blanco o rosado", "precio": 3.50, "categoria_id": categorias_creadas[3].id, "tipo": "bebida", "disponible": True}
        ]
        
        productos_creados = []
        for prod_data in productos:
            if not db.query(Producto).filter(Producto.nombre == prod_data["nombre"]).first():
                prod = Producto(**prod_data)
                db.add(prod)
                db.commit()
                db.refresh(prod)
                productos_creados.append(prod)
                print(f"Producto creado: {prod.nombre} (ID: {prod.id})")
            else:
                prod = db.query(Producto).filter(Producto.nombre == prod_data["nombre"]).first()
                productos_creados.append(prod)
                print(f"Producto ya existe: {prod.nombre} (ID: {prod.id})")
        
        # 3. Limpiar cualquier mesa ocupada existente
        mesas_ocupadas = db.query(Mesa).filter(Mesa.estado == EstadoMesa.OCUPADA).all()
        for mesa in mesas_ocupadas:
            # Eliminar pedidos anteriores vinculados a esta mesa
            pedidos_anteriores = db.query(Pedido).filter(Pedido.mesa_id == mesa.id).all()
            for pedido in pedidos_anteriores:
                pedido.mesa_id = None
                pedido.estado = EstadoPedido.ENTREGADO
            
            db.commit()
            print(f"Mesa {mesa.numero} (ID: {mesa.id}): pedidos antiguos desvinculados")
        
        # 4. Crear o actualizar mesas
        mesas = [
            {"numero": 1, "capacidad": 4, "ubicacion": "Terraza", "estado": EstadoMesa.OCUPADA},
            {"numero": 2, "capacidad": 2, "ubicacion": "Terraza", "estado": EstadoMesa.LIBRE},
            {"numero": 3, "capacidad": 6, "ubicacion": "Interior", "estado": EstadoMesa.LIBRE},
            {"numero": 4, "capacidad": 4, "ubicacion": "Interior", "estado": EstadoMesa.LIBRE},
            {"numero": 5, "capacidad": 2, "ubicacion": "Barra", "estado": EstadoMesa.LIBRE}
        ]
        
        mesas_creadas = []
        for mesa_data in mesas:
            mesa_existente = db.query(Mesa).filter(Mesa.numero == mesa_data["numero"]).first()
            if not mesa_existente:
                mesa = Mesa(**mesa_data)
                db.add(mesa)
                db.commit()
                db.refresh(mesa)
                mesas_creadas.append(mesa)
                print(f"Mesa creada: Mesa {mesa.numero} (ID: {mesa.id})")
            else:
                # Actualizar el estado de la mesa existente
                mesa_existente.estado = mesa_data["estado"]
                db.commit()
                db.refresh(mesa_existente)
                mesas_creadas.append(mesa_existente)
                print(f"Mesa actualizada: Mesa {mesa_existente.numero} (ID: {mesa_existente.id})")
        
        # 5. Asegurarse de que existe el usuario camarero
        camarero = db.query(Usuario).filter(Usuario.username == "camarero").first()
        if not camarero:
            print("ADVERTENCIA: No se encontró el usuario 'camarero'. Asegúrate de que existe para crear pedidos.")
            return
        
        print(f"Usuario camarero encontrado: ID {camarero.id}")
        
        # 6. Crear pedidos para la mesa 1 (que está ocupada)
        mesa_ocupada = db.query(Mesa).filter(Mesa.estado == EstadoMesa.OCUPADA).first()
        if mesa_ocupada:
            # 6.1 Crear un pedido para primeros platos y bebidas (ENTREGADO)
            pedido1 = Pedido(
                mesa_id=mesa_ocupada.id,
                camarero_id=camarero.id,
                estado=EstadoPedido.ENTREGADO,
                total=0,  # Se actualizará después
                fecha_creacion=datetime.datetime.now() - datetime.timedelta(minutes=45)
            )
            db.add(pedido1)
            db.commit()
            db.refresh(pedido1)
            print(f"Pedido 1 (primeros y bebidas) creado: ID {pedido1.id}")
            
            # Añadir detalles al pedido 1
            detalles_pedido1 = [
                {"producto": productos_creados[0], "cantidad": 1},  # Patatas Bravas
                {"producto": productos_creados[2], "cantidad": 1},  # Croquetas
                {"producto": productos_creados[9], "cantidad": 2},  # Cerveza
                {"producto": productos_creados[8], "cantidad": 1}   # Refresco
            ]
            
            total_pedido1 = 0
            for detalle_data in detalles_pedido1:
                producto = detalle_data["producto"]
                cantidad = detalle_data["cantidad"]
                subtotal = producto.precio * cantidad
                
                detalle = DetallePedido(
                    pedido_id=pedido1.id,
                    producto_id=producto.id,
                    cantidad=cantidad,
                    precio_unitario=producto.precio,
                    subtotal=subtotal,
                    estado=EstadoPedido.ENTREGADO
                )
                db.add(detalle)
                total_pedido1 += subtotal
            
            pedido1.total = total_pedido1
            db.commit()
            print(f"Detalles agregados al pedido 1, total: {total_pedido1}€")
            
            # 6.2 Crear un pedido para platos principales (EN PROCESO)
            pedido2 = Pedido(
                mesa_id=mesa_ocupada.id,
                camarero_id=camarero.id,
                estado=EstadoPedido.RECIBIDO,
                total=0,  # Se actualizará después
                fecha_creacion=datetime.datetime.now() - datetime.timedelta(minutes=15)
            )
            db.add(pedido2)
            db.commit()
            db.refresh(pedido2)
            print(f"Pedido 2 (principales) creado: ID {pedido2.id}")
            
            # Añadir detalles al pedido 2
            detalles_pedido2 = [
                {"producto": productos_creados[3], "cantidad": 1},  # Solomillo
                {"producto": productos_creados[5], "cantidad": 1}   # Lasaña
            ]
            
            total_pedido2 = 0
            for detalle_data in detalles_pedido2:
                producto = detalle_data["producto"]
                cantidad = detalle_data["cantidad"]
                subtotal = producto.precio * cantidad
                
                detalle = DetallePedido(
                    pedido_id=pedido2.id,
                    producto_id=producto.id,
                    cantidad=cantidad,
                    precio_unitario=producto.precio,
                    subtotal=subtotal,
                    estado=EstadoPedido.RECIBIDO
                )
                db.add(detalle)
                total_pedido2 += subtotal
            
            pedido2.total = total_pedido2
            db.commit()
            print(f"Detalles agregados al pedido 2, total: {total_pedido2}€")
            
            print(f"Mesa {mesa_ocupada.numero} preparada con pedidos actuales")
        
        # 7. Crear un ejemplo de cuenta histórica
        if not db.query(Cuenta).count():
            # Crear una cuenta histórica
            detalles_cuenta = [
                {
                    "pedido_id": 1,
                    "producto_id": productos_creados[0].id,
                    "nombre_producto": productos_creados[0].nombre,
                    "cantidad": 2,
                    "precio_unitario": productos_creados[0].precio,
                    "subtotal": productos_creados[0].precio * 2
                },
                {
                    "pedido_id": 1,
                    "producto_id": productos_creados[4].id,
                    "nombre_producto": productos_creados[4].nombre,
                    "cantidad": 1,
                    "precio_unitario": productos_creados[4].precio,
                    "subtotal": productos_creados[4].precio
                },
                {
                    "pedido_id": 1,
                    "producto_id": productos_creados[9].id,
                    "nombre_producto": productos_creados[9].nombre,
                    "cantidad": 3,
                    "precio_unitario": productos_creados[9].precio,
                    "subtotal": productos_creados[9].precio * 3
                }
            ]
            
            total_cuenta = sum(item["subtotal"] for item in detalles_cuenta)
            
            cuenta_historica = Cuenta(
                mesa_id=mesas_creadas[1].id,  # Mesa 2
                numero_mesa=mesas_creadas[1].numero,
                camarero_id=camarero.id,
                nombre_camarero=f"{camarero.nombre} {camarero.apellido}",
                fecha_cobro=datetime.datetime.now() - datetime.timedelta(days=1),  # Ayer
                total=total_cuenta,
                metodo_pago="efectivo",
                detalles=json.dumps(detalles_cuenta)
            )
            
            db.add(cuenta_historica)
            db.commit()
            db.refresh(cuenta_historica)
            print(f"Cuenta histórica creada: ID {cuenta_historica.id}, total: {total_cuenta}€")
        
        print("\nDatos iniciales creados con éxito.")
        
    except Exception as e:
        print(f"Error al crear datos iniciales: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    crear_datos_iniciales() 
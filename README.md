# 🍽️ Sistema de Gestión de Restaurante con FastAPI

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.95.0+-green.svg)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-red.svg)](https://www.sqlalchemy.org/)

## 📋 Descripción

Un completo sistema de gestión para restaurantes desarrollado con FastAPI que permite administrar mesas, reservas, pedidos, productos, categorías y usuarios con diferentes roles y permisos. Incluye una integración completa con la aplicación Android FrontRestaurante.

## ✨ Características

- 🔐 **Sistema de autenticación**: Basado en JWT con diferentes roles (Admin, Camarero, Cocinero)
- 👥 **Gestión de usuarios**: Administración completa de usuarios con diferentes niveles de permisos
- 🍔 **Gestión de productos**: Organización de productos por categorías, precios y disponibilidad
- 🏷️ **Categorías**: Organización de productos en categorías personalizables
- 🪑 **Gestión de mesas**: Control de mesas, capacidad y estado (libre, ocupada, reservada, mantenimiento)
- 📝 **Pedidos**: Sistema completo de pedidos con estados (recibido, en preparación, listo, entregado, cancelado)
- 📅 **Reservas**: Sistema de reservas con confirmación y gestión de disponibilidad
- 🔄 **WebSockets**: Notificaciones en tiempo real para pedidos y cocina
- 📱 **Integración con Android**: Backend completo para la app FrontRestaurante

## 🔑 Roles y Permisos

### 👨‍💼 Administrador
- Acceso completo a todas las funcionalidades del sistema
- Gestión de usuarios, productos, categorías, mesas y reservas
- Visualización de informes y estadísticas
- Cambio de estado de cualquier pedido, mesa o reserva
- Creación de nuevos productos y mesas

### 🧑‍🍳 Camarero
- Gestión de mesas (ver estado, cambiar a libre/ocupada/reservada)
- Creación y gestión de pedidos
- Marcado de pedidos como entregados
- Visualización de pedidos propios
- Creación de reservas
- Eliminación de reservas completadas o canceladas
- Cierre de servicio de mesa (cobro)
- Acceso a categorías y productos para visualización

### 👨‍🍳 Cocinero
- Visualización de pedidos pendientes
- Actualización del estado de los pedidos (en preparación, listo)
- Visualización de información de productos

## 🚀 Endpoints

### 🔐 Autenticación
- `POST /token`: Obtener token de acceso
- `POST /login`: Iniciar sesión (JSON)

### 👥 Usuarios
- `GET /usuarios/`: Listar usuarios (admin)
- `POST /usuarios/`: Crear usuario (admin)
- `GET /usuarios/me`: Obtener perfil del usuario actual
- `GET /usuarios/{id}`: Obtener usuario por ID
- `PUT /usuarios/{id}`: Actualizar usuario
- `DELETE /usuarios/{id}`: Eliminar usuario (admin)

### 🏷️ Categorías
- `GET /categorias/`: Listar categorías
- `POST /categorias/`: Crear categoría (admin)
- `GET /categorias/{id}`: Obtener categoría por ID
- `PUT /categorias/{id}`: Actualizar categoría (admin)
- `DELETE /categorias/{id}`: Eliminar categoría (admin)

### 🍔 Productos
- `GET /productos/`: Listar productos (filtrable por categoría, tipo y disponibilidad)
- `POST /productos/`: Crear producto (admin)
- `GET /productos/{id}`: Obtener producto por ID
- `PUT /productos/{id}`: Actualizar producto (admin)
- `DELETE /productos/{id}`: Eliminar producto (admin)

### 🪑 Mesas
- `GET /mesas/`: Listar mesas (filtrable por estado)
- `POST /mesas/`: Crear mesa (admin)
- `GET /mesas/{id}`: Obtener mesa por ID
- `GET /mesas/{id}/reserva-activa`: Obtener reserva activa de una mesa (camarero/admin)
- `PUT /mesas/{id}`: Actualizar mesa (admin/camarero)
- `DELETE /mesas/{id}`: Eliminar mesa (admin)

### 📝 Pedidos
- `GET /pedidos/`: Listar pedidos (filtrable por estado, fecha, mesa y camarero)
- `POST /pedidos/`: Crear pedido (camarero/admin)
- `GET /pedidos/{id}`: Obtener pedido por ID
- `PUT /pedidos/{id}`: Actualizar pedido
- `POST /pedidos/{id}/detalles/`: Añadir producto a pedido
- `PUT /pedidos/{id}/detalles/{detalle_id}`: Actualizar detalle de pedido
- `DELETE /pedidos/{id}/detalles/{detalle_id}`: Eliminar producto de pedido

### 📅 Reservas
- `GET /reservas/`: Listar reservas (filtrable por estado, fecha y mesa)
- `POST /reservas/`: Crear reserva
- `GET /reservas/{id}`: Obtener reserva por ID
- `PUT /reservas/{id}`: Actualizar reserva
- `DELETE /reservas/{id}`: Eliminar reserva (admin/camarero)

## 🛠️ Tecnologías

- **FastAPI**: Framework web rápido para crear APIs con Python
- **SQLAlchemy**: ORM (Object Relational Mapper) para la gestión de la base de datos
- **Pydantic**: Validación de datos y serialización
- **JWT**: Autenticación basada en tokens
- **Pytest**: Framework de pruebas automatizadas
- **WebSockets**: Comunicación en tiempo real

## ⚙️ Instalación

1. Clonar el repositorio:
   ```bash
   git clone https://github.com/rauljimm/restaurante-fastapi.git
   cd restaurante-fastapi
   ```

2. Crear y activar entorno virtual:
   ```bash
   python -m venv venv
   # En Windows:
   venv\Scripts\activate
   # En macOS/Linux:
   source venv/bin/activate
   ```

3. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

4. Configurar variables de entorno (crear archivo `.env` basado en `.env.example`)

5. Ejecutar la aplicación:
   ```bash
   python run.py
   ```

6. Acceder a la documentación: http://localhost:8000/docs

## 🧪 Pruebas

El proyecto incluye una amplia suite de pruebas automatizadas que cubren todos los endpoints y funcionalidades.

Para ejecutar las pruebas:

```bash
python -m pytest app/tests/
```

Para ejecutar pruebas específicas:

```bash
python -m pytest app/tests/test_reservas.py -v
```

## 📊 Estructura del Proyecto

```
app/
├── api/
│   ├── dependencies/   # Dependencias para los endpoints
│   └── endpoints/      # Definición de endpoints
├── core/               # Configuración central, seguridad, etc.
├── db/                 # Configuración de la base de datos
├── models/             # Modelos SQLAlchemy
├── schemas/            # Esquemas Pydantic
├── services/           # Lógica de negocio
└── tests/              # Pruebas automatizadas
```

## 🔄 Flujo de trabajo para camareros y cocineros

### 🧑‍🍳 **Camarero**:
1. Iniciar sesión en el sistema
2. Consultar mesas disponibles
3. Asignar una mesa a un cliente (cambiar estado a "ocupada")
4. Tomar el pedido del cliente
5. Registrar el pedido en el sistema
6. Recibir notificación cuando el pedido está listo
7. Entregar el pedido al cliente
8. Marcar pedido como entregado
9. Al finalizar el servicio, generar la cuenta
10. Cerrar la mesa (cambiar estado a "libre")
11. Gestionar reservas (crear, consultar, eliminar)

### 👨‍🍳 **Cocinero**:
1. Iniciar sesión en el sistema
2. Ver lista de pedidos pendientes
3. Seleccionar un pedido para preparar
4. Marcar pedido como "en preparación"
5. Al completar la preparación, marcar pedido como "listo"
6. El sistema notifica automáticamente al camarero

## 📱 Aplicación Android

Este backend está diseñado para funcionar con la aplicación Android FrontRestaurante, que proporciona una interfaz de usuario completa para camareros, cocineros y administradores.

La integración incluye:
- Autenticación mediante JWT
- Sincronización de datos en tiempo real
- Gestión completa de mesas, pedidos y reservas
- Permisos específicos por rol

Consulta el [README de FrontRestaurante](./FrontRestaurante/README.md) para más información sobre la aplicación Android.

## 📧 Contacto

rauljimm.dev@gmail.com
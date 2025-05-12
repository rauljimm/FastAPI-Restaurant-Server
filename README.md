# 🍽️ Sistema de Gestión de Restaurante - Backend FastAPI

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.95.0+-green.svg)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-red.svg)](https://www.sqlalchemy.org/)

## 📋 Descripción

Backend completo para un sistema de gestión de restaurantes desarrollado con FastAPI que permite administrar mesas, reservas, pedidos, productos, categorías y usuarios con diferentes roles y permisos. Diseñado para funcionar con la aplicación Android FrontRestaurante ubicada en el directorio `/FrontEnd-Restaurant-App-main`.

## ✨ Características

- 🔐 **Sistema de autenticación**: Basado en JWT con diferentes roles (Admin, Camarero, Cocinero)
- 👥 **Gestión de usuarios**: Administración completa de usuarios con diferentes niveles de permisos
- 🍔 **Gestión de productos**: Organización de productos por categorías, precios y disponibilidad
- 🏷️ **Categorías**: Organización de productos en categorías personalizables
- 🪑 **Gestión de mesas**: Control de mesas, capacidad y estado (libre, ocupada, reservada, mantenimiento)
- 📝 **Pedidos**: Sistema completo de pedidos con estados (recibido, en preparación, listo, entregado, cancelado)
- 📅 **Reservas**: Sistema de reservas con confirmación y gestión automática de llegadas
- 🔄 **WebSockets**: Notificaciones en tiempo real para pedidos y cocina con autenticación segura
- 💰 **Cuentas**: Gestión de cuentas y pagos
- 🛡️ **Seguridad mejorada**: Endpoints protegidos con autenticación y verificación de permisos
- 🧰 **Manejo de errores**: Sistema robusto para prevenir errores 500 y manejar casos extremos
- 📊 **Persistencia de datos**: Manejo inteligente de referencias para mantener históricos incluso cuando productos se eliminan

## 🔑 Roles y Permisos

### 👨‍💼 Administrador
- Acceso completo a todas las funcionalidades del sistema
- Gestión de usuarios, productos, categorías, mesas y reservas
- Visualización de informes y estadísticas
- Cambio de estado de cualquier pedido, mesa o reserva
- Eliminación de mesas sin pedidos activos

### 🧑‍🍳 Camarero
- Gestión de mesas (ver estado, cambiar a libre/ocupada/reservada)
- Creación y gestión de pedidos
- Marcado de pedidos como entregados
- Visualización de pedidos propios
- Creación y gestión de reservas
- Cierre de servicio de mesa (cobro)
- Eliminación automática de reservas completadas o canceladas

### 👨‍🍳 Cocinero
- Visualización de pedidos pendientes
- Actualización del estado de los pedidos (en preparación, listo)
- Visualización de información de productos

## 🔐 Cuentas Predefinidas

El sistema viene con las siguientes cuentas predefinidas para pruebas:

| Usuario     | Contraseña     | Rol       |
|-------------|----------------|-----------|
| admin       | adminpassword  | admin     |
| camarero1   | camarero1pass  | camarero  |
| camarero2   | camarero2pass  | camarero  |
| cocinero1   | cocinero1pass  | cocinero  |

## 🚀 Endpoints

### 🔐 Autenticación
- `POST /token`: Obtener token de acceso (formulario)
- `POST /login`: Iniciar sesión (JSON)
- `GET /`: Health check de la API

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
- `DELETE /pedidos/{id}`: Eliminar pedido completo (camarero/admin)

### 📅 Reservas
- `GET /reservas/`: Listar reservas (filtrable por estado, fecha y mesa)
- `POST /reservas/`: Crear reserva
- `GET /reservas/{id}`: Obtener reserva por ID
- `PUT /reservas/{id}`: Actualizar reserva
- `DELETE /reservas/{id}`: Eliminar reserva (admin/camarero)

### 💰 Cuentas
- `GET /cuentas/`: Listar cuentas (filtrable por fecha y mesa)
- `GET /cuentas/{id}`: Obtener cuenta por ID
- `GET /cuentas/resumen`: Obtener resumen de cuentas
- `GET /cuentas/generar/mesa/{mesaId}`: Generar cuenta para una mesa
- `PUT /cuentas/{id}`: Actualizar cuenta
- `DELETE /cuentas/{id}`: Eliminar cuenta (admin)

### 🔄 WebSockets
- `WS /ws/cocina`: Conexión WebSocket para la cocina (cocineros y admin)
- `WS /ws/camareros`: Conexión WebSocket para camareros (camareros y admin)
- `WS /ws/admin`: Conexión WebSocket para administradores (solo admin)

## 🛠️ Tecnologías

- **FastAPI**: Framework web rápido para crear APIs con Python
- **SQLAlchemy**: ORM para la gestión de la base de datos
- **Pydantic**: Validación de datos y serialización
- **JWT**: Autenticación basada en tokens
- **WebSockets**: Comunicación en tiempo real con autenticación
- **SQLite**: Base de datos relacional (desarrollo)
- **Pytest**: Framework para pruebas automatizadas
- **Logging**: Sistema de registro de actividad y errores

## ⚙️ Instalación

1. Clonar el repositorio:
   ```bash
   git clone https://github.com/rauljimm/FastAPI-Restaurant-Server.git
   cd FastAPI-Restaurant-Server
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

4. Ejecutar la aplicación:
   ```bash
   python run.py
   ```

5. Acceder a la documentación: http://localhost:8000/docs

## 🧪 Pruebas

El proyecto incluye una suite de pruebas automatizadas que cubren los endpoints y funcionalidades:

```bash
python -m pytest app/tests/
```

Para ejecutar pruebas específicas:

```bash
python -m pytest app/tests/test_reservas.py -v
```

## 🔄 Mejoras Recientes

- ✅ **WebSockets autenticados**: Protección de conexiones WebSockets con verificación de token y rol
- ✅ **Endpoint GET de productos y categorías**: Permitir acceso sin autenticación para consultas públicas
- ✅ **Manejo mejorado de errores**: Prevención de errores 500 en detalles de mesa y pedidos
- ✅ **Eliminación segura de mesas**: Validación de que no tengan pedidos activos ni reservas futuras
- ✅ **Manejo inteligente de productos eliminados**: Conservación de referencias históricas en pedidos y cuentas
- ✅ **Validación de permisos por rol**: Restricción precisa de acceso según el rol del usuario
- ✅ **Manejo de deserialización robusta**: Esquemas resilientes que manejan productos eliminados o nulos

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

## 🔒 Seguridad

- **Autenticación JWT**: Token basado en roles con expiración configurable
- **Verificación de permisos**: Validación granular según el rol del usuario
- **WebSockets autenticados**: Conexiones WebSocket protegidas por token y validación de rol
- **Manejo de sesiones**: Expiración de tokens y renovación segura
- **Validación de datos**: Esquemas Pydantic para prevenir inyecciones y validar datos de entrada
- **Manejo de excepciones**: Respuestas HTTP apropiadas para cada tipo de error
- **Logging**: Registro detallado de actividad para auditoría y depuración

## 📧 Contacto

rauljimm.dev@gmail.com

# Restaurante App Showcase

Este proyecto es una página web de presentación para un sistema de gestión de restaurantes que utiliza [Anime.js](https://animejs.com/) para crear animaciones elegantes y atractivas. El sistema consta de un backend en FastAPI y un frontend en Android (Kotlin).

## 🚀 Demo

Para ver la página de demostración, simplemente abre el archivo `index.html` en tu navegador web.

## 📋 Características

- **Animaciones Fluidas**: Utiliza la potencia de Anime.js para crear transiciones y animaciones suaves
- **Diseño Responsivo**: Se adapta a diferentes tamaños de pantalla
- **Presentación Clara**: Muestra las características clave del sistema de gestión de restaurantes
- **Efectos 3D**: Incluye efectos de tarjetas 3D interactivas en la sección de características
- **Animaciones en Scroll**: Elementos que aparecen al hacer scroll

## 🛠️ Tecnologías Utilizadas

- **HTML5**: Estructura del contenido
- **CSS3**: Estilos y diseño responsive
- **JavaScript**: Lógica de animaciones y efectos
- **[Anime.js](https://animejs.com/)**: Biblioteca de animaciones JavaScript
- **Google Fonts**: Tipografía Poppins

## 📂 Estructura del Proyecto

```
/
├── index.html       # Archivo HTML principal
├── styles.css       # Estilos CSS
├── animations.js    # Código JavaScript para animaciones con Anime.js
└── README.md        # Este archivo
```

## 🔧 Instalación

1. Clona este repositorio:
   ```bash
   git clone https://github.com/tu-usuario/restaurante-app-showcase.git
   ```

2. Abre el archivo `index.html` en tu navegador.

## 🎨 Personalización

Para personalizar la página:

1. Modifica los colores en `styles.css` cambiando las variables CSS en la raíz:
   ```css
   :root {
       --primary: #FF5A5F;
       --secondary: #3D3D3D;
       /* otros colores... */
   }
   ```

2. Cambia las imágenes por las de tu propio proyecto en `index.html`.

3. Ajusta las animaciones en `animations.js` según tus preferencias:
   ```javascript
   anime({
       targets: '.your-element',
       // propiedades de animación...
   });
   ```

## ✨ Animaciones Implementadas

El proyecto incluye varias animaciones sofisticadas:

- **Animación de Entrada**: La cabecera aparece con una animación secuencial
- **Elementos Flotantes**: Los iconos de comida flotan con un efecto elástico
- **Tarjetas 3D**: Las tarjetas de características tienen un efecto 3D al pasar el cursor
- **Aparición en Scroll**: Los elementos aparecen a medida que se hace scroll
- **Rotación**: Animación de rotación completa para algunos elementos
- **Animación en Ruta**: Elementos que siguen un camino SVG definido

## 🧩 Ampliando las Animaciones

Para añadir más animaciones:

1. Define nuevos elementos HTML con IDs o clases específicas
2. Añade un nuevo efecto en `animations.js`:
   ```javascript
   function miNuevaAnimacion() {
       anime({
           targets: '.mi-elemento',
           // propiedades...
       });
   }
   ```
3. Llama a tu función desde `initAllAnimations()` o conéctala a un evento

## 📚 Recursos Útiles

- [Documentación de Anime.js](https://animejs.com/documentation/)
- [Ejemplos de Anime.js](https://animejs.com/#examples)

## 📫 Contacto

Si tienes preguntas sobre este proyecto, puedes contactarme en rauljimm.dev@gmail.com.

---

Desarrollado para mostrar el proyecto FastAPI-Restaurante con animaciones modernas.
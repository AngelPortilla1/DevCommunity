# 🌐 DevCommunity API

> Una API REST de comunidad para desarrolladores — con autenticación segura, gestión de sesiones multi-dispositivo, posts con imágenes, comentarios, likes, sistema de seguidores y notificaciones en tiempo real.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat&logo=fastapi&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat&logo=sqlite&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7.0-DC382D?style=flat&logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat&logo=docker&logoColor=white)
![Version](https://img.shields.io/badge/version-0.2.0-blue?style=flat)

---

## 📋 Tabla de contenido

- [Sobre el proyecto](#-sobre-el-proyecto)
- [Stack tecnológico](#-stack-tecnológico)
- [Arquitectura](#-arquitectura)
- [Estructura del proyecto](#-estructura-del-proyecto)
- [Módulos y características](#-módulos-y-características)
- [Endpoints de la API](#-endpoints-de-la-api)
- [Requisitos previos](#-requisitos-previos)
- [Instalación y ejecución](#-instalación-y-ejecución)
- [Ejecución de pruebas](#-ejecución-de-pruebas)
- [Variables de entorno](#-variables-de-entorno)
- [Datos de prueba (Seed)](#-datos-de-prueba-seed)
- [Estado del proyecto](#-estado-del-proyecto)

---

## 🧠 Sobre el proyecto

**DevCommunity** es una plataforma backend tipo red social pensada para desarrolladores. Permite a los usuarios registrarse, publicar contenido con imágenes, interactuar mediante comentarios y likes, seguirse entre sí y recibir notificaciones de actividad en tiempo real.

El enfoque principal del proyecto es construir una **API segura, modular y escalable**, con un sistema de autenticación robusto (JWT + Redis), gestión de sesiones multi-dispositivo con telemetría, arquitectura en capas desacoplada y manejo estandarizado de excepciones de dominio.

---

## 🛠️ Stack tecnológico

| Capa | Tecnología |
|---|---|
| Framework Web | [FastAPI](https://fastapi.tiangolo.com/) |
| ORM | [SQLAlchemy](https://www.sqlalchemy.org/) |
| Base de datos | SQLite (dev) / compatible con PostgreSQL |
| Cache & Sesiones | Redis 7 |
| Autenticación | JWT (`python-jose`) + bcrypt + SHA-256 |
| Validación | Pydantic v2 |
| Testing | Pytest (`fastapi.testclient`) + Unittest Mocks |
| Servidor | Uvicorn |
| Contenerización | Docker Compose |

---

## 🏛️ Arquitectura

El proyecto sigue una arquitectura en capas limpia y separada por responsabilidades:

```
Request
  │
  ▼
Router (Controlador / Validación de entrada)
  │
  ▼
Service (Lógica de negocio & orquestación de eventos)
  │
  ▼
Repository (Capa de persistencia y consultas SQL)
  │
  ▼
Model / DB (SQLAlchemy + SQLite / PostgreSQL)
```

Las sesiones, métricas de dispositivos y tokens revocados se gestionan en una capa independiente con **Redis**, garantizando alto rendimiento sin sobrecargar la base de datos relacional.

### Flujo de autenticación

```
POST /auth/login (o /auth/token para Swagger)
      │
      ├── Genera Access Token (JWT, 60 min)
      ├── Genera Refresh Token (JWT + JTI en Redis, 7 días)
      └── Crea sesión en Redis (con IP, User-Agent, Device ID y telemetría)

POST /auth/refresh
      │
      ├── Valida Refresh Token
      ├── Revoca el JTI anterior (token rotation)
      └── Emite nuevos Access + Refresh Tokens

POST /auth/logout
      ├── Revoca Refresh Token (elimina JTI de Redis)
      └── Añade Access Token al blacklist en Redis
```

---

## 📁 Estructura del proyecto

```
DevCommunity/
├── app/
│   ├── main.py                  # Punto de entrada, middlewares (CORS), handlers y routers
│   ├── api/                     # Rutas de prueba / health check
│   ├── auth/                    # Lógica de autenticación (JWT, bcrypt, rutas)
│   │   ├── auth_handler.py      # Creación/verificación de tokens y revocación en Redis
│   │   ├── auth_routes.py       # Endpoints: register, login, token, refresh, logout, me, sessions
│   │   └── auth_utils.py        # Utilidades auxiliares de auth
│   ├── core/                    # Configuración central
│   │   ├── config.py            # Settings (SECRET_KEY, DB URL, Redis URL, etc.)
│   │   ├── dependencies.py      # Inyección de dependencias (oauth2_scheme, get_current_user, admin_only)
│   │   ├── redis.py             # Cliente Redis con manejo de excepciones
│   │   └── exceptions_handlers.py # Handler global para AppException
│   ├── db/                      # Configuración de base de datos
│   │   ├── base.py              # Base declarativa SQLAlchemy
│   │   └── session.py           # Engine, SessionLocal, get_db
│   ├── models/                  # Modelos ORM (SQLAlchemy)
│   │   ├── user.py
│   │   ├── post.py              # Post con soporte de image_url y contadores
│   │   ├── comment.py
│   │   ├── like.py
│   │   ├── follows.py
│   │   ├── notification.py      # Modelo de notificaciones (like, comment, follow)
│   │   └── session.py           # Modelo SessionOut (output Redis)
│   ├── schemas/                 # Schemas Pydantic v2 (request/response)
│   │   ├── user_schema.py
│   │   ├── post_schema.py
│   │   ├── comment_schema.py
│   │   ├── notification_schema.py # Schemas de notificaciones paginadas y unread count
│   │   └── session_schema.py
│   ├── repositories/            # Capa de acceso a datos (queries SQL)
│   │   ├── post_repository.py
│   │   ├── comment_repository.py
│   │   ├── like_repository.py
│   │   ├── follower_repository.py
│   │   └── notification_repository.py
│   ├── services/                # Lógica de negocio y eventos
│   │   ├── post_service.py
│   │   ├── comment_service.py
│   │   ├── like_service.py
│   │   ├── follower_service.py
│   │   ├── notification_service.py # Creación y consulta de notificaciones
│   │   └── session_service.py   # Gestión de sesiones y telemetría en Redis
│   ├── routers/                 # Routers FastAPI por dominio
│   │   ├── post_router.py
│   │   ├── comment_router.py
│   │   ├── like_router.py
│   │   ├── follower_router.py
│   │   ├── notification_router.py # Endpoints de notificaciones
│   │   └── admin_routes.py
│   ├── mappers/                 # Transformación de modelos a schemas
│   │   ├── post_mapper.py
│   │   └── comment_mapper.py
│   ├── exceptions/              # Excepciones de dominio personalizadas
│   │   ├── base.py              # AppException base
│   │   ├── post_exceptions.py
│   │   └── comment_exceptions.py
│   ├── utils/
│   │   └── device.py            # Extracción de IP, User-Agent, Device ID
│   └── Test/                    # Tests unitarios y de integración
│       └── test_auth.py         # Suite completa de tests de autenticación y OpenAPI
├── redis/
│   └── redis.conf               # Configuración de Redis
├── docker-compose.yml           # Redis + RedisInsight
├── seed_devcommunity.py         # Script para poblar datos de prueba
├── requirements.txt
└── .env
```

---

## ✨ Módulos y características

### 🔐 Autenticación y Seguridad

- **Registro y Login**: Validación de credenciales únicas, contraseñas hasheadas con `bcrypt` + pre-hash `SHA-256` (sin límite de 72 bytes).
- **Compatibilidad OpenAPI / Swagger UI**: Endpoint `/auth/token` integrado con `OAuth2PasswordRequestForm` para autenticación con el candado interactivo de Swagger.
- **Access Tokens**: JWT (HS256) de corta duración (60 min por defecto) con validación de blacklist en Redis.
- **Refresh Tokens & Rotation**: Tokens criptográficos con `JTI` único guardado en Redis; al refrescar, el token anterior se revoca inmediatamente.
- **Control de Acceso basado en Roles (RBAC)**: Dependencias `get_current_user` y `admin_only`.
- **Manejo Centralizado de Errores**: Jerarquía `AppException` para responder con códigos HTTP y detalles estandarizados.

### 🔔 Notificaciones de Actividad

Sistema automatizado de notificaciones vinculado a las interacciones sociales:

- **Disparadores automáticos**:
  - ❤️ Cuando un usuario le da **like** a tu publicación.
  - 💬 Cuando un usuario **comenta** en tu publicación.
  - 👥 Cuando un usuario nuevo te **sigue**.
- **Contador en tiempo real (`/notifications/unread-count`)**: Optimizado para badges e insignias en el sidebar/navbar del frontend.
- **Gestión de lectura**:
  - Marcar notificaciones individuales como leídas.
  - Marcar todas las notificaciones pendientes como leídas con un solo endpoint (`/notifications/read-all`).
- **Paginación eficiente**: Soporte para consultar historial con `page` y `size`.
- **Integridad referencial**: Borrado en cascada automático (`CASCADE`) al eliminar posts o usuarios.

### 📝 Posts y Multimedia

- **Soporte de Imágenes**: Campo obligatorio `image_url` en la creación y visualización de posts.
- **Exploración Temporal (`since_hours`)**: Filtro para consultar posts publicados dentro de las últimas $N$ horas.
- **Filtros avanzados**: Búsqueda por texto (`search`), autor (`author_id`), rango de fechas (`from_date`, `to_date`).
- **Ordenamiento dinámico**: Por fecha (`recent`), más gustados (`most_liked`) o más comentados (`most_commented`).
- **Estado de interacción (`liked_by_me`)**: Flag booleano en cada post que indica si el usuario autenticado actual ya le dio like.
- **Feed personalizado (`/posts/feed`)**: Publicaciones exclusivas de los usuarios que sigues.
- **Permisos granulares**: Solo el autor puede editar su post; el autor o un administrador pueden eliminarlo.

### 💬 Comentarios

- CRUD completo de comentarios asociados a publicaciones.
- Actualización de contadores (`comments_count`) atómica y concurrente.
- Permisos: solo el autor o un administrador pueden modificar o eliminar un comentario.
- Generación automática de notificación al autor del post.

### ❤️ Likes

- Dar y quitar like en publicaciones de forma idempotente.
- Control de likes duplicados con restricciones y manejo de errores.
- Actualización del contador `likes_count` en tiempo real.
- Notificación automática al autor del post al recibir un like.

### 👥 Sistema de Seguidores

- Seguir y dejar de seguir a otros desarrolladores.
- Prevención de auto-seguimiento (`cannot follow yourself`).
- **Estadísticas públicas por usuario (`/users/{user_id}/stats`)**:
  - Total de posts publicados (`posts_count`).
  - Total de seguidores (`followers_count`).
  - Total de seguidos (`following_count`).
- Notificación inmediata al usuario cuando recibe un nuevo seguidor.

### 📋 Gestión de Sesiones Multi-Dispositivo (Redis)

- Identificación unívoca de dispositivos mediante `device_id` generado a partir del `User-Agent` e `IP`.
- Detección semántica de sistema operativo, navegador y tipo de dispositivo.
- Métricas avanzadas: conteo de renovaciones (`refresh_count`), intentos fallidos y calidad de sesión (`session_quality_score`).
- Gestión remota de sesiones: cerrar sesiones en otros dispositivos o cerrar una sesión específica por `device_id`.

### 🛡️ Panel de Administración

- Listar todos los usuarios registrados.
- Cambiar roles de usuarios (`user`, `admin`).
- Auditoría de métricas de sesión de cualquier usuario.
- Endpoint de mantenimiento para saneamiento de roles huérfanos.

---

## 🌐 Endpoints de la API

Documentación interactiva disponible en:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Auth — `/auth`

| Método | Endpoint | Descripción | Auth |
|---|---|---|---|
| `POST` | `/auth/register` | Registrar nuevo usuario | ❌ |
| `POST` | `/auth/login` | Iniciar sesión (JSON) | ❌ |
| `POST` | `/auth/token` | Iniciar sesión OAuth2 (Form-Data para Swagger) | ❌ |
| `POST` | `/auth/refresh` | Renovar tokens (Token Rotation) | ❌ |
| `POST` | `/auth/logout` | Cerrar sesión e invalidar tokens | ✅ Bearer |
| `GET` | `/auth/me` | Obtener datos del usuario autenticado | ✅ Bearer |
| `GET` | `/auth/sessions` | Listar todas las sesiones activas | ✅ Bearer |
| `GET` | `/auth/sessions/me` | Ver detalles de la sesión actual | ✅ Bearer |
| `GET` | `/auth/sessions/metrics` | Métricas de sesión del usuario | ✅ Bearer |
| `DELETE` | `/auth/sessions/terminate-others` | Cerrar sesiones en otros dispositivos | ✅ Bearer |
| `DELETE` | `/auth/sessions/{device_id}` | Cerrar una sesión específica | ✅ Bearer |

### Posts — `/posts`

| Método | Endpoint | Descripción | Auth |
|---|---|---|---|
| `POST` | `/posts/` | Crear un post con imagen (`image_url`) | ✅ |
| `GET` | `/posts/` | Listar posts (paginado, filtros, `since_hours`, orden) | ✅ |
| `GET` | `/posts/feed` | Feed personalizado (posts de seguidos) | ✅ |
| `GET` | `/posts/{post_id}` | Obtener detalle de un post | ✅ |
| `PUT` | `/posts/{post_id}` | Editar post (solo el autor) | ✅ |
| `DELETE` | `/posts/{post_id}` | Eliminar post (autor o admin) | ✅ |
| `POST` | `/posts/{post_id}/like` | Dar like a un post | ✅ |
| `DELETE` | `/posts/{post_id}/like` | Quitar like a un post | ✅ |
| `POST` | `/posts/admin/fix-roles` | Normalizar roles nulos de usuarios (Admin) | ✅ Admin |

### Notificaciones — `/notifications`

| Método | Endpoint | Descripción | Auth |
|---|---|---|---|
| `GET` | `/notifications/` | Listar mis notificaciones paginadas (`page`, `size`) | ✅ |
| `GET` | `/notifications/unread-count` | Obtener número de notificaciones no leídas | ✅ |
| `PATCH` | `/notifications/read-all` | Marcar todas las notificaciones como leídas | ✅ |
| `PATCH` | `/notifications/{notification_id}/read` | Marcar una notificación específica como leída | ✅ |

### Comentarios — `/comments`

| Método | Endpoint | Descripción | Auth |
|---|---|---|---|
| `POST` | `/comments/{post_id}` | Crear un comentario en un post | ✅ |
| `GET` | `/comments/post/{post_id}` | Listar todos los comentarios de un post | ✅ |
| `PUT` | `/comments/{comment_id}` | Editar comentario (solo el autor) | ✅ |
| `DELETE` | `/comments/{comment_id}` | Eliminar comentario (autor o admin) | ✅ |

### Usuarios / Seguidores — `/users`

| Método | Endpoint | Descripción | Auth |
|---|---|---|---|
| `POST` | `/users/{user_id}/follow` | Seguir a un usuario | ✅ |
| `DELETE` | `/users/{user_id}/follow` | Dejar de seguir a un usuario | ✅ |
| `GET` | `/users/{user_id}/stats` | Estadísticas públicas (posts, seguidores, seguidos) | ❌ |

### Admin — `/admin`

| Método | Endpoint | Descripción | Auth |
|---|---|---|---|
| `GET` | `/admin/users` | Listar todos los usuarios del sistema | ✅ Admin |
| `PUT` | `/admin/users/{user_id}/role` | Modificar el rol de un usuario | ✅ Admin |
| `GET` | `/admin/users/{user_id}/sessions/metrics` | Auditar métricas de sesión de un usuario | ✅ Admin |

---

## ✅ Requisitos previos

- **Python** 3.11+
- **Docker** y **Docker Compose** (para Redis)
- `pip` o gestor de paquetes Python

---

## 🚀 Instalación y ejecución

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/DevCommunity.git
cd DevCommunity
```

### 2. Crear entorno virtual e instalar dependencias

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Configurar variables de entorno

Crear un archivo `.env` en la raíz del proyecto (ver sección [Variables de entorno](#-variables-de-entorno)).

### 4. Levantar Redis con Docker

```bash
docker-compose up -d
```

Esto inicia:
- **Redis** en `localhost:6379`
- **RedisInsight** (GUI web) en `http://localhost:5540`

### 5. Ejecutar la API

```bash
uvicorn app.main:app --reload
```

- La API estará disponible en: **`http://localhost:8000`**
- Documentación interactiva: **`http://localhost:8000/docs`**

---

## 🧪 Ejecución de pruebas

El proyecto incluye una suite de pruebas automatizadas con **Pytest**, mockeando la capa de Redis y utilizando SQLite en memoria:

```bash
# Ejecutar todos los tests
python -m pytest app/Test/test_auth.py -v
```

---

## ⚙️ Variables de entorno

```env
# Base de datos
DATABASE_URL=sqlite:///./devcommunity.db

# Seguridad JWT
SECRET_KEY=tu_clave_secreta_super_segura_aqui

# Tiempos de expiración de tokens
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# Redis
REDIS_URL=redis://:tu_password@localhost:6379/0
```

---

## 🌱 Datos de prueba (Seed)

El proyecto incluye un script para poblar la base de datos con datos de ejemplo (usuarios, posts con imágenes, comentarios, likes y relaciones):

```bash
python seed_devcommunity.py
```

---

## 📌 Estado del proyecto

| Módulo | Estado |
|---|---|
| Autenticación (Register / Login / Logout) | ✅ Completo |
| OAuth2 Password Bearer (Swagger UI Support) | ✅ Completo |
| Token Rotation (Refresh con JTI) | ✅ Completo |
| Gestión de Sesiones Multi-Dispositivo (Redis) | ✅ Completo |
| Blacklist de Access Tokens | ✅ Completo |
| Posts (CRUD + Paginación + Filtros + Imágenes + `since_hours`) | ✅ Completo |
| Feed personalizado de seguidos | ✅ Completo |
| Comentarios (CRUD + Contadores) | ✅ Completo |
| Likes (Idempotencia + Contadores) | ✅ Completo |
| Sistema de Seguidores & Estadísticas | ✅ Completo |
| Sistema de Notificaciones (Likes, Comentarios, Seguimientos) | ✅ Completo |
| Contador de Notificaciones no leídas (`unread-count`) | ✅ Completo |
| Panel de Administración & Gestión de Roles | ✅ Completo |
| Telemetría y Métricas de Sesión | ✅ Completo |
| Tests automatizados de Autenticación | ✅ Completo |
| Migración a PostgreSQL (producción) | 🔜 Pendiente |

---

*Desarrollado con ❤️ usando FastAPI + Redis*

# 🌐 DevCommunity API

> Una API REST de comunidad para desarrolladores — con autenticación segura, gestión de sesiones multi-dispositivo, posts, comentarios, likes y sistema de seguidores.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat&logo=fastapi&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat&logo=sqlite&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7.0-DC382D?style=flat&logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat&logo=docker&logoColor=white)
![Version](https://img.shields.io/badge/version-0.1.0-blue?style=flat)

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
- [Variables de entorno](#-variables-de-entorno)
- [Datos de prueba (Seed)](#-datos-de-prueba-seed)

---

## 🧠 Sobre el proyecto

**DevCommunity** es una plataforma backend tipo red social pensada para desarrolladores. Permite a los usuarios registrarse, publicar contenido, comentar, dar likes, y seguirse entre sí.

El enfoque principal del proyecto es construir una **API segura y escalable**, con un sistema de autenticación robusto (JWT + Redis) y gestión de sesiones multi-dispositivo con telemetría en tiempo real.

---

## 🛠️ Stack tecnológico

| Capa | Tecnología |
|---|---|
| Framework Web | [FastAPI](https://fastapi.tiangolo.com/) |
| ORM | [SQLAlchemy](https://www.sqlalchemy.org/) |
| Base de datos | SQLite (dev) / compatible con PostgreSQL |
| Cache & Sesiones | Redis 7 |
| Autenticación | JWT (`python-jose`) + bcrypt |
| Validación | Pydantic v2 |
| Servidor | Uvicorn |
| Contenerización | Docker Compose |

---

## 🏛️ Arquitectura

El proyecto sigue una arquitectura en capas limpia y separada por responsabilidades:

```
Request
  │
  ▼
Router (Controlador)
  │
  ▼
Service (Lógica de negocio)
  │
  ▼
Repository (Acceso a datos)
  │
  ▼
Model / DB (SQLAlchemy + SQLite)
```

Las sesiones y tokens se manejan en una capa aparte con **Redis**, sin tocar la base de datos SQL.

### Flujo de autenticación

```
POST /auth/login
      │
      ├── Genera Access Token (JWT, 60 min)
      ├── Genera Refresh Token (JWT + JTI en Redis, 7 días)
      └── Crea sesión en Redis (con IP, User-Agent, Device ID)

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
│   ├── main.py                  # Punto de entrada, registro de routers y middleware
│   ├── api/                     # Rutas de prueba / health check
│   ├── auth/                    # Lógica de autenticación (JWT, bcrypt, rutas)
│   │   ├── auth_handler.py      # Creación/verificación de tokens y revocación
│   │   ├── auth_routes.py       # Endpoints: register, login, refresh, logout, me, sessions
│   │   └── auth_utils.py        # Utilidades auxiliares de auth
│   ├── core/                    # Configuración central
│   │   ├── config.py            # Settings (SECRET_KEY, DB URL, Redis URL, etc.)
│   │   ├── dependencies.py      # Dependencias FastAPI (get_current_user, admin_only)
│   │   ├── redis.py             # Conexión al cliente Redis
│   │   └── exceptions_handlers.py
│   ├── db/                      # Configuración de base de datos
│   │   ├── base.py              # Base declarativa SQLAlchemy
│   │   └── session.py           # Engine, SessionLocal, get_db
│   ├── models/                  # Modelos ORM
│   │   ├── user.py
│   │   ├── post.py
│   │   ├── comment.py
│   │   ├── like.py
│   │   ├── follows.py
│   │   └── session.py           # Modelo SessionOut (output Redis)
│   ├── schemas/                 # Schemas Pydantic (request/response)
│   │   ├── user_schema.py
│   │   ├── post_schema.py
│   │   ├── comment_schema.py
│   │   └── session_schema.py
│   ├── repositories/            # Capa de acceso a datos (queries SQL)
│   │   ├── post_repository.py
│   │   ├── comment_repository.py
│   │   ├── like_repository.py
│   │   └── follower_repository.py
│   ├── services/                # Lógica de negocio
│   │   ├── post_service.py
│   │   ├── comment_service.py
│   │   ├── like_service.py
│   │   ├── follower_service.py
│   │   └── session_service.py   # Gestión completa de sesiones en Redis
│   ├── routers/                 # Routers FastAPI por dominio
│   │   ├── post_router.py
│   │   ├── comment_router.py
│   │   ├── like_router.py
│   │   ├── follower_router.py
│   │   └── admin_routes.py
│   ├── mappers/                 # Transformación de modelos a schemas
│   │   ├── post_mapper.py
│   │   └── comment_mapper.py
│   ├── exceptions/              # Excepciones de dominio personalizadas
│   │   ├── base.py
│   │   ├── post_exceptions.py
│   │   └── comment_exceptions.py
│   └── utils/
│       └── device.py            # Extracción de IP, User-Agent, Device ID
├── redis/
│   └── redis.conf               # Configuración personalizada de Redis
├── docker-compose.yml           # Redis + RedisInsight
├── seed_devcommunity.py         # Script para poblar la base de datos
├── requirements.txt
└── .env
```

---

## ✨ Módulos y características

### 🔐 Autenticación y Seguridad

- **Registro** con validación de email y username únicos.
- **Contraseñas** hasheadas con `bcrypt` + pre-hash `SHA-256` (previene el límite de 72 bytes de bcrypt).
- **Access Token** JWT (HS256) de corta duración (60 min por defecto).
- **Refresh Token** JWT con `JTI` único registrado en Redis — soporta revocación exacta.
- **Token Rotation**: al refrescar, el JTI anterior se invalida y se emite uno nuevo.
- **Blacklist de Access Tokens** en Redis al hacer logout (nivel enterprise).
- **Protección por roles**: dependencias `get_current_user` y `admin_only`.
- **CORS** configurado para entornos de desarrollo frontend.

### 📋 Gestión de Sesiones (Redis)

Sistema completo de sesiones multi-dispositivo almacenadas en Redis:

- **Sesión por dispositivo**: identificada por un `device_id` derivado del `User-Agent`.
- **Etiquetado semántico**: detección de OS, browser y tipo de dispositivo (mobile/desktop).
- **Trust level**: clasificación de confianza por IP (preparatorio para geo-detección).
- **Métricas de sesión**: `refresh_count`, `failed_refresh_attempts`, `session_quality_score`, `device_trust_score`.
- **Endpoints de sesión**:
  - Ver todas las sesiones activas.
  - Ver sesión actual.
  - Cerrar sesiones de otros dispositivos.
  - Cerrar sesión específica por `device_id`.
  - Métricas de sesión propias.

### 📝 Posts

- Crear, leer, actualizar y eliminar posts.
- **Paginación** con `page` y `size`.
- **Búsqueda** por texto (`search`).
- **Filtros**: por `author_id`, `from_date`, `to_date`.
- **Ordenamiento**: `recent`, `most_liked`, `most_commented`.
- **Feed personalizado**: posts de los usuarios que sigo.
- Control de permisos: solo el dueño edita; dueño o admin elimina.

### 💬 Comentarios

- CRUD completo sobre comentarios por post.
- Mapper dedicado para transformación de modelos.
- Permisos: solo el dueño edita/elimina (o admin).

### ❤️ Likes

- Dar y quitar like a un post.
- Validación de like duplicado.

### 👥 Seguidores

- Seguir y dejar de seguir usuarios.
- Endpoint de estadísticas públicas por usuario: `posts_count`, `followers_count`, `following_count`.

### 🛡️ Panel de Administración

- Listar todos los usuarios.
- Cambiar el rol de un usuario.
- Ver métricas de sesión de cualquier usuario (auditoría).

---

## 🌐 Endpoints de la API

La documentación interactiva está disponible en:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Auth — `/auth`

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| `POST` | `/auth/register` | Registrar nuevo usuario | ❌ |
| `POST` | `/auth/login` | Iniciar sesión | ❌ |
| `POST` | `/auth/refresh` | Renovar tokens (rotation) | ❌ |
| `POST` | `/auth/logout` | Cerrar sesión | ✅ Bearer |
| `GET` | `/auth/me` | Datos del usuario autenticado | ✅ Bearer |
| `GET` | `/auth/sessions` | Listar sesiones activas | ✅ Bearer |
| `GET` | `/auth/sessions/me` | Sesión actual | ✅ Bearer |
| `GET` | `/auth/sessions/metrics` | Métricas de mis sesiones | ✅ Bearer |
| `DELETE` | `/auth/sessions/terminate-others` | Cerrar sesiones de otros dispositivos | ✅ Bearer |
| `DELETE` | `/auth/sessions/{device_id}` | Cerrar sesión específica | ✅ Bearer |

### Posts — `/posts`

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| `POST` | `/posts/` | Crear post | ✅ |
| `GET` | `/posts/` | Listar posts (paginado + filtros) | ✅ |
| `GET` | `/posts/feed` | Feed personalizado | ✅ |
| `GET` | `/posts/{post_id}` | Obtener post por ID | ✅ |
| `PUT` | `/posts/{post_id}` | Editar post (dueño) | ✅ |
| `DELETE` | `/posts/{post_id}` | Eliminar post (dueño/admin) | ✅ |
| `POST` | `/posts/{post_id}/like` | Dar like | ✅ |
| `DELETE` | `/posts/{post_id}/like` | Quitar like | ✅ |

### Comentarios — `/comments`

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| `POST` | `/comments/{post_id}` | Crear comentario | ✅ |
| `GET` | `/comments/post/{post_id}` | Listar comentarios de un post | ✅ |
| `PUT` | `/comments/{comment_id}` | Editar comentario | ✅ |
| `DELETE` | `/comments/{comment_id}` | Eliminar comentario | ✅ |

### Usuarios / Seguidores — `/users`

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| `POST` | `/users/{user_id}/follow` | Seguir usuario | ✅ |
| `DELETE` | `/users/{user_id}/follow` | Dejar de seguir | ✅ |
| `GET` | `/users/{user_id}/stats` | Estadísticas públicas | ❌ |

### Admin — `/admin`

| Método | Endpoint | Descripción | Auth |
|--------|----------|-------------|------|
| `GET` | `/admin/users` | Listar todos los usuarios | ✅ Admin |
| `PUT` | `/admin/users/{user_id}/role` | Cambiar rol de usuario | ✅ Admin |
| `GET` | `/admin/users/{user_id}/sessions/metrics` | Métricas de sesión de usuario | ✅ Admin |

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

 (ver sección [Variables de entorno](#-variables-de-entorno)).

### 4. Levantar Redis con Docker

```bash
docker-compose up -d
```

Esto inicia:
- **Redis** en `localhost:6379`
- **RedisInsight** (GUI) en `http://localhost:5540`

### 5. Ejecutar la API

```bash
uvicorn app.main:app --reload
```

La API estará disponible en: **`http://localhost:8000`**

Documentación interactiva: **`http://localhost:8000/docs`**

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

El proyecto incluye un script para poblar la base de datos con datos de ejemplo:

```bash
python seed_devcommunity.py
```

Esto crea usuarios, posts, comentarios, likes y relaciones de seguimiento de ejemplo para facilitar el desarrollo y las pruebas.

---

## 📌 Estado del proyecto

| Módulo | Estado |
|--------|--------|
| Autenticación (Register/Login/Logout) | ✅ Completo |
| Token Rotation (Refresh) | ✅ Completo |
| Gestión de Sesiones multi-dispositivo | ✅ Completo |
| Blacklist de Access Tokens | ✅ Completo |
| Posts (CRUD + Paginación + Filtros) | ✅ Completo |
| Feed personalizado | ✅ Completo |
| Comentarios (CRUD) | ✅ Completo |
| Likes | ✅ Completo |
| Sistema de Seguidores | ✅ Completo |
| Panel Admin | ✅ Completo |
| Métricas de sesión | ✅ Completo |
| Tests automatizados | 🚧 En progreso |
| Migración a PostgreSQL (producción) | 🔜 Pendiente |

---

*Desarrollado con ❤️ usando FastAPI + Redis*

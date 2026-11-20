# 🚗 SmartPark API

Sistema inteligente de gestión de parqueaderos desarrollado con **Python, FastAPI y MongoDB**.

SmartPark permite administrar parqueaderos, espacios, usuarios, vehículos, reservas, estancias y pagos, además de generar reportes estadísticos sobre ocupación e ingresos.

## 🛠️ Tecnologías

- **Python 3.14.5:** lenguaje de programación.
- **FastAPI:** framework para desarrollar la API REST.
- **MongoDB 7:** base de datos NoSQL.
- **PyMongo:** conexión asíncrona con MongoDB.
- **Pydantic:** validación de datos.
- **Uvicorn:** servidor ASGI.

## 📋 Requisitos previos

Antes de ejecutar el proyecto, es necesario tener instalado:

- Python 3.14.5.
- Git.
- Docker Desktop.
- MongoDB 7 ejecutándose en Docker.
- Un editor de código (VS Code, PyCharm o IntelliJ IDEA).

Verificar las instalaciones:

```bash
python --version
git --version
docker --version
```

## 📥 1. Clonar el repositorio

```bash
git clone https://github.com/Juandoqg/SmartPark
```

Ingresar al proyecto:

```bash
cd smartpark
```

## 🐍 2. Crear el entorno virtual

Crear el entorno virtual:

```bash
python -m venv .venv
```

Activarlo en Windows PowerShell:

```powershell
.venv\Scripts\activate
```

Si utilizas Linux o macOS:

```bash
source .venv/bin/activate
```

Actualizar pip:

```bash
python -m pip install --upgrade pip
```

## 📦 3. Instalar dependencias

Con el entorno virtual activado, ejecutar:

```bash
pip install -r requirements.txt
```

Si es la primera configuración del proyecto y todavía no existe un `requirements.txt` actualizado, instalar:

```bash
pip install "fastapi[standard]" pymongo pydantic-settings python-dotenv email-validator
```

## ⚙️ 4. Configurar variables de entorno

En la raíz del proyecto existe un archivo `.env.example`.

Crear una copia llamada `.env`:

En PowerShell:

```powershell
Copy-Item .env.example .env
```

Configurar las siguientes variables:

```env
APP_NAME=SmartPark API
APP_VERSION=1.0.0
API_V1_PREFIX=/api/v1

MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=smartpark
```

**Importante:**

- `MONGODB_URL`: dirección de conexión a MongoDB.
- `MONGODB_DATABASE`: nombre de la base de datos que utilizará la aplicación.
- No modificar las variables de entorno sin verificar primero la configuración local.
- El archivo `.env` no debe subirse al repositorio.

## 🐳 5. Configurar MongoDB con Docker

SmartPark utiliza MongoDB 7 como base de datos principal.

Verificar que el contenedor esté ejecutándose:

```bash
docker ps
```

Si todavía no existe un contenedor MongoDB, puedes crear uno:

```bash
docker run -d --name smartpark-mongodb -p 27017:27017 -v smartpark-mongo-data:/data/db mongo:7
```

Verificar que esté activo:

```bash
docker ps
```

La conexión configurada será:

```text
mongodb://localhost:27017
```

**Nota:** Si ya tienes un contenedor MongoDB 7 ejecutándose y exponiendo el puerto `27017`, no necesitas crear otro.

## 🚀 6. Ejecutar el proyecto

Desde la raíz del proyecto, con el entorno virtual activado:

```bash
fastapi dev app/main.py
```

La aplicación estará disponible en:

```text
http://localhost:8000
```

## 📚 7. Documentación de la API

FastAPI genera automáticamente la documentación de los endpoints.

| Recurso | URL |
|---|---|
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Health Check | http://localhost:8000/health |

## 👤 8. Módulo de usuarios

Actualmente se encuentra implementado el módulo inicial de usuarios.

### Registrar usuario

**POST** `/api/v1/users`

Ejemplo de solicitud:

```json
{
  "full_name": "Juan David Quintero",
  "email": "juan@example.com",
  "phone": "3001234567"
}
```

### Consultar usuarios

**GET** `/api/v1/users`

### Respuestas principales

| Código | Descripción |
|---|---|
| 201 | Usuario creado correctamente |
| 200 | Consulta exitosa |
| 409 | Ya existe un usuario con ese correo |
| 422 | Error de validación de los datos |

## 🏗️ 9. Arquitectura del proyecto

El proyecto utiliza una arquitectura por capas sencilla:

```text
app/
│
├── config/
│   └── settings.py
│
├── database/
│   └── mongodb.py
│
├── controllers/
│   └── user_controller.py
│
├── services/
│   └── user_service.py
│
├── repositories/
│   └── user_repository.py
│
├── schemas/
│   └── user_schema.py
│
├── utils/
│
└── main.py
```

### Responsabilidades

- **Controllers:** reciben las peticiones HTTP y gestionan las respuestas.
- **Services:** contienen las reglas de negocio.
- **Repositories:** gestionan las operaciones de persistencia en MongoDB.
- **Schemas:** validan y estructuran los datos de entrada y salida.
- **Database:** administra la conexión con MongoDB.
- **Config:** centraliza las configuraciones de la aplicación.

### Flujo de ejecución

```text
HTTP Request
     |
     v
Controller
     |
     v
Service
     |
     v
Repository
     |
     v
MongoDB
```

## 🧪 10. Ejecutar pruebas

Para ejecutar las pruebas automatizadas:

```bash
pytest
```

Para visualizar los resultados detallados:

```bash
pytest -v
```

## 🔄 11. Detener la aplicación

Para detener el servidor FastAPI:

```text
CTRL + C
```

Para desactivar el entorno virtual:

```bash
deactivate
```

## 👥 12. Equipo de desarrollo

Proyecto académico desarrollado por:

- Juan José Hincapié Tascón.
- Alejandro Luna.
- Juan David Quintero García.
- Sofía Quenoran.
- Juan José Ospina.

**Fecha de entrega:** 22 de diciembre de 2026.

---

**SmartPark API** — Sistema inteligente de gestión de parqueaderos.

## Comparación de MongoDB y PostgreSQL

La persistencia de usuarios y vehículos se puede elegir al iniciar con `DATABASE_BACKEND`. Los servicios usan contratos de repositorio compartidos; cada base implementa su propio adaptador.

Con Docker Compose, MongoDB sigue siendo la opción inicial. Para probar PostgreSQL, inicia con la variable de entorno:

```powershell
$env:DATABASE_BACKEND = "postgresql"
docker compose up --build
```

Para volver a MongoDB:

```powershell
$env:DATABASE_BACKEND = "mongodb"
docker compose up --build
```

El servicio de PostgreSQL está incluido en Compose. `POSTGRES_URL` puede configurarse para cambiar la conexión. 


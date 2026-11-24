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
  "phone": "3001234567",
  "password": "UnaClaveSegura123"
}
```

El backend exige teléfono y almacena la contraseña como hash Argon2; nunca la devuelve en respuestas. Los registros reciben rol `user`, excepto el correo configurado en `ADMIN_EMAIL`, que recibe rol `admin`.

### Inicio de sesión y roles

- `POST /api/v1/auth/login`: recibe `username` (el correo) y `password` como formulario `application/x-www-form-urlencoded`; responde con JWT Bearer.
- `GET /api/v1/auth/me`: retorna el usuario autenticado y su rol.
- Los roles disponibles son `user`, `manager` y `admin`. Un administrador puede asignar `manager` mediante `PATCH /api/v1/users/{user_id}` con `{"role":"manager"}`.
- El helper `require_manager` autoriza `manager` y `admin` para proteger los endpoints de reportes. Los reportes deben declarar `Depends(require_manager)` cuando se implementen.
- El registro y login son públicos. Las consultas operativas requieren token; la gestión de usuarios, vehículos, sedes y espacios requiere rol `admin`.

Configura `JWT_SECRET_KEY` con un valor aleatorio de al menos 32 caracteres y define `ADMIN_EMAIL` en `.env`. Puedes generar la clave con `python -c "import secrets; print(secrets.token_hex(32))"`. Los tokens usan algoritmo HS256 y vencen según `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`.

El primer administrador se crea registrando el correo definido en `ADMIN_EMAIL` (por ejemplo, `admin@gmail.com`; evita dominios reservados como `.local`). Si ese usuario ya existía antes de esta función, el arranque le asigna el rol `admin`, pero un administrador debe establecerle una contraseña en la base de datos antes del primer inicio de sesión. Para asignar el rol `manager`, inicia sesión como administrador y actualiza el usuario con `PATCH /api/v1/users/{user_id}`. Las cuentas existentes sin `password_hash` no podrán iniciar sesión hasta que se les asigne una contraseña.

La contraseña no se cifra para poder recuperarla: se almacena como hash Argon2 con sal. El JWT contiene los claims `sub`, `role`, `email`, `phone`, `iat` y `exp`. La clave JWT se mantiene en `.env` y no se guarda en MongoDB ni PostgreSQL. Las cuentas antiguas sin teléfono deben ser actualizadas por un administrador antes de iniciar sesión.

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

### CRUD de sedes y zonas

El siguiente recurso es `parkings`, que registra una sede y sus zonas. Las zonas se almacenan embebidas en MongoDB y en la tabla relacionada `parking_zones` en PostgreSQL; la API entrega ambas con la misma estructura.

- `POST /api/v1/parkings`: crea una sede con una o más zonas.
- `GET /api/v1/parkings`: lista las sedes.
- `GET /api/v1/parkings/{parking_id}`: consulta una sede.
- `PUT /api/v1/parkings/{parking_id}`: actualiza uno o más campos; al enviar `zones`, reemplaza la lista completa.
- `DELETE /api/v1/parkings/{parking_id}`: elimina una sede.

Se validan el nombre, dirección, ciudad y zonas; cada sede debe tener entre 1 y 50 zonas y no se permiten nombres de zona repetidos sin distinguir mayúsculas. Los campos de creación son obligatorios y las actualizaciones parciales rechazan cuerpos vacíos, campos desconocidos y valores nulos.

### Espacios y disponibilidad

Los espacios se administran en la colección `parking_spaces` de MongoDB (o en la tabla equivalente de PostgreSQL). Cada espacio está asociado a una sede y zona, tiene un código único dentro de la sede, tipos de vehículo admitidos y un estado (`available`, `occupied`, `reserved` o `out_of_service`).

- `POST /api/v1/parkings/{parking_id}/spaces`: crea un espacio.
- `GET /api/v1/parkings/{parking_id}/spaces`: lista espacios; admite filtros opcionales `status` y `vehicle_type`.
- `GET /api/v1/parkings/{parking_id}/availability`: consulta espacios disponibles y cantidad; admite `vehicle_type`.
- `GET /api/v1/parking-spaces/{space_id}`: consulta un espacio.
- `PATCH /api/v1/parking-spaces/{space_id}`: actualiza código, zona, tipos admitidos o estado.
- `DELETE /api/v1/parking-spaces/{space_id}`: elimina un espacio.

El `parking_id` se toma de la ruta y no se repite en el JSON. El cuerpo del espacio incluye `zone_id`, que debe existir dentro de la sede. Los tipos canónicos del sistema son `carro`, `moto` y `bicicleta`; también se aceptan `car`, `motorcycle` y `bicycle` como alias y se normalizan a esos valores.

### Redis opcional

Redis almacena temporalmente el resultado de disponibilidad por sede y tipo de vehículo. MongoDB o PostgreSQL siguen siendo la fuente persistente. La caché expira según `REDIS_AVAILABILITY_TTL_SECONDS` y se invalida cuando se crea, actualiza o elimina un espacio.

En `.env`, configurar `REDIS_ENABLED=true` para activar la integración o `false` para ejecutar sin ella. `REDIS_URL` define la conexión. Con Docker Compose, Redis está disponible en el puerto 6379; la aplicación no usa la caché cuando la opción está desactivada.

### Tarifas y reservas

Las tarifas se guardan en la colección `tariffs` y se consultan por sede, tipo de vehículo y estado. Un administrador o manager puede crearlas con `POST /api/v1/parkings/{parking_id}/tariffs` (el cuerpo incluye `parking_id`, `name`, `vehicle_type`, `hourly_rate` y, opcionalmente, `currency`, `reservation_rate` y `billing_increment_minutes`). `GET` lista las tarifas; `PATCH /api/v1/parkings/{parking_id}/tariffs/{tariff_id}` actualiza precio, nombre, incremento o estado. Desactivar una tarifa conserva su historial.

Un usuario autenticado crea una reserva con `POST /api/v1/reservations`, enviando `space_id`, `vehicle_id`, `tariff_id`, `starts_at`, `ends_at` (fechas ISO 8601 con zona horaria) y `idempotency_key` (única por usuario). `GET /api/v1/reservations` lista sus reservas y `POST /api/v1/reservations/{reservation_id}/cancel` cancela una reserva confirmada. El cálculo estimado suma la tarifa de reserva y el cobro por bloques configurados, redondeando cada fracción al siguiente bloque. La reserva conserva una copia de la tarifa y el estimado para que cambios futuros no alteren el precio histórico; el cobro final pertenece al flujo de salida/pago.

Las sesiones representan las estancias reales, independientemente de que exista una reserva. `POST /api/v1/sessions/entry` inicia una sesión con `parking_id`, `space_id`, `vehicle_id`, `tariff_id` e `idempotency_key`. El usuario solo puede ingresar un vehículo propio; manager/admin puede registrar ingresos operativos. La API valida sede, compatibilidad y tarifa activa, guarda una copia de la tarifa, marca el espacio ocupado y evita más de una sesión activa por espacio. `GET /api/v1/sessions` lista las sesiones del usuario; manager/admin puede consultar todas, filtrando por `parking_id` y `status` (`active` o `completed`).

`POST /api/v1/sessions/{session_id}/exit` cierra la sesión del usuario autenticado o permite que manager/admin registre la salida. El servidor calcula duración real en minutos y cobra bloques completos con `hourly_rate` y `billing_increment_minutes`, redondeando el importe a dos decimales. La sesión queda con `payment_status: pending`; el registro de pagos es un flujo separado. La salida libera el espacio e invalida la caché Redis de disponibilidad.

MongoDB y PostgreSQL conservan los datos persistentes mediante repositorios específicos seleccionados por `DATABASE_BACKEND`. Redis conserva la caché de disponibilidad existente y adquiere un lock temporal por espacio durante la creación de una reserva; el lock tiene TTL de 15 segundos y se libera solo si pertenece a esa operación. Ambos backends garantizan una clave única de idempotencia por usuario y mantienen índices de consulta por espacio/horario y usuario/fecha.


### Reportes

Los reportes se calculan con agregaciones de MongoDB (`$match`, `$group`, `$lookup`, `$project`, `$sort`) y requieren rol `manager` o `admin`. Solo están disponibles con `DATABASE_BACKEND=mongodb`; con PostgreSQL responden `501`.

`GET /api/v1/reports/occupancy` devuelve, por sede, el total de espacios, la cantidad en cada estado (`available`, `occupied`, `reserved`, `out_of_service`) y `occupancy_rate`: el porcentaje de espacios ocupados sobre los que están en servicio. El parámetro opcional `parking_id` limita el resultado a una sede.

`GET /api/v1/reports/revenue?date_from=...&date_to=...` devuelve, por sede y moneda, los ingresos (`revenue`), la cantidad de sesiones completadas y la duración promedio en minutos de las sesiones cuya salida ocurrió en el rango. `date_from` se incluye y `date_to` se excluye; ambas son fechas ISO 8601 y, si no traen zona horaria, se interpretan como UTC. `parking_id` es opcional. El índice `sessions_by_status_exit_date` respalda el filtro por estado y fecha de salida.

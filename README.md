# Práctica MongoDB Atlas con FastAPI

Aplicación web para consultar e insertar alumnos guardados en MongoDB Atlas. La base de datos es `practica_py` y la colección es `alumnos`.

## Tecnologías

- Python 3.13
- FastAPI
- Uvicorn
- PyMongo
- python-dotenv
- Pydantic
- Jinja2, para renderizar la tabla HTML
- HTML5 y CSS3

## Estructura

```text
practicaMongoDB/
├── .venv/
├── .env
├── .env.example
├── .gitignore
├── main.py
├── database.py
├── models.py
├── requirements.txt
├── README.md
└── templates/
    └── index.html
```

- `main.py`: endpoints, validación HTTP y página HTML.
- `database.py`: lectura de `MONGO_URI`, cliente de Atlas y traducción de errores.
- `models.py`: modelos Pydantic y conversión de `ObjectId` a texto.
- `templates/index.html`: tabla de alumnos.
- `.env`: cadena real de conexión. No se sube a Git.
- `.env.example`: plantilla con valores ficticios.

## Activar el entorno

Desde la carpeta del proyecto:

```bash
source .venv/bin/activate
```

## Instalar dependencias

```bash
pip install -r requirements.txt
```

`dnspython` es necesario porque la conexión de Atlas usa `mongodb+srv`. `jinja2` renderiza la plantilla HTML.

## Configurar .env

Copia la plantilla solo si todavía no tienes `.env`:

```bash
cp .env.example .env
```

Edita `.env` y coloca la cadena de tu clúster:

```text
MONGO_URI=mongodb+srv://usuario:contraseña@cluster.ejemplo.mongodb.net/?retryWrites=true&w=majority
```

En este proyecto el archivo `.env` ya existe. No hace falta reemplazarlo. La aplicación nunca imprime esa cadena.

En Atlas, la IP de tu equipo debe estar autorizada y el usuario debe poder leer y escribir en `practica_py`.

## Iniciar el servidor

```bash
python -m uvicorn main:app --reload
```

El servidor queda en `http://localhost:8000`. La documentación interactiva está en `http://localhost:8000/docs`.

La aplicación no inserta alumnos al arrancar.

## Endpoints

| Método | Ruta | Descripción |
| --- | --- | --- |
| GET | `/` | Tabla HTML con todos los alumnos |
| GET | `/api/alumnos` | Todos los alumnos en JSON |
| GET | `/api/alumnos/activos` | Alumnos con `activo: true` |
| GET | `/api/alumnos/carrera?nombre=Administración` | Filtro exacto por carrera |
| GET | `/api/alumnos/promedio?minimo=9` | Alumnos con promedio mayor o igual al mínimo |
| POST | `/api/alumnos` | Inserta un alumno con `insert_one()` |
| GET | `/test-mongo` | Ejecuta `ping` contra Atlas |
| GET | `/docs` | Swagger UI |

## Ejemplos

### Todos los alumnos

```http
GET /api/alumnos
```

```json
[
  {
    "_id": "67101234567890abcdef1234",
    "nombre": "Ana López",
    "matricula": "A001",
    "carrera": "Tecnologías de la Información",
    "promedio": 9.2,
    "activo": true
  }
]
```

### Alumnos activos

```http
GET /api/alumnos/activos
```

Filtro usado en MongoDB:

```json
{"activo": true}
```

### Carrera

```http
GET /api/alumnos/carrera?nombre=Administración
```

Si omites `nombre`, la respuesta es HTTP 422:

```json
{
  "detail": "Los datos de la solicitud no son válidos",
  "errores": [
    {
      "campo": "nombre",
      "mensaje": "El parámetro 'nombre' es obligatorio"
    }
  ]
}
```

La comparación de carrera es exacta, respetando mayúsculas y acentos.

### Promedio mínimo

```http
GET /api/alumnos/promedio?minimo=9
```

Si no envías `minimo`, se usa 9. El filtro es:

```json
{"promedio": {"$gte": 9}}
```

### Insertar un alumno

```http
POST /api/alumnos
Content-Type: application/json
```

```json
{
  "nombre": "Pedro Ramírez",
  "matricula": "A006",
  "carrera": "Tecnologías de la Información",
  "promedio": 8.9,
  "activo": true
}
```

Respuesta exitosa: HTTP 201 con el alumno y su `_id`.

Validaciones:

- `nombre`, `matricula` y `carrera` son obligatorios y no pueden ir vacíos.
- `promedio` debe estar entre 0 y 10.
- `activo` debe ser booleano (`true` o `false`).
- Una matrícula repetida responde HTTP 409 y no se inserta.

### Conexión

```http
GET /test-mongo
```

```json
{
  "conectado": true,
  "mensaje": "Conexión exitosa con MongoDB Atlas"
}
```

Si Atlas no responde, el estado es HTTP 503 y el cuerpo no incluye la cadena de conexión.

## Verificación en MongoDB Compass

1. Conéctate al mismo clúster configurado en `.env`.
2. Abre la base `practica_py`.
3. Abre la colección `alumnos`.
4. Confirma que se ven los documentos ya cargados.
5. Compara esos registros con `http://localhost:8000` y con `http://localhost:8000/api/alumnos`.

## Comprobar el filtro de promedio

En Compass, pestaña **Documents**, usa el filtro:

```json
{"promedio": {"$gte": 9}}
```

Pulsa **Find**. Los documentos mostrados deben coincidir con:

```text
http://localhost:8000/api/alumnos/promedio?minimo=9
```

Para activos, el filtro de Compass es:

```json
{"activo": true}
```

## Insertar un alumno desde Swagger UI

1. Abre `http://localhost:8000/docs`.
2. Despliega `POST /api/alumnos`.
3. Pulsa **Try it out**.
4. Usa una matrícula que todavía no exista.
5. Pulsa **Execute**.
6. La respuesta debe ser **201**.
7. Actualiza Compass y comprueba que el documento nuevo aparece una sola vez.

Esa petición sí escribe en Atlas. Usa una matrícula nueva. Si repites la misma matrícula, la API responde **409**.

## Capturas para entregar

1. Compass con la base `practica_py` y la colección `alumnos`.
2. Compass con el filtro `{"promedio": {"$gte": 9}}`.
3. La tabla HTML en `http://localhost:8000`.
4. El JSON de `http://localhost:8000/api/alumnos`.
5. El JSON de `/api/alumnos/activos`.
6. El JSON de `/api/alumnos/carrera?nombre=` con una carrera que sí exista.
7. El JSON de `/api/alumnos/promedio?minimo=9`.
8. Swagger UI en `http://localhost:8000/docs`.
9. La respuesta **201** de `POST /api/alumnos` hecha desde Swagger.
10. El mismo alumno ya visible en Compass.
11. Una respuesta **409** al intentar repetir esa matrícula.
12. La respuesta de `http://localhost:8000/test-mongo`.

## Errores controlados

- Sin `MONGO_URI`, la aplicación no arranca y el mensaje no incluye secretos.
- Si Atlas no responde o las credenciales fallan, los endpoints responden **503**.
- Un documento con campos faltantes o de tipo incorrecto responde **500** con un mensaje general.
- Los datos inválidos de una petición responden **422**.
- Las matrículas duplicadas responden **409**.
- Las respuestas no incluyen trazas, contraseñas ni la cadena de conexión.

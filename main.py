"""API de alumnos con FastAPI y MongoDB Atlas."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pymongo.errors import PyMongoError

from database import (
    ConfiguracionError,
    cerrar_conexion,
    obtener_coleccion,
    traducir_error_mongo,
    verificar_conexion,
)
from models import AlumnoCreate, AlumnoResponse, DocumentoInvalido, alumno_desde_documento

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("practica_mongodb")

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    """Verifica Atlas al arrancar y cierra el cliente al detenerse."""
    try:
        verificar_conexion()
        logger.info("Ping a MongoDB Atlas correcto")
    except ConfiguracionError:
        logger.error("Falta MONGO_URI en el entorno")
        raise
    except PyMongoError:
        logger.error("MongoDB Atlas no respondió al ping inicial")
    yield
    cerrar_conexion()


app = FastAPI(
    title="Práctica MongoDB Atlas",
    description=(
        "Consulta e inserción de alumnos almacenados en la base "
        "practica_py, colección alumnos."
    ),
    version="1.0.0",
    lifespan=ciclo_de_vida,
)


def _nombre_campo(ubicacion: tuple) -> str:
    partes = [
        str(parte)
        for parte in ubicacion
        if parte not in {"body", "query", "path"}
    ]
    return ".".join(partes) if partes else "solicitud"


def _mensaje_validacion(campo: str, origen: object, error: dict) -> str:
    tipo = str(error.get("type", ""))
    if tipo == "missing":
        if origen == "query":
            return f"El parámetro '{campo}' es obligatorio"
        return f"El campo '{campo}' es obligatorio"
    if tipo == "string_too_short" or tipo == "value_error":
        if campo == "activo":
            return "El campo 'activo' debe ser un booleano"
        return f"El campo '{campo}' no puede estar vacío"
    if campo == "promedio" or campo == "minimo":
        if campo == "minimo":
            return "El parámetro 'minimo' debe estar entre 0 y 10"
        return "El promedio debe estar entre 0 y 10"
    if campo == "activo" or "bool" in tipo:
        return "El campo 'activo' debe ser un booleano"
    return "El valor enviado no es válido"


@app.exception_handler(RequestValidationError)
async def errores_de_validacion(request: Request, exc: RequestValidationError):
    """Devuelve HTTP 422 con el campo y el motivo, sin datos internos."""
    errores = []
    for error in exc.errors():
        ubicacion = error.get("loc", ())
        origen = ubicacion[0] if ubicacion else ""
        campo = _nombre_campo(tuple(ubicacion))
        errores.append(
            {
                "campo": campo,
                "mensaje": _mensaje_validacion(campo, origen, error),
            }
        )
    logger.info("Solicitud inválida en %s", request.url.path)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "detail": "Los datos de la solicitud no son válidos",
            "errores": errores,
        },
    )


def consultar_alumnos(filtro: dict) -> list[AlumnoResponse]:
    """Ejecuta un filtro fijo construido por la API y serializa el resultado."""
    try:
        documentos = obtener_coleccion().find(filtro)
        return [alumno_desde_documento(documento) for documento in documentos]
    except DocumentoInvalido:
        logger.error("La colección alumnos contiene un documento con formato inválido")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Se encontró un documento con formato inválido",
        ) from None
    except PyMongoError as exc:
        raise traducir_error_mongo(exc) from None


@app.get(
    "/",
    response_class=HTMLResponse,
    summary="Tabla HTML de alumnos",
    description="Muestra en una tabla los alumnos registrados en MongoDB Atlas.",
    tags=["Página"],
)
def inicio(request: Request):
    try:
        alumnos = [
            alumno.model_dump(by_alias=True) for alumno in consultar_alumnos({})
        ]
        error = None
        codigo = status.HTTP_200_OK
    except HTTPException as exc:
        alumnos = []
        error = exc.detail
        codigo = exc.status_code
    return templates.TemplateResponse(
        request,
        "index.html",
        {"alumnos": alumnos, "error": error},
        status_code=codigo,
    )


@app.get(
    "/test-mongo",
    summary="Verificar conexión con MongoDB Atlas",
    description="Ejecuta ping sobre el clúster. Responde 503 si Atlas no está disponible.",
    tags=["Sistema"],
    responses={
        503: {"description": "MongoDB Atlas no está disponible o rechazó las credenciales"}
    },
)
def probar_mongo():
    try:
        verificar_conexion()
    except ConfiguracionError as exc:
        logger.error("Configuración de MongoDB incompleta")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from None
    except PyMongoError as exc:
        raise traducir_error_mongo(exc) from None
    return {
        "conectado": True,
        "mensaje": "Conexión exitosa con MongoDB Atlas",
    }


@app.get(
    "/api/alumnos",
    response_model=list[AlumnoResponse],
    summary="Listar alumnos",
    description="Devuelve todos los documentos de la colección alumnos.",
    tags=["Alumnos"],
)
def listar_alumnos():
    return consultar_alumnos({})


@app.get(
    "/api/alumnos/activos",
    response_model=list[AlumnoResponse],
    summary="Listar alumnos activos",
    description="Consulta MongoDB con el filtro {\"activo\": true}.",
    tags=["Alumnos"],
)
def listar_alumnos_activos():
    return consultar_alumnos({"activo": True})


@app.get(
    "/api/alumnos/carrera",
    response_model=list[AlumnoResponse],
    summary="Filtrar alumnos por carrera",
    description=(
        "Recibe el query param nombre y busca coincidencias exactas "
        "en el campo carrera. Si falta el parámetro, responde HTTP 422."
    ),
    tags=["Alumnos"],
)
def listar_alumnos_por_carrera(
    nombre: str = Query(
        ...,
        min_length=1,
        description="Nombre exacto de la carrera",
        examples=["Administración"],
    ),
):
    carrera = nombre.strip()
    if not carrera:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="El parámetro 'nombre' no puede estar vacío",
        )
    return consultar_alumnos({"carrera": carrera})


@app.get(
    "/api/alumnos/promedio",
    response_model=list[AlumnoResponse],
    summary="Filtrar alumnos por promedio mínimo",
    description="Consulta MongoDB con {\"promedio\": {\"$gte\": minimo}}. El valor predeterminado es 9.",
    tags=["Alumnos"],
)
def listar_alumnos_por_promedio(
    minimo: float = Query(
        9,
        ge=0,
        le=10,
        description="Promedio mínimo, inclusive. Predeterminado: 9",
        examples=[9],
    ),
):
    return consultar_alumnos({"promedio": {"$gte": minimo}})


@app.post(
    "/api/alumnos",
    response_model=AlumnoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Insertar un alumno",
    description=(
        "Valida el cuerpo con Pydantic e inserta el documento con insert_one. "
        "Responde 409 si la matrícula ya existe."
    ),
    tags=["Alumnos"],
    responses={
        409: {"description": "La matrícula ya está registrada"},
        422: {"description": "Los datos del alumno no son válidos"},
    },
)
def crear_alumno(alumno: AlumnoCreate):
    coleccion = obtener_coleccion()
    try:
        existente = coleccion.find_one({"matricula": alumno.matricula}, {"_id": 1})
        if existente:
            logger.info("Rechazada matrícula duplicada")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un alumno con esa matrícula",
            )
        resultado = coleccion.insert_one(alumno.model_dump())
    except HTTPException:
        raise
    except PyMongoError as exc:
        raise traducir_error_mongo(exc) from None

    logger.info("Alumno insertado")
    return alumno_desde_documento(
        {
            "_id": resultado.inserted_id,
            **alumno.model_dump(),
        }
    )

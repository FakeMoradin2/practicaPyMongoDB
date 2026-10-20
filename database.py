"""Conexión a MongoDB Atlas.

Lee la cadena de conexión solo desde la variable de entorno MONGO_URI.
No registra ni devuelve credenciales.
"""

import logging
import os

from dotenv import load_dotenv
from fastapi import HTTPException
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import (
    ConfigurationError,
    ConnectionFailure,
    DuplicateKeyError,
    NetworkTimeout,
    OperationFailure,
    PyMongoError,
    ServerSelectionTimeoutError,
)
from pymongo.server_api import ServerApi

logger = logging.getLogger("practica_mongodb")

TIEMPO_ESPERA_MS = 5000

_cliente: MongoClient | None = None


class ConfiguracionError(RuntimeError):
    """Falta la configuración necesaria para conectarse a MongoDB."""


def obtener_uri() -> str:
    """Devuelve MONGO_URI sin imprimir su contenido."""
    load_dotenv()
    uri = os.getenv("MONGO_URI")
    if uri is None or not uri.strip():
        raise ConfiguracionError(
            "No se encontró MONGO_URI. Defínela en el archivo .env"
        )
    return uri.strip()


def obtener_cliente() -> MongoClient:
    """Crea el cliente de MongoDB una sola vez y reutiliza la conexión."""
    global _cliente
    if _cliente is None:
        _cliente = MongoClient(
            obtener_uri(),
            server_api=ServerApi("1"),
            serverSelectionTimeoutMS=TIEMPO_ESPERA_MS,
            connectTimeoutMS=TIEMPO_ESPERA_MS,
            socketTimeoutMS=TIEMPO_ESPERA_MS,
        )
    return _cliente


def obtener_coleccion() -> Collection:
    """Selecciona la base practica_py y la colección alumnos."""
    cliente = obtener_cliente()
    db = cliente["practica_py"]
    collection = db["alumnos"]
    return collection


def verificar_conexion() -> None:
    """Comprueba que Atlas responde mediante ping."""
    obtener_cliente().admin.command("ping")


def cerrar_conexion() -> None:
    """Cierra el cliente al detener la aplicación."""
    global _cliente
    if _cliente is not None:
        _cliente.close()
        _cliente = None


def traducir_error_mongo(exc: PyMongoError) -> HTTPException:
    """Convierte errores de PyMongo en respuestas HTTP sin datos sensibles."""
    logger.error("Error de MongoDB: %s", type(exc).__name__)

    if isinstance(exc, DuplicateKeyError):
        return HTTPException(
            status_code=409,
            detail="Ya existe un alumno con esa matrícula",
        )

    codigo = getattr(exc, "code", None)
    if isinstance(exc, OperationFailure) and codigo in {13, 18}:
        return HTTPException(
            status_code=503,
            detail="Las credenciales de MongoDB Atlas fueron rechazadas",
        )

    if isinstance(
        exc,
        (
            ServerSelectionTimeoutError,
            ConnectionFailure,
            NetworkTimeout,
            ConfigurationError,
        ),
    ):
        return HTTPException(
            status_code=503,
            detail="MongoDB Atlas no está disponible",
        )

    return HTTPException(
        status_code=500,
        detail="No se pudo completar la operación en la base de datos",
    )

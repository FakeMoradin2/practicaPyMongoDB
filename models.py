"""Modelos de alumnos para validar entradas y serializar documentos."""

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator


class DocumentoInvalido(Exception):
    """Un documento de MongoDB no cumple el esquema esperado."""


class AlumnoCreate(BaseModel):
    """Datos necesarios para insertar un alumno."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "nombre": "Pedro Ramírez",
                    "matricula": "A006",
                    "carrera": "Tecnologías de la Información",
                    "promedio": 8.9,
                    "activo": True,
                }
            ]
        }
    )

    nombre: str = Field(
        ...,
        min_length=1,
        description="Nombre completo del alumno",
        examples=["Pedro Ramírez"],
    )
    matricula: str = Field(
        ...,
        min_length=1,
        description="Matrícula única del alumno",
        examples=["A006"],
    )
    carrera: str = Field(
        ...,
        min_length=1,
        description="Carrera del alumno",
        examples=["Tecnologías de la Información"],
    )
    promedio: float = Field(
        ...,
        ge=0,
        le=10,
        description="Promedio entre 0 y 10",
        examples=[8.9],
    )
    activo: bool = Field(
        ...,
        description="Indica si el alumno está activo",
        examples=[True],
    )

    @field_validator("nombre", "matricula", "carrera", mode="before")
    @classmethod
    def limpiar_texto(cls, valor: object) -> object:
        if isinstance(valor, str):
            return valor.strip()
        return valor

    @field_validator("activo", mode="before")
    @classmethod
    def exigir_booleano(cls, valor: object) -> object:
        if isinstance(valor, bool):
            return valor
        raise ValueError("El campo activo debe ser un booleano")


class AlumnoResponse(BaseModel):
    """Alumno listo para enviarse como JSON."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="_id", description="Identificador de MongoDB")
    nombre: str = Field(description="Nombre completo del alumno")
    matricula: str = Field(description="Matrícula del alumno")
    carrera: str = Field(description="Carrera del alumno")
    promedio: float = Field(description="Promedio del alumno")
    activo: bool = Field(description="Indica si el alumno está activo")


def alumno_desde_documento(documento: dict) -> AlumnoResponse:
    """Convierte un documento de MongoDB en una respuesta JSON válida."""
    try:
        return AlumnoResponse.model_validate(
            {
                "_id": str(documento["_id"]),
                "nombre": documento["nombre"],
                "matricula": documento["matricula"],
                "carrera": documento["carrera"],
                "promedio": documento["promedio"],
                "activo": documento["activo"],
            }
        )
    except (KeyError, TypeError, ValidationError) as exc:
        raise DocumentoInvalido from exc

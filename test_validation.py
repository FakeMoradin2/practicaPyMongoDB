from datetime import datetime, timezone

from config import get_database


def main():
    db = get_database()
    invalid_patient = {
        "full_name": "A",
        "email": "correo-invalido",
        "age": 300,
        "created_at": datetime.now(timezone.utc),
    }

    try:
        db["patients"].insert_one(invalid_patient)
        print("Error: el documento inválido fue aceptado.")
    except Exception as error:
        print("Registro rechazado por validación:")
        print(error)


if __name__ == "__main__":
    main()

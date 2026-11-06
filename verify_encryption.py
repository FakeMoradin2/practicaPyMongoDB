from config import get_database


def main():
    db = get_database()
    patient = db["patients"].find_one({"full_name": "Ana López"})
    if patient is None:
        print("No se encontró el paciente.")
        return

    print("national_id:", type(patient["national_id"]).__name__, patient["national_id"].subtype)
    print("diagnosis:", type(patient["diagnosis"]).__name__, patient["diagnosis"].subtype)
    print(patient)


if __name__ == "__main__":
    main()

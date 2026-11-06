from config import get_database


def main():
    db = get_database()
    patients = list(
        db["patients_public"].find({}, {"_id": 0}).sort("created_at", -1).limit(10)
    )

    print("Registros visibles para una aplicación pública:")
    for patient in patients:
        print(patient)


if __name__ == "__main__":
    main()

from config import get_database


def main():
    db = get_database()
    existentes = {coleccion["name"] for coleccion in db.list_collections()}
    if "patients_public" in existentes:
        db.drop_collection("patients_public")

    db.command(
        {
            "create": "patients_public",
            "viewOn": "patients",
            "pipeline": [
                {
                    "$project": {
                        "_id": 1,
                        "full_name": 1,
                        "email": 1,
                        "age": 1,
                        "created_at": 1,
                    }
                }
            ],
        }
    )

    print("Vista 'patients_public' creada.")


if __name__ == "__main__":
    main()

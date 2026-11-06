import uuid
from pathlib import Path

from bson.binary import UuidRepresentation
from bson.codec_options import CodecOptions
from dotenv import load_dotenv
from pymongo.encryption import ClientEncryption

from config import DB_NAME, get_client

load_dotenv()

KEY_VAULT_NAMESPACE = f"{DB_NAME}.__keyVault"
MASTER_KEY_PATH = Path("master-key.bin")
ALT_NAME = "patients-data-key"


def guardar_data_key_id(data_key_id: str) -> None:
    ruta = Path(".env")
    lineas = ruta.read_text().splitlines()
    actualizado = False
    nuevas = []
    for linea in lineas:
        if linea.startswith("DATA_KEY_ID="):
            nuevas.append(f'DATA_KEY_ID="{data_key_id}"')
            actualizado = True
        else:
            nuevas.append(linea)
    if not actualizado:
        nuevas.append(f'DATA_KEY_ID="{data_key_id}"')
    ruta.write_text("\n".join(nuevas) + "\n")


def main():
    if not MASTER_KEY_PATH.exists():
        raise FileNotFoundError(
            "Falta master-key.bin. Genera la llave maestra local antes de continuar."
        )

    client = get_client()
    key_vault = client[DB_NAME]["__keyVault"]
    key_vault.create_index(
        "keyAltNames",
        unique=True,
        partialFilterExpression={"keyAltNames": {"$exists": True}},
    )

    client_encryption = ClientEncryption(
        kms_providers={"local": {"key": MASTER_KEY_PATH.read_bytes()}},
        key_vault_namespace=KEY_VAULT_NAMESPACE,
        key_vault_client=client,
        codec_options=CodecOptions(uuid_representation=UuidRepresentation.STANDARD),
    )

    existente = key_vault.find_one({"keyAltNames": ALT_NAME}, {"_id": 1})
    if existente:
        data_key_uuid = existente["_id"].as_uuid(UuidRepresentation.STANDARD)
        print("Ya existía la llave de datos. DATA_KEY_ID:")
    else:
        data_key_id = client_encryption.create_data_key("local", key_alt_names=[ALT_NAME])
        data_key_uuid = uuid.UUID(bytes=bytes(data_key_id))
        print("Guarda este DATA_KEY_ID en .env:")

    print(data_key_uuid)
    guardar_data_key_id(str(data_key_uuid))
    print("DATA_KEY_ID guardado en .env.")

    client_encryption.close()
    client.close()


if __name__ == "__main__":
    main()

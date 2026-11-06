import os

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME", "clinica")


def get_client():
    if not MONGODB_URI:
        raise ValueError("Falta MONGODB_URI en el archivo .env")
    return MongoClient(MONGODB_URI, serverSelectionTimeoutMS=10000)


def get_database():
    client = get_client()
    return client[DB_NAME]

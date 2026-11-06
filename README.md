# Práctica: Python + MongoDB Atlas con CSFLE

Guarda pacientes en MongoDB Atlas con campos cifrados mediante CSFLE, valida los documentos con JSON Schema y expone la vista `patients_public`, que no incluye datos sensibles.

## Estructura

```text
config.py
create_collection.py
create_data_key.py
create_view.py
insert_patient.py
verify_encryption.py
read_public_view.py
test_validation.py
.env
master-key.bin
```

`.env` y `master-key.bin` no se suben a Git. La llave local sirve solo para esta práctica.

## Preparar el entorno

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

El archivo `.env` debe tener `MONGODB_URI`, `DB_NAME` y, después de crear la llave, `DATA_KEY_ID`.

## Orden de ejecución

```bash
python create_collection.py
python -c "import os; open('master-key.bin','wb').write(os.urandom(96))"
python create_data_key.py
python insert_patient.py
python verify_encryption.py
python create_view.py
python read_public_view.py
python test_validation.py
```

`national_id` usa cifrado determinista. `diagnosis` usa cifrado aleatorio. En una consulta directa ambos deben verse como `Binary`, no como texto.

## Acceso en Atlas

En Database Access crea un usuario de la aplicación pública con un rol que solo pueda leer `clinica.patients_public`. En Network Access deja únicamente las IP necesarias. No uses el usuario administrador en una aplicación pública.

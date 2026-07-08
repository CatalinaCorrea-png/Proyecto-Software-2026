"""
Configuracion compartida de TODOS los tests.

Este modulo lo importa pytest antes de cargar cualquier modulo del backend, asi
que es el lugar correcto para aislar los tests del entorno real. Como
`core.config` hace `load_dotenv()` con override=False, lo que seteemos aca en
os.environ tiene prioridad sobre el .env del proyecto.

  - DATABASE_URL  -> SQLite temporal (nunca tocamos el aerosearch.db real)
  - CAMERA_SOURCE -> "synthetic" (sin camara ni hardware)
  - DRONE_IP      -> 127.0.0.1 (los envios UDP de control van a localhost;
                     nadie escucha, pero al ser UDP no falla)
  - JWT_SECRET    -> fijo, para que los tokens sean validos durante la corrida

Los tests unitarios existentes crean su propio engine (tmp_path), asi que este
cambio no los afecta; solo garantiza que nada escriba en la base real.
"""
import os
import tempfile

_TEST_DB = os.path.join(tempfile.gettempdir(), "aerosearch_pytest.db")

# Arrancar siempre de una base limpia (evita misiones residuales de corridas previas)
for _suffix in ("", "-journal", "-wal", "-shm"):
    try:
        os.remove(_TEST_DB + _suffix)
    except OSError:
        pass

os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB}"
os.environ["CAMERA_SOURCE"] = "synthetic"
os.environ.setdefault("DRONE_IP", "127.0.0.1")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-e2e")

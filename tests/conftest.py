"""Pruebas. Las de integración usan TEST_DATABASE_URL (base vacía con migraciones aplicadas) y se omiten si no está definida."""
import os
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(Path(__file__).parent))

os.environ.setdefault("SECRET_KEY", "x" * 48)
os.environ.setdefault("JWT_SECRET_KEY", "y" * 48)


@pytest.fixture(scope="session")
def app():
    dsn = os.environ.get("TEST_DATABASE_URL")
    if not dsn:
        pytest.skip("Defina TEST_DATABASE_URL para ejecutar las pruebas de integración")
    os.environ["DATABASE_URL"] = dsn
    from migraciones import EjecutorMigraciones
    EjecutorMigraciones(dsn).migrar()
    from app import crear_app
    aplicacion = crear_app()
    s = aplicacion.extensions["seguridad"]
    from Seguridad import Rol
    for nombre, clave, rol in (("admin_t", "Prueba#Segura2026", Rol.ADMIN), ("lector_t", "Lectura#Segura2026", Rol.CONSULTA)):
        if not s.usuarios.buscar_por_nombre(nombre):
            s.crear_usuario(nombre, nombre, clave, rol)
    return aplicacion


@pytest.fixture()
def admin(app):
    from ayudas import iniciar_sesion
    c = app.test_client()
    assert iniciar_sesion(app, c, "admin_t", "Prueba#Segura2026").status_code == 302
    return c


@pytest.fixture()
def lector(app):
    from ayudas import iniciar_sesion
    c = app.test_client()
    assert iniciar_sesion(app, c, "lector_t", "Lectura#Segura2026").status_code == 302
    return c

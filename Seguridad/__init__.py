"""Paquete de Seguridad: autenticación JWT, contraseñas, CAPTCHA, roles y auditoría.

Es autónomo: solo necesita un objeto ``db`` con ``fetch_one / fetch_all / execute``
(ver ``contratos.EjecutorSQL``). No importa nada del paquete ``app``.
"""
from .configuracion import ConfigSeguridad
from .decoradores import login_requerido, rol_requerido, usuario_actual
from .flask_integracion import inicializar_seguridad
from .modelos import Rol, Usuario

__all__ = ["ConfigSeguridad", "inicializar_seguridad", "login_requerido", "rol_requerido",
           "usuario_actual", "Rol", "Usuario"]

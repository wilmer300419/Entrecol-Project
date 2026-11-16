from __future__ import annotations

from functools import wraps

from flask import abort, g, jsonify, redirect, request, url_for

from .modelos import Rol, Usuario


def usuario_actual() -> Usuario | None:
    return getattr(g, "usuario", None)


def _es_api() -> bool:
    return request.path.startswith("/api/")


def login_requerido(vista):
    @wraps(vista)
    def envoltura(*args, **kwargs):
        if usuario_actual() is None:
            if _es_api():
                return jsonify(error="No autenticado"), 401
            return redirect(url_for("auth.login", next=request.full_path.rstrip("?")))
        return vista(*args, **kwargs)
    return envoltura


def rol_requerido(*roles: Rol):
    permitidos = {r.value if isinstance(r, Rol) else r for r in roles}

    def decorador(vista):
        @wraps(vista)
        @login_requerido
        def envoltura(*args, **kwargs):
            if usuario_actual().rol.value not in permitidos:
                if _es_api():
                    return jsonify(error="Sin permisos"), 403
                abort(403)
            return vista(*args, **kwargs)
        return envoltura
    return decorador

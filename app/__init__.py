"""Fábrica de la aplicación Flask (patrón MVC).

* Modelos:       app/models, app/repositories, app/services, app/cargas
* Vistas:        app/templates (HTML), app/reportes/pdf.py (PDF)
* Controladores: app/controllers (blueprints) y Seguridad/ (autenticación)
"""
from __future__ import annotations

import atexit
from dataclasses import asdict

from dotenv import load_dotenv
from flask import Flask, render_template, request

from Seguridad import ConfigSeguridad, inicializar_seguridad
from Seguridad.repositorio import RepositorioAuditoria

from .cargas import CARGADORES
from .config import Configuracion
from .core.database import Database
from .models.catalogo import ENTIDADES
from .repositories.reportes import RepositorioReportes
from .reportes.registro import construir_reportes
from .services.crud import ServicioCrud
from .utils.fechas import formatear_fecha
from .utils.formatos import celda, moneda


def crear_app(config: Configuracion | None = None) -> Flask:
    load_dotenv()
    cfg = config or Configuracion.desde_entorno()
    app = Flask(__name__)
    app.config.update(SECRET_KEY=cfg.secret_key, MAX_CONTENT_LENGTH=cfg.upload_max_mb * 1024 * 1024,
                      ENTORNO=cfg.entorno, CFG=cfg)

    db = Database(cfg.database_url)
    db.abrir()
    atexit.register(db.cerrar)
    app.extensions["db"] = db

    inicializar_seguridad(app, db, ConfigSeguridad(jwt_secreto=cfg.jwt_secret, jwt_expira_min=cfg.jwt_expira_min,
                                                   cookie_segura=cfg.cookie_segura))
    app.extensions["crud"] = ServicioCrud(db, RepositorioAuditoria(db))
    app.extensions["auditoria"] = RepositorioAuditoria(db)
    app.extensions["reportes"] = construir_reportes(RepositorioReportes(db), cfg.filas_pdf_max)
    app.extensions["cargadores"] = {clave: clase(db) for clave, clase in CARGADORES.items()}

    from .controllers import admin, cargas, crud, main, reportes
    for modulo in (main, crud, reportes, cargas, admin):
        app.register_blueprint(modulo.bp)

    app.jinja_env.filters.update(fecha=formatear_fecha, moneda=moneda, celda=celda, a_dict=asdict)

    @app.context_processor
    def menu():
        grupos: dict[str, list] = {}
        for e in ENTIDADES:
            grupos.setdefault(e.grupo, []).append(e)
        return {"menu_datos": grupos, "menu_reportes": list(app.extensions["reportes"].values()),
                "filas_html_max": cfg.filas_html_max}

    @app.after_request
    def cabeceras(resp):
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        resp.headers.setdefault("Referrer-Policy", "same-origin")
        resp.headers.setdefault("Content-Security-Policy",
                                "default-src 'self'; img-src 'self' data:; object-src 'self'; frame-src 'self'; frame-ancestors 'self'; base-uri 'self'; form-action 'self'")
        if request.endpoint in ("auth.login", "auth.login_post") or request.path.startswith("/api/"):
            resp.headers["Cache-Control"] = "no-store"
        return resp

    for codigo, titulo, texto in ((403, "Sin permisos", "Tu rol no permite realizar esta acción."),
                                  (404, "No encontrado", "La página o el registro que buscas no existe."),
                                  (413, "Archivo muy grande", f"El archivo supera el límite de {cfg.upload_max_mb} MB."),
                                  (500, "Error del servidor", "Ocurrió un problema inesperado. Intenta de nuevo.")):
        app.register_error_handler(codigo, lambda e, c=codigo, t=titulo, x=texto: (render_template("errors/error.html", codigo=c, titulo=t, texto=x), c))
    app.register_error_handler(400, lambda e: (render_template("errors/error.html", codigo=400, titulo="Solicitud inválida",
                                                               texto="La solicitud no es válida o la sesión del formulario venció. Recarga la página."), 400))

    from .cli import registrar_comandos
    registrar_comandos(app)
    return app

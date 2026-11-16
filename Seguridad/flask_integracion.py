"""Conecta el paquete con Flask: resolución del usuario por petición, CSRF y rutas /auth."""
from __future__ import annotations

import hashlib
import hmac
from urllib.parse import urlparse

from flask import (Blueprint, Flask, abort, current_app, flash, g, jsonify, make_response,
                   redirect, render_template, request, url_for)

from .captcha import ServicioCaptcha
from .configuracion import ConfigSeguridad
from .contrasenas import HasherContrasena, PoliticaContrasena
from .contratos import EjecutorSQL
from .repositorio import RepositorioAuditoria, RepositorioUsuarios
from .servicio import ErrorAutenticacion, ServicioAutenticacion
from .tokens import ServicioJWT, TokenInvalido

_METODOS_ESCRITURA = {"POST", "PUT", "PATCH", "DELETE"}
auth_bp = Blueprint("auth", __name__, url_prefix="/auth")
api_bp = Blueprint("auth_api", __name__, url_prefix="/api/auth")


def servicio() -> ServicioAutenticacion:
    return current_app.extensions["seguridad"]


def _ip() -> str | None:
    return request.remote_addr


def _agente() -> str:
    return request.headers.get("User-Agent", "")


def _csrf_esperado(jti: str) -> str:
    cfg: ConfigSeguridad = current_app.extensions["seguridad_cfg"]
    return hmac.new(cfg.jwt_secreto.encode(), f"csrf:{jti}".encode(), hashlib.sha256).hexdigest()


def _destino_seguro(destino: str | None) -> str:
    """Evita redirecciones abiertas: solo rutas internas."""
    if destino and destino.startswith("/") and not destino.startswith("//") and not urlparse(destino).netloc:
        return destino
    return url_for("main.inicio")


def inicializar_seguridad(app: Flask, db: EjecutorSQL, cfg: ConfigSeguridad) -> None:
    usuarios, auditoria = RepositorioUsuarios(db), RepositorioAuditoria(db)
    app.extensions["seguridad"] = ServicioAutenticacion(
        usuarios, auditoria, ServicioJWT(cfg), ServicioCaptcha(cfg.jwt_secreto, cfg.captcha_ttl_s),
        HasherContrasena(), PoliticaContrasena(), cfg)
    app.extensions["seguridad_cfg"] = cfg

    @app.before_request
    def resolver_usuario():
        g.usuario, g.claims, g.via_cookie = None, None, False
        token = None
        cabecera = request.headers.get("Authorization", "")
        if cabecera.lower().startswith("bearer "):
            token = cabecera[7:].strip()
        elif request.cookies.get(cfg.cookie_nombre):
            token, g.via_cookie = request.cookies[cfg.cookie_nombre], True
        if not token:
            return
        try:
            g.usuario, g.claims = servicio().autenticar_token(token, _agente())
        except TokenInvalido:
            g.via_cookie = False
            return
        if g.via_cookie and request.method in _METODOS_ESCRITURA:          # protección CSRF
            enviado = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token", "")
            if not hmac.compare_digest(enviado, _csrf_esperado(g.claims.jti)):
                abort(400, "Token CSRF inválido")

    @app.context_processor
    def contexto():
        return {"usuario": g.get("usuario"),
                "csrf_token": lambda: _csrf_esperado(g.claims.jti) if g.get("claims") else ""}

    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)


# ------------------------------------------------------------------ web
@auth_bp.get("/login")
def login():
    if g.usuario:
        return redirect(url_for("main.inicio"))
    svg, token = servicio().captcha.generar()
    return render_template("auth/login.html", captcha_svg=svg, captcha_token=token, siguiente=request.args.get("next", ""))


@auth_bp.post("/login")
def login_post():
    f = request.form
    try:
        token, claims, u = servicio().iniciar_sesion(f.get("usuario", ""), f.get("password", ""),
                                                      f.get("captcha_token", ""), f.get("captcha", ""), _ip(), _agente())
    except ErrorAutenticacion as e:
        svg, nuevo = servicio().captcha.generar()
        return render_template("auth/login.html", captcha_svg=svg, captcha_token=nuevo, error=str(e),
                               usuario_previo=f.get("usuario", ""), siguiente=f.get("next", "")), 401
    cfg = current_app.extensions["seguridad_cfg"]
    resp = make_response(redirect(_destino_seguro(f.get("next"))))
    resp.set_cookie(cfg.cookie_nombre, token, max_age=cfg.jwt_expira_min * 60, httponly=True,
                    secure=cfg.cookie_segura, samesite="Strict", path="/")
    return resp


@auth_bp.post("/logout")
def logout():
    if g.claims:
        try:
            servicio().cerrar_sesion(g.claims, _ip())
        except TokenInvalido:
            pass                                                       # ya estaba cerrada: igual se limpia la cookie
    resp = make_response(redirect(url_for("auth.login")))
    resp.delete_cookie(current_app.extensions["seguridad_cfg"].cookie_nombre, path="/")
    flash("Sesión cerrada correctamente.", "ok")
    return resp


@auth_bp.post("/logout-todas")
def logout_todas():
    if not g.usuario:
        return redirect(url_for("auth.login"))
    n = servicio().cerrar_todas(g.usuario.id, g.usuario.nombre_usuario, ip=_ip())
    resp = make_response(redirect(url_for("auth.login")))
    resp.delete_cookie(current_app.extensions["seguridad_cfg"].cookie_nombre, path="/")
    flash(f"Se cerraron {n} sesión(es) activa(s).", "ok")
    return resp


@auth_bp.get("/captcha")
def captcha_nuevo():
    svg, token = servicio().captcha.generar()
    resp = jsonify(svg=svg, token=token)
    resp.headers["Cache-Control"] = "no-store"
    return resp


# ------------------------------------------------------------------ API JWT
@api_bp.get("/captcha")
def api_captcha():
    return captcha_nuevo()


@api_bp.post("/token")
def api_token():
    d = request.get_json(silent=True) or {}
    try:
        token, claims, _ = servicio().iniciar_sesion(d.get("usuario", ""), d.get("password", ""),
                                                     d.get("captcha_token", ""), d.get("captcha", ""), _ip(), _agente())
    except ErrorAutenticacion as e:
        return jsonify(error=str(e)), 401
    cfg = current_app.extensions["seguridad_cfg"]
    return jsonify(access_token=token, token_type="Bearer", expires_in=cfg.jwt_expira_min * 60)


@api_bp.get("/yo")
def api_yo():
    if not g.usuario:
        return jsonify(error="No autenticado"), 401
    return jsonify(id=g.usuario.id, usuario=g.usuario.nombre_usuario, rol=g.usuario.rol.value,
                   expira=g.claims.exp.isoformat())


@api_bp.post("/logout")
def api_logout():
    if not g.claims:
        return jsonify(error="No autenticado"), 401
    try:
        servicio().cerrar_sesion(g.claims, _ip())
    except TokenInvalido:
        return jsonify(error="La sesión ya no está activa"), 409
    return jsonify(mensaje="Sesión cerrada y token revocado")


@api_bp.post("/logout-todas")
def api_logout_todas():
    if not g.usuario:
        return jsonify(error="No autenticado"), 401
    n = servicio().cerrar_todas(g.usuario.id, g.usuario.nombre_usuario, ip=_ip())
    return jsonify(mensaje="Sesiones cerradas", sesiones=n)


@api_bp.get("/sesiones")
def api_sesiones():
    if not g.usuario:
        return jsonify(error="No autenticado"), 401
    filas = servicio().usuarios.sesiones_activas(g.usuario.id)
    return jsonify([{"sesion": f["jti"][:8], "actual": f["jti"] == g.claims.jti, "emitida": f["emitido_en"].isoformat(),
                     "expira": f["expira_en"].isoformat(), "ip": f["ip"]} for f in filas])

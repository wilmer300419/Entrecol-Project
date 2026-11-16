from __future__ import annotations

from flask import Blueprint, abort, current_app, flash, g, redirect, render_template, request, url_for

from Seguridad import Rol, rol_requerido
from Seguridad.servicio import DatosUsuarioInvalidos

from ..utils.paginacion import Pagina

bp = Blueprint("admin", __name__, url_prefix="/admin")


def _auth():
    return current_app.extensions["seguridad"]


@bp.get("/usuarios")
@rol_requerido(Rol.ADMIN)
def usuarios():
    return render_template("admin/usuarios.html", filas=_auth().usuarios.listar())


@bp.route("/usuarios/nuevo", methods=["GET", "POST"])
@rol_requerido(Rol.ADMIN)
def usuario_nuevo():
    if request.method == "POST":
        f = request.form
        try:
            _auth().crear_usuario(f.get("nombre_usuario", ""), f.get("nombre_visible", ""), f.get("password", ""), Rol(f.get("rol", "CONSULTA")))
            current_app.extensions["auditoria"].registrar(g.usuario.id, g.usuario.nombre_usuario, "CREAR", "usuarios",
                                                          f.get("nombre_usuario", ""), request.remote_addr)
            flash("Usuario creado.", "ok")
            return redirect(url_for("admin.usuarios"))
        except DatosUsuarioInvalidos as exc:
            return render_template("admin/usuario_form.html", valores=f, errores=exc.errores, editando=False, roles=list(Rol)), 422
    return render_template("admin/usuario_form.html", valores={"rol": "CONSULTA"}, errores={}, editando=False, roles=list(Rol))


@bp.route("/usuarios/<int:id_usuario>/editar", methods=["GET", "POST"])
@rol_requerido(Rol.ADMIN)
def usuario_editar(id_usuario):
    u = _auth().usuarios.buscar_por_id(id_usuario) or abort(404)
    if request.method == "GET":
        return render_template("admin/usuario_form.html", valores={"nombre_usuario": u.nombre_usuario, "nombre_visible": u.nombre_visible,
                                                                   "rol": u.rol.value, "activo": "1" if u.activo else ""},
                               errores={}, editando=True, roles=list(Rol), objetivo=u)
    f = request.form
    clave = f.get("password", "")
    errores = _auth().validar_datos(u.nombre_usuario, f.get("nombre_visible", ""), clave or None)
    if u.id == g.usuario.id and (f.get("rol") != u.rol.value or not f.get("activo")):
        errores["rol"] = ["No puedes quitarte tu propio rol ni desactivar tu propia cuenta."]
    if errores:
        return render_template("admin/usuario_form.html", valores=f, errores=errores, editando=True, roles=list(Rol), objetivo=u), 422
    _auth().usuarios.actualizar(u.id, f["nombre_visible"].strip(), Rol(f.get("rol", u.rol.value)), bool(f.get("activo")))
    if not f.get("activo") or f.get("rol") != u.rol.value:
        _auth().cerrar_todas(u.id, u.nombre_usuario, "CAMBIO_ESTADO_O_ROL", request.remote_addr)
    if clave:
        _auth().cambiar_password(u.id, u.nombre_usuario, clave)
    current_app.extensions["auditoria"].registrar(g.usuario.id, g.usuario.nombre_usuario, "ACTUALIZAR", "usuarios", u.nombre_usuario, request.remote_addr)
    flash("Usuario actualizado.", "ok")
    return redirect(url_for("admin.usuarios"))


@bp.post("/usuarios/<int:id_usuario>/cerrar-sesiones")
@rol_requerido(Rol.ADMIN)
def usuario_cerrar_sesiones(id_usuario):
    u = _auth().usuarios.buscar_por_id(id_usuario) or abort(404)
    n = _auth().cerrar_todas(u.id, u.nombre_usuario, f"FORZADO_POR_{g.usuario.nombre_usuario}"[:40], request.remote_addr)
    flash(f"Se cerraron {n} sesión(es) de {u.nombre_usuario}.", "ok")
    return redirect(url_for("admin.usuarios"))


@bp.get("/auditoria")
@rol_requerido(Rol.ADMIN)
def auditoria():
    repo = current_app.extensions["auditoria"]
    n = max(1, request.args.get("pagina", 1, type=int))
    accion, usuario = request.args.get("accion", ""), request.args.get("usuario", "").strip()
    filas, total = repo.listar(accion, usuario, 25, (n - 1) * 25)
    return render_template("admin/auditoria.html", filas=filas, pagina=Pagina(n, 25, total), acciones=repo.acciones(),
                           accion=accion, usuario_filtro=usuario)

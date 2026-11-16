from __future__ import annotations

from flask import Blueprint, abort, current_app, flash, g, redirect, render_template, request, url_for

from Seguridad import Rol, login_requerido, rol_requerido

from ..models.catalogo import POR_SLUG
from ..services.crud import ErrorDeNegocio
from ..utils.paginacion import Pagina

bp = Blueprint("crud", __name__, url_prefix="/datos")
TAM = 15
ESCRIBE = (Rol.ADMIN, Rol.ANALISTA)


def _entidad(slug: str):
    return POR_SLUG.get(slug) or abort(404)


def _opciones(servicio, e) -> dict:
    return {c.nombre: servicio.repo(e).opciones(c) for c in e.campos if c.opciones_sql}


def _a_formulario(e, fila: dict) -> dict:
    valores = {}
    for c in e.campos:
        v = fila.get(c.nombre, fila.get(c.col))
        if c.tipo == "fecha" and v:
            v = v.isoformat()
        elif c.tipo == "multi":
            v = [str(x) for x in (v or [])]
        valores[c.nombre] = "" if v is None else v
    return valores


@bp.get("/<slug>")
@login_requerido
def listar(slug):
    e, servicio = _entidad(slug), current_app.extensions["crud"]
    pagina_n = max(1, request.args.get("pagina", 1, type=int))
    filtros = {c: request.args.get(f"f_{c}", "").strip() for c, _ in e.columnas}
    filtros = {c: v for c, v in filtros.items() if v}
    q, orden = request.args.get("q", "").strip(), request.args.get("orden", "")
    direccion = "desc" if request.args.get("dir") == "desc" else "asc"
    filas, total = servicio.repo(e).listar(q, filtros, orden, direccion, TAM, (pagina_n - 1) * TAM)
    pagina = Pagina(pagina_n, TAM, total)
    return render_template("crud/lista.html", e=e, filas=filas, pagina=pagina, q=q, filtros=filtros,
                           orden=orden or e.orden, direccion=direccion)


def _formulario(e, valores, errores, editando, pk=None, status=200):
    return render_template("crud/formulario.html", e=e, valores=valores, errores=errores, editando=editando, pk=pk,
                           opciones=_opciones(current_app.extensions["crud"], e)), status


@bp.route("/<slug>/nuevo", methods=["GET", "POST"])
@rol_requerido(*ESCRIBE)
def nuevo(slug):
    e, servicio = _entidad(slug), current_app.extensions["crud"]
    if request.method == "GET":
        return _formulario(e, {}, {}, False)
    datos, errores = servicio.validar(e, request.form, request.form.getlist)
    if not errores:
        try:
            servicio.crear(e, datos, g.usuario, request.remote_addr)
            flash(f"Se creó {e.singular} correctamente.", "ok")
            return redirect(url_for("crud.listar", slug=slug))
        except ErrorDeNegocio as exc:
            errores["_general"] = str(exc)
    return _formulario(e, request.form.to_dict() | {c.nombre: request.form.getlist(c.nombre) for c in e.campos if c.tipo == "multi"}, errores, False, status=422)


@bp.route("/<slug>/<pk>/editar", methods=["GET", "POST"])
@rol_requerido(*ESCRIBE)
def editar(slug, pk):
    e, servicio = _entidad(slug), current_app.extensions["crud"]
    fila = servicio.repo(e).obtener(pk)
    if fila is None:
        abort(404)
    if request.method == "GET":
        return _formulario(e, _a_formulario(e, fila), {}, True, pk)
    datos, errores = servicio.validar(e, request.form, request.form.getlist, editando=True)
    if not errores:
        try:
            servicio.actualizar(e, pk, datos, g.usuario, request.remote_addr)
            flash(f"Se actualizó {e.singular} correctamente.", "ok")
            return redirect(url_for("crud.listar", slug=slug))
        except ErrorDeNegocio as exc:
            errores["_general"] = str(exc)
    valores = _a_formulario(e, fila) | request.form.to_dict() | {c.nombre: request.form.getlist(c.nombre) for c in e.campos if c.tipo == "multi"}
    return _formulario(e, valores, errores, True, pk, 422)


@bp.post("/<slug>/<pk>/eliminar")
@rol_requerido(Rol.ADMIN)
def eliminar(slug, pk):
    e = _entidad(slug)
    try:
        current_app.extensions["crud"].eliminar(e, pk, g.usuario, request.remote_addr)
        flash(f"Se eliminó {e.singular}.", "ok")
    except ErrorDeNegocio as exc:
        flash(str(exc), "error")
    return redirect(url_for("crud.listar", slug=slug))

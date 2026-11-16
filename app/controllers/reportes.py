from __future__ import annotations

from flask import Blueprint, Response, abort, current_app, g, render_template, request, url_for

from Seguridad import login_requerido

from ..reportes.pdf import generar_pdf

bp = Blueprint("reportes", __name__, url_prefix="/reportes")


def _reporte(slug: str):
    return current_app.extensions["reportes"].get(slug) or abort(404)


def _auditar(accion: str, slug: str):
    current_app.extensions["auditoria"].registrar(g.usuario.id, g.usuario.nombre_usuario, accion, f"reporte:{slug}",
                                                  request.query_string.decode()[:300], request.remote_addr)


@bp.get("/")
@login_requerido
def indice():
    return render_template("reportes/indice.html")


@bp.get("/<slug>")
@login_requerido
def ver(slug):
    r = _reporte(slug)
    ejecutar = "ejecutar" in request.args
    valores, errores = r.validar(request.args)
    informe = None
    if ejecutar and not errores:
        informe = r.generar(valores)
        _auditar("REPORTE", slug)
    formulario = {p.nombre: request.args.get(p.nombre, p.por_defecto) for p in r.parametros()}
    consulta = {k: v for k, v in request.args.items() if k != "ejecutar"}
    return render_template("reportes/ver.html", r=r, informe=informe, errores=errores if ejecutar else {}, formulario=formulario,
                           parametros=r.parametros(), consulta=consulta)


def _construir_pdf(slug: str):
    r = _reporte(slug)
    valores, errores = r.validar(request.args)
    if errores:
        abort(400)
    return r, generar_pdf(r.generar(valores), g.usuario.nombre_visible)


@bp.get("/<slug>/pdf")
@login_requerido
def pdf(slug):
    r, contenido = _construir_pdf(slug)
    _auditar("REPORTE_PDF", slug)
    disposicion = "attachment" if request.args.get("descargar") else "inline"
    return Response(contenido, mimetype="application/pdf", headers={
        "Content-Disposition": f'{disposicion}; filename="entrecol-{slug}.pdf"', "Cache-Control": "no-store"})


@bp.get("/<slug>/vista-previa")
@login_requerido
def vista_previa(slug):
    r = _reporte(slug)
    _, errores = r.validar(request.args)
    if errores:
        abort(400)
    consulta = {k: v for k, v in request.args.items() if k != "descargar"}
    return render_template("reportes/vista_previa.html", r=r, consulta=consulta,
                           url_pdf=url_for("reportes.pdf", slug=slug, **consulta),
                           url_descarga=url_for("reportes.pdf", slug=slug, descargar=1, **consulta))

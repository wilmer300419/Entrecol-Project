from __future__ import annotations

from flask import Blueprint, current_app, g, render_template, request

from Seguridad import Rol, rol_requerido

from ..cargas import CARGADORES, ErrorCarga

bp = Blueprint("cargas", __name__, url_prefix="/cargas")


@bp.get("/")
@rol_requerido(Rol.ADMIN, Rol.ANALISTA)
def indice():
    return render_template("cargas/indice.html", cargadores=CARGADORES.values())


@bp.post("/<clave>")
@rol_requerido(Rol.ADMIN, Rol.ANALISTA)
def subir(clave):
    clase = CARGADORES.get(clave)
    if clase is None:
        return render_template("errors/error.html", codigo=404, titulo="No encontrado", texto="Tipo de carga desconocido."), 404
    archivo = request.files.get("archivo")
    resultado, error = None, None
    if not archivo or not archivo.filename:
        error = "Seleccione un archivo."
    elif not archivo.filename.lower().endswith(clase.extensiones):
        error = f"Tipo de archivo no permitido. Se espera: {', '.join(clase.extensiones)}"
    else:
        opciones = {}
        if clave == "nomina":
            opciones = {"anio": request.form.get("anio", type=int), "mes": request.form.get("mes", type=int)}
            if opciones["mes"] and not 1 <= opciones["mes"] <= 12:
                opciones["mes"] = None
        try:
            resultado = current_app.extensions["cargadores"][clave].cargar(archivo.read(), **opciones)
            current_app.extensions["auditoria"].registrar(g.usuario.id, g.usuario.nombre_usuario, "CARGA", clave,
                                                          resultado.resumen(), request.remote_addr)
        except ErrorCarga as exc:
            error = str(exc)
    return render_template("cargas/indice.html", cargadores=CARGADORES.values(), resultado=resultado, error=error,
                           clave_activa=clave), (200 if resultado else 422)

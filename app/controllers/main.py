from __future__ import annotations

from flask import Blueprint, current_app, render_template

from Seguridad import login_requerido

bp = Blueprint("main", __name__)


@bp.get("/")
@login_requerido
def inicio():
    db = current_app.extensions["db"]
    tarjetas = [(titulo, db.fetch_one(f"SELECT COUNT(*) AS n FROM {tabla}")["n"], slug) for titulo, tabla, slug in (
        ("Empleados", "empleado", "empleados"), ("Novedades", "novedad", "novedades"),
        ("Películas", "pelicula", "peliculas"), ("Libros", "libro", "libros"))]
    return render_template("dashboard.html", tarjetas=tarjetas)

"""Comandos de consola:  flask --app run <comando>"""
from __future__ import annotations

import os
from pathlib import Path

import click
from flask import Flask

from Seguridad import Rol
from Seguridad.servicio import DatosUsuarioInvalidos

from .cargas import CARGADORES, ErrorCarga
from migraciones import EjecutorMigraciones


def registrar_comandos(app: Flask) -> None:
    cfg = app.config["CFG"]

    @app.cli.command("migrar")
    def migrar():
        """Aplica las migraciones pendientes."""
        click.echo("Aplicadas: " + (", ".join(EjecutorMigraciones(cfg.database_url).migrar()) or "ninguna (al día)"))

    @app.cli.command("estado-migraciones")
    def estado():
        for e in EjecutorMigraciones(cfg.database_url).estado():
            click.echo(f"{e.version}  {'aplicada' if e.aplicada else 'PENDIENTE'}  {e.nombre}")

    @app.cli.command("revertir")
    @click.argument("pasos", default=1)
    def revertir(pasos):
        """Revierte las últimas N migraciones."""
        click.echo("Revertidas: " + (", ".join(EjecutorMigraciones(cfg.database_url).revertir(pasos)) or "ninguna"))

    @app.cli.command("crear-usuario")
    @click.argument("nombre")
    @click.option("--nombre-visible", prompt="Nombre para mostrar")
    @click.option("--rol", type=click.Choice([r.value for r in Rol]), default="ADMIN", show_default=True)
    def crear_usuario(nombre, nombre_visible, rol):
        """Crea un usuario. La contraseña se pide oculta (o variable USUARIO_PASSWORD)."""
        clave = os.environ.get("USUARIO_PASSWORD") or click.prompt("Contraseña", hide_input=True, confirmation_prompt=True)
        try:
            app.extensions["seguridad"].crear_usuario(nombre, nombre_visible, clave, Rol(rol))
            click.echo("Usuario creado.")
        except DatosUsuarioInvalidos as exc:
            raise click.ClickException(" | ".join(m for ms in exc.errores.values() for m in ms))

    @app.cli.command("cargar")
    @click.argument("tipo", type=click.Choice(sorted(CARGADORES)))
    @click.argument("archivo", type=click.Path(exists=True, dir_okay=False, path_type=Path))
    def cargar(tipo, archivo):
        """Carga un archivo (nomina | peliculas | libros) a la base de datos."""
        try:
            r = app.extensions["cargadores"][tipo].cargar(archivo.read_bytes())
        except ErrorCarga as exc:
            raise click.ClickException(str(exc))
        click.echo(f"{r.origen}: {r.resumen()} {r.detalle}")
        for a in r.advertencias:
            click.echo(f"  ! {a}")

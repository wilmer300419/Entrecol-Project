"""Catálogo de entidades administrables (CRUD genérico)."""
from __future__ import annotations

from .meta import Campo, Entidad, RelMuchos, RelRef


def _simple(slug, titulo, singular, tabla, pk, conteo_sql, etiqueta_conteo, grupo="Nómina"):
    return Entidad(
        slug=slug, titulo=titulo, singular=singular, tabla=tabla, pk=pk, grupo=grupo,
        lista_sql=f"SELECT t.{pk}, t.nombre, ({conteo_sql})::int AS usos FROM {tabla} t",
        columnas=((pk, "ID"), ("nombre", "Nombre"), ("usos", etiqueta_conteo)),
        campos=(Campo("nombre", "Nombre", max_len=80 if grupo == "Nómina" else 40),),
        buscar=("nombre",), orden="nombre")


def _validar_novedad(d: dict) -> dict[str, str]:
    if d.get("fecha_inicio") and d.get("fecha_fin") and d["fecha_fin"] < d["fecha_inicio"]:
        return {"fecha_fin": "La fecha final no puede ser anterior a la inicial."}
    return {}


ENTIDADES: tuple[Entidad, ...] = (
    _simple("dependencias", "Dependencias", "dependencia", "dependencia", "id_dependencia",
            "SELECT COUNT(*) FROM cargo c WHERE c.id_dependencia = t.id_dependencia", "Cargos"),
    Entidad(
        slug="cargos", titulo="Cargos", singular="cargo", tabla="cargo", pk="id_cargo", grupo="Nómina",
        lista_sql="""SELECT c.id_cargo, c.nombre, d.nombre AS dependencia,
                            (SELECT COUNT(*) FROM empleado e WHERE e.id_cargo = c.id_cargo)::int AS empleados
                     FROM cargo c JOIN dependencia d ON d.id_dependencia = c.id_dependencia""",
        columnas=(("id_cargo", "ID"), ("nombre", "Cargo"), ("dependencia", "Dependencia"), ("empleados", "Empleados")),
        campos=(Campo("id_dependencia", "Dependencia", "fk",
                      opciones_sql="SELECT id_dependencia AS valor, nombre AS etiqueta FROM dependencia ORDER BY nombre"),
                Campo("nombre", "Nombre del cargo", max_len=100)),
        buscar=("nombre", "dependencia"), orden="dependencia"),
    _simple("eps", "EPS", "EPS", "eps", "id_eps", "SELECT COUNT(*) FROM empleado e WHERE e.id_eps = t.id_eps", "Empleados"),
    _simple("arl", "ARL", "ARL", "arl", "id_arl", "SELECT COUNT(*) FROM empleado e WHERE e.id_arl = t.id_arl", "Empleados"),
    _simple("fondos-pension", "Fondos de pensión", "fondo de pensión", "fondo_pension", "id_fondo_pension",
            "SELECT COUNT(*) FROM empleado e WHERE e.id_fondo_pension = t.id_fondo_pension", "Empleados"),
    Entidad(
        slug="empleados", titulo="Empleados", singular="empleado", tabla="empleado", pk="codigo", pk_auto=False, grupo="Nómina",
        lista_sql="SELECT codigo, nombre_completo, dependencia, cargo, fecha_ingreso, eps, pension, salario FROM v_empleado_detalle",
        columnas=(("codigo", "Código"), ("nombre_completo", "Nombre"), ("dependencia", "Dependencia"), ("cargo", "Cargo"),
                  ("fecha_ingreso", "Ingreso"), ("eps", "EPS"), ("pension", "Pensión"), ("salario", "Salario")),
        campos=(Campo("codigo", "Código", "entero", minimo=1, inmutable=True),
                Campo("apellidos", "Apellidos", max_len=80), Campo("nombres", "Nombres", max_len=80),
                Campo("fecha_ingreso", "Fecha de ingreso", "fecha"),
                Campo("salario", "Salario (COP)", "decimal", minimo=0, maximo=999999999, paso="1"),
                Campo("id_cargo", "Cargo", "fk", opciones_sql="""SELECT c.id_cargo AS valor, d.nombre || ' › ' || c.nombre AS etiqueta
                                                               FROM cargo c JOIN dependencia d ON d.id_dependencia = c.id_dependencia ORDER BY 2"""),
                Campo("id_eps", "EPS", "fk", opciones_sql="SELECT id_eps AS valor, nombre AS etiqueta FROM eps ORDER BY nombre"),
                Campo("id_arl", "ARL", "fk", opciones_sql="SELECT id_arl AS valor, nombre AS etiqueta FROM arl ORDER BY nombre"),
                Campo("id_fondo_pension", "Fondo de pensión", "fk",
                      opciones_sql="SELECT id_fondo_pension AS valor, nombre AS etiqueta FROM fondo_pension ORDER BY nombre")),
        buscar=("codigo", "nombre_completo", "dependencia", "cargo", "eps", "pension"), orden="nombre_completo"),
    Entidad(
        slug="novedades", titulo="Novedades", singular="novedad", tabla="novedad", pk="id_novedad", grupo="Nómina",
        lista_sql="SELECT id_novedad, codigo, nombre_completo, tipo, fecha_inicio, fecha_fin, dias FROM v_novedad_detalle",
        columnas=(("codigo", "Código"), ("nombre_completo", "Empleado"), ("tipo", "Tipo"), ("fecha_inicio", "Inicio"),
                  ("fecha_fin", "Fin"), ("dias", "Días")),
        campos=(Campo("codigo", "Código del empleado", "entero", minimo=1),
                Campo("id_tipo_novedad", "Tipo de novedad", "fk",
                      opciones_sql="SELECT id_tipo_novedad AS valor, nombre AS etiqueta FROM tipo_novedad ORDER BY 1"),
                Campo("fecha_inicio", "Fecha de inicio", "fecha"), Campo("fecha_fin", "Fecha de terminación", "fecha"),
                Campo("dias", "Días de la novedad", "entero", minimo=1, maximo=366)),
        buscar=("codigo", "nombre_completo", "tipo"), orden="fecha_inicio", validadores=(_validar_novedad,)),
    Entidad(
        slug="liquidaciones", titulo="Liquidación mensual", singular="liquidación", tabla="liquidacion_mensual",
        pk="id_liquidacion", grupo="Nómina",
        lista_sql="SELECT id_liquidacion, codigo, nombre_completo, anio, mes, dias_trabajados, bonificacion, auxilio_transporte FROM v_liquidacion_detalle",
        columnas=(("codigo", "Código"), ("nombre_completo", "Empleado"), ("anio", "Año"), ("mes", "Mes"),
                  ("dias_trabajados", "Días trab."), ("bonificacion", "Bonificación"), ("auxilio_transporte", "Transporte")),
        campos=(Campo("codigo", "Código del empleado", "entero", minimo=1),
                Campo("anio", "Año", "entero", minimo=2000, maximo=2100), Campo("mes", "Mes", "entero", minimo=1, maximo=12),
                Campo("bonificacion", "Bonificación", "decimal", minimo=0, paso="1"),
                Campo("auxilio_transporte", "Auxilio de transporte", "decimal", minimo=0, paso="1")),
        buscar=("codigo", "nombre_completo", "anio"), orden="anio"),
    _simple("generos", "Géneros de películas", "género", "genero", "id_genero",
            "SELECT COUNT(*) FROM pelicula_genero pg WHERE pg.id_genero = t.id_genero", "Películas", grupo="Entretenimiento"),
    Entidad(
        slug="peliculas", titulo="Películas", singular="película", tabla="pelicula", pk="id_pelicula", grupo="Entretenimiento",
        lista_sql="SELECT id_pelicula, titulo, anio_estreno, generos, num_generos FROM v_pelicula_detalle",
        columnas=(("id_pelicula", "ID"), ("titulo", "Título"), ("anio_estreno", "Año"), ("generos", "Géneros")),
        campos=(Campo("titulo", "Título", max_len=300),
                Campo("anio_estreno", "Año de estreno", "entero", requerido=False, minimo=1870, maximo=2100),
                Campo("generos", "Géneros", "multi", requerido=False,
                      opciones_sql="SELECT id_genero AS valor, nombre AS etiqueta FROM genero ORDER BY nombre",
                      rel=RelMuchos("pelicula_genero", "id_pelicula", "id_genero", "genero", "id_genero", "nombre"),
                      lectura_sql="(SELECT array_agg(pg.id_genero) FROM pelicula_genero pg WHERE pg.id_pelicula = t.id_pelicula)")),
        buscar=("titulo", "generos", "anio_estreno"), orden="titulo"),
    Entidad(
        slug="libros", titulo="Libros", singular="libro", tabla="libro", pk="id_libro", grupo="Entretenimiento",
        lista_sql="""SELECT id_libro, titulo, autores, editorial, anio_publicacion, calificacion_promedio,
                            cantidad_calificaciones FROM v_libro_detalle""",
        columnas=(("id_libro", "ID"), ("titulo", "Título"), ("autores", "Autores"), ("editorial", "Editorial"),
                  ("anio_publicacion", "Año"), ("calificacion_promedio", "Rating")),
        campos=(Campo("titulo", "Título", max_len=600),
                Campo("autores", "Autores", "lista_texto", requerido=False, ayuda="Separe varios autores con /",
                      rel=RelMuchos("libro_autor", "id_libro", "id_autor", "autor", "id_autor", "nombre", con_orden=True),
                      lectura_sql="""(SELECT string_agg(a.nombre, ' / ' ORDER BY la.orden) FROM libro_autor la
                                      JOIN autor a ON a.id_autor = la.id_autor WHERE la.id_libro = t.id_libro)"""),
                Campo("editorial", "Editorial", "ref_texto", requerido=False, columna="id_editorial", max_len=300,
                      rel=RelRef("editorial", "id_editorial", "nombre"),
                      lectura_sql="(SELECT e.nombre FROM editorial e WHERE e.id_editorial = t.id_editorial)"),
                Campo("codigo_idioma", "Idioma", "fk", requerido=False, valor_texto=True,
                      opciones_sql="SELECT codigo_idioma AS valor, codigo_idioma AS etiqueta FROM idioma ORDER BY 1"),
                Campo("isbn", "ISBN", requerido=False, max_len=10), Campo("isbn13", "ISBN-13", requerido=False, max_len=13),
                Campo("num_paginas", "Páginas", "entero", requerido=False, minimo=0, maximo=100000),
                Campo("fecha_publicacion", "Fecha de publicación", "fecha", requerido=False),
                Campo("calificacion_promedio", "Calificación promedio (0–5)", "decimal", minimo=0, maximo=5, paso="0.01"),
                Campo("cantidad_calificaciones", "Cantidad de calificaciones", "entero", minimo=0),
                Campo("cantidad_resenas", "Cantidad de reseñas", "entero", minimo=0)),
        buscar=("titulo", "autores", "editorial"), orden="titulo"),
)

POR_SLUG = {e.slug: e for e in ENTIDADES}

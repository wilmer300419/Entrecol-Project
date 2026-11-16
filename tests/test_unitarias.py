"""Pruebas unitarias (no requieren base de datos)."""
from datetime import date

import jwt
import pytest

from Seguridad.captcha import ServicioCaptcha
from Seguridad.configuracion import ConfigSeguridad
from Seguridad.contrasenas import HasherContrasena, PoliticaContrasena
from Seguridad.modelos import Rol, Usuario
from Seguridad.tokens import ServicioJWT, TokenInvalido
from app.cargas.libros import alinear
from app.cargas.peliculas import parsear_linea
from app.utils.fechas import formatear_fecha, parsear_fecha, parsear_mes_anio
from app.utils.textos import separar_nombre

CFG = ConfigSeguridad(jwt_secreto="s" * 48)
USUARIO = Usuario(7, "ana", "Ana", Rol.ANALISTA)


def test_politica_contrasena():
    p = PoliticaContrasena()
    assert p.validar("Valida#Clave2026", "ana") == []
    assert len(p.validar("corta")) >= 4
    assert any("nombre de usuario" in e for e in p.validar("Ana#Clave2026xx", "ana"))


def test_hash_no_reversible_y_con_sal():
    h = HasherContrasena()
    a, b = h.cifrar("Valida#Clave2026"), h.cifrar("Valida#Clave2026")
    assert a != b and "Valida" not in a and h.verificar(a, "Valida#Clave2026") and not h.verificar(a, "otra")


def test_jwt_solo_datos_no_sensibles():
    s = ServicioJWT(CFG)
    token, claims = s.emitir(USUARIO)
    carga = jwt.decode(token, CFG.jwt_secreto, algorithms=["HS256"], audience=CFG.jwt_audiencia)
    assert set(carga) == {"sub", "usr", "rol", "jti", "iat", "exp", "iss", "aud"}
    assert s.verificar(token).usr == "ana" and claims.rol == "ANALISTA"


def test_jwt_rechaza_manipulados_y_otros_algoritmos():
    s = ServicioJWT(CFG)
    token, _ = s.emitir(USUARIO)
    with pytest.raises(TokenInvalido):
        s.verificar(token[:-3] + "abc")
    sin_firma = jwt.encode({"sub": "1", "usr": "x", "rol": "ADMIN", "jti": "1", "iat": 1, "exp": 9999999999, "iss": CFG.jwt_emisor, "aud": CFG.jwt_audiencia}, None, algorithm="none")
    with pytest.raises(TokenInvalido):
        s.verificar(sin_firma)
    with pytest.raises(TokenInvalido):
        ServicioJWT(ConfigSeguridad(jwt_secreto="otra" * 12)).verificar(token)


def test_captcha_un_solo_uso_y_respuesta_correcta():
    import time
    c = ServicioCaptcha("s" * 48)
    svg, token = c.generar()
    assert svg.startswith("<svg") and "<text" in svg
    assert "texto" not in jwt.decode(token, c._clave, algorithms=["HS256"])        # el token nunca contiene la respuesta
    assert not c.validar(token, "XXXXX") and not c.validar("basura", "A")
    # Token con respuesta conocida (mismo mecanismo de firma que usa el servicio)
    conocido = jwt.encode({"n": "nonce-1", "h": c._firma("nonce-1", "AB3DE"), "typ": "captcha", "exp": int(time.time()) + 60}, c._clave, algorithm="HS256")
    assert c.validar(conocido, " ab3de ")                                             # no distingue mayúsculas ni espacios
    assert not c.validar(conocido, "AB3DE")                                           # segundo uso: rechazado (anti-repetición)
    vencido = jwt.encode({"n": "nonce-2", "h": c._firma("nonce-2", "AB3DE"), "typ": "captcha", "exp": int(time.time()) - 5}, c._clave, algorithm="HS256")
    assert not c.validar(vencido, "AB3DE")


def test_fechas_y_nombres():
    assert parsear_fecha(20210311) == date(2021, 3, 11) and parsear_fecha("9/16/2006") == date(2006, 9, 16)
    assert parsear_fecha("11/31/2000") is None and formatear_fecha(date(2022, 3, 2)) == "02/03/2022"
    assert parsear_mes_anio("03/2022") == date(2022, 3, 1) and parsear_mes_anio("13/2022") is None
    assert separar_nombre("AGUDELO ESCOBAR EDWAR DAVID") == ("AGUDELO ESCOBAR", "EDWAR DAVID")
    assert separar_nombre("GIRALDO BRICEÑO SANTIAGO") == ("GIRALDO BRICEÑO", "SANTIAGO")


def test_parser_peliculas():
    assert parsear_linea("1::Toy Story (1995)::Adventure|Animation") == (1, "Toy Story", 1995, ["Adventure", "Animation"])
    assert parsear_linea("9::Sin año::(no genres listed)")[3] == []
    with pytest.raises(ValueError):
        parsear_linea("rota")


def test_libro_con_coma_en_autor_se_repara():
    roto = {"bookID": 12224, "title": "Libro", "authors": "Sam Bass Warner", "average_rating": " Jr./Sam B. Warner", "isbn": "3.58", "isbn13": "0674842111",
            "language_code": "9780674842113", "num_pages": "en-US", "ratings_count": 236, "text_reviews_count": 61, "publication_date": "6", "publisher": "4/20/2004", "FIELD13": "Harvard"}
    v = alinear(roto)
    assert v[2] == "Sam Bass Warner, Jr./Sam B. Warner" and v[3] == "3.58" and v[6] == "en-US" and v[10] == "4/20/2004" and v[11] == "Harvard"
    normal = {"bookID": 1, "title": "T", "authors": "A/B", "average_rating": "4.5", "isbn": "1", "isbn13": "2", "language_code": "eng", "num_pages": "3", "ratings_count": "4", "text_reviews_count": "5", "publication_date": "1/1/2000", "publisher": "P", "FIELD13": ""}
    assert alinear(normal)[2] == "A/B" and alinear(normal)[11] == "P"


def test_reportes_con_datos_vacios_generan_pdf_sin_fallar():
    """Instalación nueva (tablas sin datos): todos los reportes deben producir HTML/PDF válidos."""
    from unittest.mock import MagicMock
    from app.repositories.reportes import RepositorioReportes
    from app.reportes.pdf import generar_pdf
    from app.reportes.registro import construir_reportes
    repo = MagicMock(spec=RepositorioReportes)
    for nombre in dir(RepositorioReportes):
        if not nombre.startswith("_"):
            getattr(repo, nombre).return_value = []
    repo.rango_novedades.return_value = None
    repo.rango_anios_libros.return_value = (2000, 2006)
    for slug, reporte in construir_reportes(repo, 5000).items():
        valores, errores = reporte.validar({})
        assert not errores, (slug, errores)
        assert generar_pdf(reporte.generar(valores)).startswith(b"%PDF"), slug

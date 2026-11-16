"""Pruebas de integración (base PostgreSQL con migraciones)."""
from pathlib import Path

import pytest

from ayudas import captcha_resuelto, csrf, iniciar_sesion

DATOS = Path(__file__).resolve().parent.parent.parent / "data"


def test_rutas_protegidas_redirigen_al_login(app):
    c = app.test_client()
    for ruta in ("/", "/datos/empleados", "/reportes/", "/cargas/", "/admin/usuarios"):
        r = c.get(ruta)
        assert r.status_code == 302 and "/auth/login" in r.headers["Location"]
    assert c.get("/api/auth/yo").status_code == 401


def test_login_exige_captcha_y_no_revela_usuarios(app):
    c = app.test_client()
    token, texto = captcha_resuelto(app)
    r = c.post("/auth/login", data={"usuario": "admin_t", "password": "Prueba#Segura2026", "captcha_token": token, "captcha": "MALO1"})
    assert r.status_code == 401 and "verificación" in r.get_data(as_text=True)
    m1 = iniciar_sesion(app, c, "admin_t", "incorrecta").get_data(as_text=True)
    m2 = iniciar_sesion(app, c, "no_existe", "incorrecta").get_data(as_text=True)
    assert "Usuario o contraseña incorrectos" in m1 and "Usuario o contraseña incorrectos" in m2


def test_bloqueo_por_intentos_fallidos(app):
    s = app.extensions["seguridad"]
    s.crear_usuario("bloqueable", "Bloqueable", "Prueba#Segura2026", __import__("Seguridad").Rol.CONSULTA) if not s.usuarios.buscar_por_nombre("bloqueable") else None
    c = app.test_client()
    for _ in range(5):
        iniciar_sesion(app, c, "bloqueable", "mala")
    r = iniciar_sesion(app, c, "bloqueable", "Prueba#Segura2026")
    assert r.status_code == 401 and "bloqueada" in r.get_data(as_text=True)
    app.extensions["db"].execute("UPDATE usuario SET bloqueado_hasta = NULL, intentos_fallidos = 0 WHERE nombre_usuario = 'bloqueable'")


def test_cookie_httponly_y_logout_revoca_token(app):
    c = app.test_client()
    r = iniciar_sesion(app, c, "admin_t", "Prueba#Segura2026")
    cookie = r.headers["Set-Cookie"]
    assert "HttpOnly" in cookie and "SameSite=Strict" in cookie
    token = c.get_cookie("access_token").value
    pagina = c.get("/").data
    assert c.post("/auth/logout", data={"csrf_token": csrf(pagina)}).status_code == 302
    c2 = app.test_client()
    r = c2.get("/api/auth/yo", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401                                         # sesión revocada


def test_csrf_obligatorio_en_post(admin):
    r = admin.post("/datos/dependencias/nuevo", data={"nombre": "Sin CSRF"})
    assert r.status_code == 400


def test_api_jwt(app):
    c = app.test_client()
    token, texto = captcha_resuelto(app)
    r = c.post("/api/auth/token", json={"usuario": "admin_t", "password": "Prueba#Segura2026", "captcha_token": token, "captcha": texto})
    assert r.status_code == 200 and r.json["token_type"] == "Bearer"
    yo = c.get("/api/auth/yo", headers={"Authorization": "Bearer " + r.json["access_token"]}).json
    assert yo["usuario"] == "admin_t" and yo["rol"] == "ADMIN"


def test_rol_consulta_no_puede_escribir_ni_administrar(lector):
    assert lector.get("/datos/empleados").status_code == 200
    assert lector.get("/datos/empleados/nuevo").status_code == 403
    assert lector.get("/cargas/").status_code == 403
    assert lector.get("/admin/usuarios").status_code == 403
    assert lector.get("/admin/auditoria").status_code == 403


def test_crud_dependencia_completo(admin, app):
    csrf_t = csrf(admin.get("/datos/dependencias/nuevo").data)
    r = admin.post("/datos/dependencias/nuevo", data={"nombre": "Dependencia de prueba", "csrf_token": csrf_t})
    assert r.status_code == 302
    pk = app.extensions["db"].fetch_one("SELECT id_dependencia FROM dependencia WHERE nombre = 'Dependencia de prueba'")["id_dependencia"]
    assert admin.post("/datos/dependencias/nuevo", data={"nombre": "Dependencia de prueba", "csrf_token": csrf_t}).status_code == 422   # duplicado
    assert admin.post("/datos/dependencias/nuevo", data={"nombre": "", "csrf_token": csrf_t}).status_code == 422                     # obligatorio
    assert admin.post(f"/datos/dependencias/{pk}/editar", data={"nombre": "Dependencia editada", "csrf_token": csrf_t}).status_code == 302
    assert "Dependencia editada" in admin.get("/datos/dependencias?q=editada").get_data(as_text=True)
    assert admin.post(f"/datos/dependencias/{pk}/eliminar", data={"csrf_token": csrf_t}).status_code == 302
    assert app.extensions["db"].fetch_one("SELECT 1 FROM dependencia WHERE id_dependencia = %s", (pk,)) is None
    acciones = {f["accion"] for f in app.extensions["db"].fetch_all("SELECT accion FROM auditoria WHERE entidad = 'dependencias'")}
    assert {"CREAR", "ACTUALIZAR", "ELIMINAR"} <= acciones


def test_consultas_dinamicas_no_permiten_inyeccion(admin):
    for q in ("'; DROP TABLE empleado; --", "\" OR 1=1 --"):
        assert admin.get("/datos/empleados", query_string={"q": q}).status_code == 200
    assert admin.get("/datos/empleados", query_string={"orden": "codigo; DROP TABLE empleado", "dir": "x"}).status_code == 200
    assert admin.get("/datos/empleados").status_code == 200


@pytest.mark.skipif(not DATOS.exists(), reason="Sin archivos de datos de ejemplo")
def test_cargas_son_idempotentes_y_reparan_libros(app):
    from app.cargas import CargadorLibros, CargadorNomina, CargadorPeliculas
    db = app.extensions["db"]
    r = CargadorLibros(db).cargar((DATOS / "Books.json").read_bytes())
    assert r.rechazados == 0 and r.detalle.get("filas reparadas (autor con coma)") == 4
    r2 = CargadorLibros(db).cargar((DATOS / "Books.json").read_bytes())
    assert r2.insertados == 0 and r2.actualizados == r.insertados + r.actualizados
    n = CargadorNomina(db).cargar((DATOS / "Nomina.xlsx").read_bytes())
    assert n.rechazados == 0 and n.detalle["empleados"] == 20
    assert CargadorPeliculas(db).cargar((DATOS / "movies.dat").read_bytes()).rechazados == 0
    assert db.fetch_one("SELECT autores FROM v_libro_detalle WHERE autores LIKE '%Warner, Jr.%' LIMIT 1")


def test_carga_rechaza_extension_y_archivo_invalido(admin):
    c = csrf(admin.get("/cargas/").data)
    from io import BytesIO
    r = admin.post("/cargas/libros", data={"csrf_token": c, "archivo": (BytesIO(b"{}"), "malo.exe")}, content_type="multipart/form-data")
    assert r.status_code == 422
    r = admin.post("/cargas/libros", data={"csrf_token": c, "archivo": (BytesIO(b"no es json"), "libros.json")}, content_type="multipart/form-data")
    assert r.status_code == 422


@pytest.mark.parametrize("slug", ["nomina", "informacion-personal", "salud-pension", "novedades", "entretenimiento"])
def test_reportes_html_y_pdf(admin, slug):
    assert admin.get(f"/reportes/{slug}").status_code == 200
    assert admin.get(f"/reportes/{slug}?ejecutar=1").status_code == 200
    pdf = admin.get(f"/reportes/{slug}/pdf")
    assert pdf.status_code == 200 and pdf.mimetype == "application/pdf" and pdf.data.startswith(b"%PDF")
    assert admin.get(f"/reportes/{slug}/vista-previa").status_code == 200


def test_reporte_valida_parametros(admin):
    assert admin.get("/reportes/novedades/pdf?desde=99/2022&hasta=01/2022&orden=asc").status_code == 400
    assert "MM/AAAA" in admin.get("/reportes/novedades?ejecutar=1&desde=xx&hasta=01/2022&orden=asc").get_data(as_text=True)
    assert admin.get("/reportes/nomina/pdf?orden=asc;drop").status_code == 400


def test_cabeceras_de_seguridad_y_tema_claro_por_defecto(admin):
    r = admin.get("/")
    assert "default-src 'self'" in r.headers["Content-Security-Policy"] and r.headers["X-Content-Type-Options"] == "nosniff"
    html = r.get_data(as_text=True)
    assert 'data-tema="light"' in html and 'name="viewport"' in html


# ------------------------------------------------------------------ sesiones JWT ligadas a usuario
def _token_api(app, cliente, usuario="admin_t", clave="Prueba#Segura2026", agente=None):
    token, texto = captcha_resuelto(app)
    cab = {"User-Agent": agente} if agente else {}
    r = cliente.post("/api/auth/token", json={"usuario": usuario, "password": clave, "captcha_token": token, "captcha": texto}, headers=cab)
    assert r.status_code == 200
    return r.json["access_token"]


def test_cada_token_queda_registrado_como_sesion_del_usuario_por_dos_horas(app):
    db = app.extensions["db"]
    t = _token_api(app, app.test_client())
    import jwt as _jwt
    jti = _jwt.decode(t, options={"verify_signature": False})["jti"]
    f = db.fetch_one("SELECT s.id_usuario, u.nombre_usuario, s.revocado_en, EXTRACT(EPOCH FROM (s.expira_en - s.emitido_en)) AS seg "
                     "FROM sesion_jwt s JOIN usuario u USING (id_usuario) WHERE s.jti = %s", (jti,))
    assert f["nombre_usuario"] == "admin_t" and f["revocado_en"] is None
    assert round(float(f["seg"])) == 120 * 60                                  # vigencia de 2 horas


def test_token_firmado_sin_sesion_registrada_es_rechazado(app):
    from Seguridad.modelos import Rol, Usuario
    u = app.extensions["seguridad"].usuarios.buscar_por_nombre("admin_t")
    token, _ = app.extensions["seguridad"].jwt.emitir(u)                         # firma válida, pero nunca se creó su sesión
    r = app.test_client().get("/api/auth/yo", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_token_usado_desde_otro_navegador_revoca_la_sesion(app):
    c = app.test_client()
    t = _token_api(app, c, agente="Navegador-A/1.0")
    auth = {"Authorization": f"Bearer {t}"}
    assert c.get("/api/auth/yo", headers={**auth, "User-Agent": "Navegador-A/1.0"}).status_code == 200
    assert c.get("/api/auth/yo", headers={**auth, "User-Agent": "Atacante/9.9"}).status_code == 401
    assert c.get("/api/auth/yo", headers={**auth, "User-Agent": "Navegador-A/1.0"}).status_code == 401       # quedó revocada
    motivo = app.extensions["db"].fetch_one("SELECT motivo_revocacion FROM sesion_jwt ORDER BY emitido_en DESC LIMIT 1")["motivo_revocacion"]
    assert motivo == "AGENTE_DISTINTO"


def test_logout_valida_sesion_activa_y_no_se_puede_repetir(app):
    c = app.test_client()
    t = _token_api(app, c)
    auth = {"Authorization": f"Bearer {t}"}
    assert c.post("/api/auth/logout", headers=auth).status_code == 200
    assert c.get("/api/auth/yo", headers=auth).status_code == 401              # token revocado
    assert c.post("/api/auth/logout", headers=auth).status_code == 401         # ya no autentica
    f = app.extensions["db"].fetch_one("SELECT motivo_revocacion, revocado_en FROM sesion_jwt ORDER BY emitido_en DESC LIMIT 1")
    assert f["motivo_revocacion"] == "LOGOUT" and f["revocado_en"] is not None


def test_cerrar_todas_las_sesiones_del_usuario(app):
    c = app.test_client()
    t1, t2 = _token_api(app, c), _token_api(app, c)
    a1, a2 = {"Authorization": f"Bearer {t1}"}, {"Authorization": f"Bearer {t2}"}
    assert len(c.get("/api/auth/sesiones", headers=a1).json) >= 2
    assert c.post("/api/auth/logout-todas", headers=a1).json["sesiones"] >= 2
    assert c.get("/api/auth/yo", headers=a1).status_code == 401 and c.get("/api/auth/yo", headers=a2).status_code == 401


def test_cambio_de_clave_y_desactivacion_cierran_sesiones(app):
    s = app.extensions["seguridad"]
    from Seguridad import Rol
    if not s.usuarios.buscar_por_nombre("temporal_t"):
        s.crear_usuario("temporal_t", "Temporal", "Temporal#Clave2026", Rol.CONSULTA)
    c = app.test_client()
    t = _token_api(app, c, "temporal_t", "Temporal#Clave2026")
    u = s.usuarios.buscar_por_nombre("temporal_t")
    s.cambiar_password(u.id, u.nombre_usuario, "Otra#Clave2026Nueva")
    assert c.get("/api/auth/yo", headers={"Authorization": f"Bearer {t}"}).status_code == 401
    app.extensions["db"].execute("DELETE FROM usuario WHERE nombre_usuario = 'temporal_t'")                      # ON DELETE CASCADE limpia sus sesiones
    assert app.extensions["db"].fetch_one("SELECT 1 FROM sesion_jwt WHERE id_usuario = %s", (u.id,)) is None


def test_admin_puede_forzar_cierre_de_sesiones_de_un_usuario(admin, app):
    otro = app.test_client()
    t = _token_api(app, otro, "lector_t", "Lectura#Segura2026")
    uid = app.extensions["seguridad"].usuarios.buscar_por_nombre("lector_t").id
    tok = csrf(admin.get("/admin/usuarios").data)
    assert admin.post(f"/admin/usuarios/{uid}/cerrar-sesiones", data={"csrf_token": tok}).status_code == 302
    assert otro.get("/api/auth/yo", headers={"Authorization": f"Bearer {t}"}).status_code == 401


def test_restricciones_de_la_tabla_sesion(app):
    from psycopg import errors
    db = app.extensions["db"]
    uid = app.extensions["seguridad"].usuarios.buscar_por_nombre("admin_t").id
    with pytest.raises(errors.CheckViolation):
        db.execute("INSERT INTO sesion_jwt (jti, id_usuario, expira_en, agente_hash) VALUES ('x1', %s, now() - interval '1 hour', 'a')", (uid,))
    with pytest.raises(errors.ForeignKeyViolation):
        db.execute("INSERT INTO sesion_jwt (jti, id_usuario, expira_en, agente_hash) VALUES ('x2', 999999, now() + interval '1 hour', 'a')")


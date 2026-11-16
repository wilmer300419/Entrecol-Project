# EntreCOL+ · Sistema de Información (Proyecto Final Bases de Datos 2026-2)

Aplicación web **Flask + PostgreSQL** (MVC, POO y SOLID) para administrar la nómina y la base de entretenimiento
(películas y libros) de EntreCOL+, con autenticación **JWT**, auditoría, CRUD, consultas dinámicas, cargas de archivos
y cinco reportes con **vista previa en PDF**. Frontend responsivo con **tema claro por defecto** y modo oscuro.

## Requisitos
- Python 3.11+ y PostgreSQL 14+ (probado con Python 3.12 y PostgreSQL 16)

## Puesta en marcha

```bash
python -m venv .venv && source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 1) Base de datos vacía
createdb entrecol                                         # o créala desde pgAdmin

# 2) Configuración
cp .env.example .env                                      # Windows: copy .env.example .env
#   Edita .env: DATABASE_URL y genera los dos secretos con
#   python -c "import secrets; print(secrets.token_urlsafe(48))"

# 3) Migraciones (crea tablas, índices, vistas y roles)
flask --app run migrar

# 4) Primer usuario administrador (la contraseña se pide oculta)
flask --app run crear-usuario admin --nombre-visible "Administrador" --rol ADMIN

# 5) Cargar los archivos del cliente (o hazlo desde la web: menú «Cargar archivos»)
flask --app run cargar nomina Nomina.xlsx
flask --app run cargar peliculas movies.dat
flask --app run cargar libros Books.json

# 6) Ejecutar
flask --app run run          # http://127.0.0.1:5000
```

**Alternativa rápida:** restaurar `sql/entrecol_bd.sql` (esquema + vistas + datos de ejemplo, sin usuarios):
`psql -d entrecol -f sql/entrecol_bd.sql` y luego el paso 4.

> La contraseña no puede contener el nombre de usuario y debe tener ≥10 caracteres con mayúscula, minúscula, número y símbolo.

## Estructura (MVC)

```
app/
  models/          Modelo: metadatos de entidades (catalogo.py) y estructura de informes
  repositories/    Modelo: SQL (crud genérico + consultas de reportes sobre vistas)
  services/        Modelo: validación y reglas de negocio del CRUD
  cargas/          Modelo: cargadores de Excel / .dat / .json (clase base Cargador)
  reportes/        5 reportes (clase base Reporte) + generador PDF (vista PDF)
  controllers/     Controladores: blueprints de Flask
  templates/ static/   Vista HTML/CSS/JS (tema claro/oscuro, responsivo, accesible)
  utils/           Utilería: fechas, textos, formatos, paginación
Seguridad/         JWT, contraseñas, CAPTCHA, roles, CSRF y auditoría (lógica propia, sin importar `app`)
migraciones/       Ejecutor + versions/V00x__*.up.sql / .down.sql
sql/               entrecol_bd.sql (completo) y entrecol_esquema.sql (solo estructura)
tests/             35 pruebas (unitarias e integración)
```

## Migraciones
```bash
python -m migraciones estado        # o: flask --app run estado-migraciones
python -m migraciones migrar
python -m migraciones revertir 1    # baja la última versión
```
Cada migración corre en una transacción; no se puede modificar una migración ya aplicada (checksum).

## Seguridad
| Tema | Implementación |
|---|---|
| Contraseñas | Política + hash scrypt con sal |
| Segundo factor | CAPTCHA propio (SVG + token firmado de un solo uso) |
| JWT | Cookie HttpOnly/SameSite=Strict para la web; `Authorization: Bearer` para la API. Claims no sensibles: `sub, usr, rol, jti, iat, exp, iss, aud` |
| Fuerza bruta | 5 fallos → bloqueo 15 min |
| Sesión JWT | Tabla `sesion_jwt` (FK a `usuario`): cada token vive 2 h y solo vale si su sesión existe, está activa y coincide con el navegador. Logout validado, «cerrar todas» y revocación al cambiar clave/rol/estado |
| CSRF | Token HMAC por sesión en todo POST con cookie |
| Roles | `ADMIN`, `ANALISTA`, `CONSULTA` |
| Auditoría | Tabla `auditoria` (visible para ADMIN) |

### API JWT (ejemplo)
```bash
curl -s localhost:5000/api/auth/captcha                    # {"svg": "...", "token": "..."}  → resolver la imagen
curl -s -X POST localhost:5000/api/auth/token -H "Content-Type: application/json" \
     -d '{"usuario":"admin","password":"…","captcha_token":"…","captcha":"AB3DE"}'
curl -s localhost:5000/api/auth/yo -H "Authorization: Bearer <access_token>"
curl -s localhost:5000/api/auth/sesiones -H "Authorization: Bearer <access_token>"       # sesiones activas
curl -s -X POST localhost:5000/api/auth/logout -H "Authorization: Bearer <access_token>"   # revoca esta sesión
```

## Pruebas
```bash
createdb entrecol_test
TEST_DATABASE_URL=postgresql://usuario:clave@localhost:5432/entrecol_test pytest -q
```
Sin `TEST_DATABASE_URL` solo se ejecutan las pruebas unitarias.
Las pruebas de carga usan los archivos de ejemplo si existen en `../data/` (`Books.json`, `Nomina.xlsx`, `movies.dat`).

## Producción
`gunicorn "run:app"` detrás de HTTPS y `COOKIE_SEGURA=true`. No subas `.env` al repositorio.

## Cómo agregar…
- **Un reporte:** subclase de `Reporte` en `app/reportes/` y registrarla en `registro.py`.
- **Una entidad al CRUD:** declarar una `Entidad` en `app/models/catalogo.py`.
- **Un formato de carga:** subclase de `Cargador` y registrarla en `app/cargas/__init__.py`.

from __future__ import annotations

from datetime import date
from io import BytesIO

from openpyxl import load_workbook
from psycopg import sql

from ..utils.fechas import parsear_fecha
from ..utils.textos import a_decimal, a_entero, limpiar, normalizar_encabezado, separar_nombre
from .base import Cargador, ErrorCarga, ResultadoCarga

_TIPO_INCAPACIDAD, _TIPO_VACACIONES = 1, 2
_OBLIGATORIAS_EMP = ["codigo", "nombre del empleado", "dependencia", "cargo", "fecha ingreso", "eps", "arl", "pension", "sueldo"]


class _Hoja:
    def __init__(self, filas: list[tuple]):
        self.enc = {normalizar_encabezado(c): i for i, c in enumerate(filas[0]) if c is not None}
        self.filas = filas[1:]

    def tiene(self, *cols: str) -> bool:
        return all(c in self.enc for c in cols)

    def valor(self, fila: tuple, col: str):
        i = self.enc.get(col)
        return fila[i] if i is not None and i < len(fila) else None


class CargadorNomina(Cargador):
    clave, titulo, extensiones = "nomina", "Nómina de empleados (Excel)", (".xlsx",)

    def cargar(self, contenido: bytes, anio: int | None = None, mes: int | None = None, **_) -> ResultadoCarga:
        try:
            libro = load_workbook(BytesIO(contenido), data_only=True, read_only=True)
        except Exception as exc:
            raise ErrorCarga("No se pudo leer el archivo Excel (¿está dañado o no es .xlsx?).") from exc
        empleados = novedades = None
        for ws in libro.worksheets:
            filas = [f for f in ws.iter_rows(values_only=True)]
            if not filas or not any(filas[0]):
                continue
            hoja = _Hoja(filas)
            if hoja.tiene("nombre del empleado"):
                empleados = hoja
            elif hoja.tiene("novedad incapacidad", "novedad vacaciones"):
                novedades = hoja
        if empleados is None:
            raise ErrorCarga("No se encontró la hoja de empleados (debe tener la columna 'NOMBRE DEL EMPLEADO').")
        faltan = [c for c in _OBLIGATORIAS_EMP if c not in empleados.enc]
        if faltan:
            raise ErrorCarga("Faltan columnas en la hoja de empleados: " + ", ".join(faltan).upper())

        res = ResultadoCarga("Nómina")
        with self._db.transaccion() as conn:
            cache: dict[tuple, int] = {}

            def catalogo(tabla: str, pk: str, nombre: str, extra: dict | None = None) -> int:
                clave = (tabla, nombre, tuple((extra or {}).items()))
                if clave not in cache:
                    cols = {**(extra or {}), "nombre": nombre}
                    consulta = sql.SQL("INSERT INTO {t} ({c}) VALUES ({p}) ON CONFLICT ({u}) DO UPDATE SET nombre = EXCLUDED.nombre RETURNING {pk}").format(
                        t=sql.Identifier(tabla), c=sql.SQL(", ").join(map(sql.Identifier, cols)),
                        p=sql.SQL(", ").join(sql.Placeholder() * len(cols)),
                        u=sql.SQL(", ").join(map(sql.Identifier, cols)) if extra else sql.Identifier("nombre"),
                        pk=sql.Identifier(pk))
                    cache[clave] = conn.execute(consulta, list(cols.values())).fetchone()[pk]
                return cache[clave]

            for n, fila in enumerate(empleados.filas, start=2):
                if not any(fila):
                    continue
                v = lambda c: empleados.valor(fila, c)          # noqa: E731
                codigo, ingreso, salario = a_entero(v("codigo")), parsear_fecha(v("fecha ingreso")), a_decimal(v("sueldo"))
                textos = {c: limpiar(v(c)) for c in ("nombre del empleado", "dependencia", "cargo", "eps", "arl", "pension")}
                problemas = [x for x, ok in (("código", codigo and codigo > 0), ("fecha de ingreso", ingreso),
                                             ("sueldo", salario is not None and salario >= 0)) if not ok]
                problemas += [c for c, t in textos.items() if not t]
                if problemas:
                    res.rechazados += 1
                    res.advertir(f"Empleados fila {n}: dato inválido o vacío ({', '.join(problemas)}).")
                    continue
                apellidos, nombres = separar_nombre(textos["nombre del empleado"])
                id_dep = catalogo("dependencia", "id_dependencia", textos["dependencia"])
                id_cargo = catalogo("cargo", "id_cargo", textos["cargo"], {"id_dependencia": id_dep})
                nuevo = conn.execute(
                    """INSERT INTO empleado (codigo, apellidos, nombres, fecha_ingreso, salario, id_cargo, id_eps, id_arl, id_fondo_pension)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                       ON CONFLICT (codigo) DO UPDATE SET apellidos=EXCLUDED.apellidos, nombres=EXCLUDED.nombres,
                         fecha_ingreso=EXCLUDED.fecha_ingreso, salario=EXCLUDED.salario, id_cargo=EXCLUDED.id_cargo,
                         id_eps=EXCLUDED.id_eps, id_arl=EXCLUDED.id_arl, id_fondo_pension=EXCLUDED.id_fondo_pension
                       RETURNING (xmax = 0) AS nuevo""",
                    (codigo, apellidos, nombres, ingreso, salario, id_cargo,
                     catalogo("eps", "id_eps", textos["eps"]), catalogo("arl", "id_arl", textos["arl"]),
                     catalogo("fondo_pension", "id_fondo_pension", textos["pension"]))).fetchone()["nuevo"]
                res.insertados += nuevo
                res.actualizados += not nuevo
            res.detalle["empleados"] = res.insertados + res.actualizados

            if novedades is not None:
                self._cargar_novedades(conn, novedades, res, anio, mes)
        return res

    # --------------------------------------------------------------------
    def _cargar_novedades(self, conn, hoja: _Hoja, res: ResultadoCarga, anio: int | None, mes: int | None) -> None:
        existentes = {f["codigo"] for f in conn.execute("SELECT codigo FROM empleado").fetchall()}
        fechas = [parsear_fecha(hoja.valor(f, c)) for f in hoja.filas
                  for c in ("fecha inicio incapacidad", "fecha de inicio de vacaciones")]
        fechas = [d for d in fechas if d]
        base = max(fechas) if fechas else date.today()           # período por defecto: la novedad más reciente
        anio, mes = anio or base.year, mes or base.month
        n_nov = n_liq = 0
        for n, fila in enumerate(hoja.filas, start=2):
            if not any(fila):
                continue
            v = lambda c: hoja.valor(fila, c)                    # noqa: E731
            codigo = a_entero(v("codigo"))
            if codigo not in existentes:
                res.rechazados += 1
                res.advertir(f"Novedades fila {n}: el código {v('codigo')} no existe en empleados.")
                continue
            for tipo, c_ini, c_fin, c_dias in (
                    (_TIPO_INCAPACIDAD, "fecha inicio incapacidad", "fecha terminacion incapacidad", "numero dias incapacidades en el mes"),
                    (_TIPO_VACACIONES, "fecha de inicio de vacaciones", "fecha terminacion de vacaciones", "numero de dias vacaciones")):
                ini, fin = parsear_fecha(v(c_ini)), parsear_fecha(v(c_fin))
                if not ini and not fin:
                    continue
                if not (ini and fin and fin >= ini):
                    res.rechazados += 1
                    res.advertir(f"Novedades fila {n}: fechas inválidas ({c_ini}/{c_fin}).")
                    continue
                dias = a_entero(v(c_dias)) or (fin - ini).days + 1
                conn.execute("""INSERT INTO novedad (codigo, id_tipo_novedad, fecha_inicio, fecha_fin, dias) VALUES (%s,%s,%s,%s,%s)
                                ON CONFLICT (codigo, id_tipo_novedad, fecha_inicio) DO UPDATE SET fecha_fin=EXCLUDED.fecha_fin, dias=EXCLUDED.dias""",
                             (codigo, tipo, ini, fin, max(1, dias)))
                n_nov += 1
            bonif, transp = a_decimal(v("bonificacion")) or 0, a_decimal(v("transporte")) or 0
            conn.execute("""INSERT INTO liquidacion_mensual (codigo, anio, mes, bonificacion, auxilio_transporte) VALUES (%s,%s,%s,%s,%s)
                            ON CONFLICT (codigo, anio, mes) DO UPDATE SET bonificacion=EXCLUDED.bonificacion,
                              auxilio_transporte=EXCLUDED.auxilio_transporte""", (codigo, anio, mes, bonif, transp))
            n_liq += 1
        res.detalle.update({"novedades": n_nov, f"liquidaciones {mes:02d}/{anio}": n_liq})

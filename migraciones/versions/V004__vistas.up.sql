-- V004: vistas de consulta usadas por la aplicación y los reportes
CREATE VIEW v_empleado_detalle AS
SELECT e.codigo,
       e.apellidos,
       e.nombres,
       e.apellidos || ' ' || e.nombres AS nombre_completo,
       d.id_dependencia,
       d.nombre  AS dependencia,
       c.id_cargo,
       c.nombre  AS cargo,
       e.fecha_ingreso,
       ep.nombre AS eps,
       a.nombre  AS arl,
       p.nombre  AS pension,
       e.salario
FROM empleado e
JOIN cargo c          ON c.id_cargo = e.id_cargo
JOIN dependencia d    ON d.id_dependencia = c.id_dependencia
JOIN eps ep           ON ep.id_eps = e.id_eps
JOIN arl a            ON a.id_arl = e.id_arl
JOIN fondo_pension p  ON p.id_fondo_pension = e.id_fondo_pension;

CREATE VIEW v_novedad_detalle AS
SELECT n.id_novedad, n.codigo, v.nombre_completo, v.dependencia, v.cargo,
       t.nombre AS tipo, n.fecha_inicio, n.fecha_fin, n.dias,
       date_trunc('month', n.fecha_inicio)::date AS periodo
FROM novedad n
JOIN tipo_novedad t       ON t.id_tipo_novedad = n.id_tipo_novedad
JOIN v_empleado_detalle v ON v.codigo = n.codigo;

-- Los días trabajados se DERIVAN (30 - días de novedades del mes); no se almacenan (3FN).
CREATE VIEW v_liquidacion_detalle AS
SELECT l.id_liquidacion, l.codigo, v.nombre_completo, l.anio, l.mes,
       GREATEST(0, 30 - COALESCE((
           SELECT SUM(n.dias) FROM novedad n
           WHERE n.codigo = l.codigo
             AND n.fecha_inicio >= make_date(l.anio, l.mes, 1)
             AND n.fecha_inicio <  make_date(l.anio, l.mes, 1) + INTERVAL '1 month'), 0))::int AS dias_trabajados,
       l.bonificacion, l.auxilio_transporte
FROM liquidacion_mensual l
JOIN v_empleado_detalle v ON v.codigo = l.codigo;

CREATE VIEW v_frecuencia_dependencia AS
SELECT dependencia, COUNT(*)::int AS cantidad FROM v_empleado_detalle GROUP BY dependencia;

CREATE VIEW v_frecuencia_dependencia_cargo AS
SELECT dependencia, cargo, COUNT(*)::int AS cantidad FROM v_empleado_detalle GROUP BY dependencia, cargo;

CREATE VIEW v_frecuencia_eps AS
SELECT eps, COUNT(*)::int AS cantidad FROM v_empleado_detalle GROUP BY eps;

CREATE VIEW v_frecuencia_pension AS
SELECT pension, COUNT(*)::int AS cantidad FROM v_empleado_detalle GROUP BY pension;

CREATE VIEW v_frecuencia_eps_dependencia AS
SELECT dependencia, eps, COUNT(*)::int AS cantidad FROM v_empleado_detalle GROUP BY dependencia, eps;

CREATE VIEW v_frecuencia_pension_dependencia AS
SELECT dependencia, pension, COUNT(*)::int AS cantidad FROM v_empleado_detalle GROUP BY dependencia, pension;

CREATE VIEW v_pelicula_detalle AS
SELECT p.id_pelicula, p.titulo, p.anio_estreno,
       COUNT(pg.id_genero)::int AS num_generos,
       COALESCE(string_agg(g.nombre, ', ' ORDER BY g.nombre), '') AS generos
FROM pelicula p
LEFT JOIN pelicula_genero pg ON pg.id_pelicula = p.id_pelicula
LEFT JOIN genero g           ON g.id_genero = pg.id_genero
GROUP BY p.id_pelicula, p.titulo, p.anio_estreno;

CREATE VIEW v_pelicula_por_genero AS
SELECT g.nombre AS genero, p.id_pelicula, p.titulo, p.anio_estreno
FROM genero g
JOIN pelicula_genero pg ON pg.id_genero = g.id_genero
JOIN pelicula p         ON p.id_pelicula = pg.id_pelicula;

CREATE VIEW v_frecuencia_pelicula_genero AS
SELECT g.nombre AS genero, COUNT(pg.id_pelicula)::int AS cantidad
FROM genero g LEFT JOIN pelicula_genero pg ON pg.id_genero = g.id_genero
GROUP BY g.nombre;

CREATE VIEW v_libro_detalle AS
SELECT l.id_libro, l.titulo,
       COALESCE(string_agg(a.nombre, ' / ' ORDER BY la.orden), '') AS autores,
       ed.nombre AS editorial, l.codigo_idioma, l.num_paginas,
       l.calificacion_promedio, l.cantidad_calificaciones, l.cantidad_resenas,
       l.fecha_publicacion,
       EXTRACT(YEAR FROM l.fecha_publicacion)::int AS anio_publicacion,
       l.isbn, l.isbn13
FROM libro l
LEFT JOIN editorial ed   ON ed.id_editorial = l.id_editorial
LEFT JOIN libro_autor la ON la.id_libro = l.id_libro
LEFT JOIN autor a        ON a.id_autor = la.id_autor
GROUP BY l.id_libro, ed.nombre;

CREATE VIEW v_frecuencia_libro_anio AS
SELECT EXTRACT(YEAR FROM fecha_publicacion)::int AS anio, COUNT(*)::int AS cantidad
FROM libro WHERE fecha_publicacion IS NOT NULL GROUP BY 1;

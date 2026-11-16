-- V001: catálogos y tablas del módulo de NÓMINA (3FN)
CREATE TABLE dependencia (
    id_dependencia SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre         VARCHAR(80) NOT NULL UNIQUE
);

CREATE TABLE cargo (
    id_cargo       INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_dependencia SMALLINT NOT NULL REFERENCES dependencia (id_dependencia) ON UPDATE CASCADE ON DELETE RESTRICT,
    nombre         VARCHAR(100) NOT NULL,
    CONSTRAINT uq_cargo_dependencia UNIQUE (id_dependencia, nombre)
);

CREATE TABLE eps (
    id_eps SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre VARCHAR(80) NOT NULL UNIQUE
);

CREATE TABLE arl (
    id_arl SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre VARCHAR(80) NOT NULL UNIQUE
);

CREATE TABLE fondo_pension (
    id_fondo_pension SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre           VARCHAR(80) NOT NULL UNIQUE
);

CREATE TABLE empleado (
    codigo           INTEGER PRIMARY KEY CHECK (codigo > 0),
    apellidos        VARCHAR(80) NOT NULL,
    nombres          VARCHAR(80) NOT NULL,
    fecha_ingreso    DATE NOT NULL,
    salario          NUMERIC(12,2) NOT NULL CHECK (salario >= 0),
    id_cargo         INTEGER  NOT NULL REFERENCES cargo (id_cargo) ON UPDATE CASCADE ON DELETE RESTRICT,
    id_eps           SMALLINT NOT NULL REFERENCES eps (id_eps) ON UPDATE CASCADE ON DELETE RESTRICT,
    id_arl           SMALLINT NOT NULL REFERENCES arl (id_arl) ON UPDATE CASCADE ON DELETE RESTRICT,
    id_fondo_pension SMALLINT NOT NULL REFERENCES fondo_pension (id_fondo_pension) ON UPDATE CASCADE ON DELETE RESTRICT
);
CREATE INDEX ix_empleado_cargo ON empleado (id_cargo);

CREATE TABLE tipo_novedad (
    id_tipo_novedad SMALLINT PRIMARY KEY,
    nombre          VARCHAR(30) NOT NULL UNIQUE
);
INSERT INTO tipo_novedad (id_tipo_novedad, nombre) VALUES (1, 'INCAPACIDAD'), (2, 'VACACIONES');

CREATE TABLE novedad (
    id_novedad      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo          INTEGER NOT NULL REFERENCES empleado (codigo) ON UPDATE CASCADE ON DELETE CASCADE,
    id_tipo_novedad SMALLINT NOT NULL REFERENCES tipo_novedad (id_tipo_novedad),
    fecha_inicio    DATE NOT NULL,
    fecha_fin       DATE NOT NULL,
    dias            SMALLINT NOT NULL CHECK (dias > 0),
    CONSTRAINT ck_novedad_fechas CHECK (fecha_fin >= fecha_inicio),
    CONSTRAINT uq_novedad UNIQUE (codigo, id_tipo_novedad, fecha_inicio)
);
CREATE INDEX ix_novedad_inicio ON novedad (fecha_inicio);

CREATE TABLE liquidacion_mensual (
    id_liquidacion     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo             INTEGER NOT NULL REFERENCES empleado (codigo) ON UPDATE CASCADE ON DELETE CASCADE,
    anio               SMALLINT NOT NULL CHECK (anio BETWEEN 2000 AND 2100),
    mes                SMALLINT NOT NULL CHECK (mes BETWEEN 1 AND 12),
    bonificacion       NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (bonificacion >= 0),
    auxilio_transporte NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (auxilio_transporte >= 0),
    CONSTRAINT uq_liquidacion UNIQUE (codigo, anio, mes)
);

-- V003: usuarios, roles, auditoría y revocación de tokens JWT
CREATE TABLE rol (
    id_rol      SMALLINT PRIMARY KEY,
    nombre      VARCHAR(30) NOT NULL UNIQUE,
    descripcion VARCHAR(200) NOT NULL
);
INSERT INTO rol (id_rol, nombre, descripcion) VALUES
 (1, 'ADMIN',    'Administra usuarios, cargas, auditoría y todos los datos'),
 (2, 'ANALISTA', 'Consulta reportes, carga archivos y edita datos'),
 (3, 'CONSULTA', 'Solo consulta reportes y datos');

CREATE TABLE usuario (
    id_usuario        INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre_usuario    VARCHAR(40) NOT NULL,
    nombre_visible    VARCHAR(80) NOT NULL,
    password_hash     TEXT NOT NULL,
    id_rol            SMALLINT NOT NULL REFERENCES rol (id_rol),
    activo            BOOLEAN NOT NULL DEFAULT TRUE,
    intentos_fallidos SMALLINT NOT NULL DEFAULT 0,
    bloqueado_hasta   TIMESTAMPTZ,
    creado_en         TIMESTAMPTZ NOT NULL DEFAULT now(),
    ultimo_acceso     TIMESTAMPTZ,
    CONSTRAINT ck_usuario_nombre CHECK (nombre_usuario = lower(nombre_usuario) AND nombre_usuario ~ '^[a-z0-9._-]{3,40}$')
);
CREATE UNIQUE INDEX uq_usuario_nombre ON usuario (nombre_usuario);

CREATE TABLE auditoria (
    id_auditoria   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_usuario     INTEGER REFERENCES usuario (id_usuario) ON DELETE SET NULL,
    nombre_usuario VARCHAR(40),
    accion         VARCHAR(40) NOT NULL,
    entidad        VARCHAR(60),
    detalle        TEXT,
    ip             VARCHAR(45),
    fecha          TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_auditoria_fecha ON auditoria (fecha DESC);

CREATE TABLE token_revocado (
    jti       VARCHAR(64) PRIMARY KEY,
    expira_en TIMESTAMPTZ NOT NULL
);
CREATE INDEX ix_token_revocado_exp ON token_revocado (expira_en);

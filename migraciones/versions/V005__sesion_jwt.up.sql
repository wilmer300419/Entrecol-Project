-- V005: cada JWT emitido queda registrado como una SESIÓN ligada a un usuario.
-- El token firmado solo es válido si su sesión existe, pertenece al usuario, no está revocada ni vencida
-- y coincide con el navegador que la creó (control lógico adicional a la firma y a la expiración).
CREATE TABLE sesion_jwt (
    jti               VARCHAR(64) PRIMARY KEY,
    id_usuario        INTEGER NOT NULL REFERENCES usuario (id_usuario) ON UPDATE CASCADE ON DELETE CASCADE,
    emitido_en        TIMESTAMPTZ NOT NULL DEFAULT now(),
    expira_en         TIMESTAMPTZ NOT NULL,
    ip                VARCHAR(45),
    agente_hash       CHAR(64) NOT NULL,
    revocado_en       TIMESTAMPTZ,
    motivo_revocacion VARCHAR(40),
    CONSTRAINT ck_sesion_fechas     CHECK (expira_en > emitido_en),
    CONSTRAINT ck_sesion_revocacion CHECK ((revocado_en IS NULL) = (motivo_revocacion IS NULL))
);
CREATE INDEX ix_sesion_usuario ON sesion_jwt (id_usuario, revocado_en);
CREATE INDEX ix_sesion_expira  ON sesion_jwt (expira_en);

DROP TABLE token_revocado;      -- reemplazada: ahora se revoca marcando la propia sesión

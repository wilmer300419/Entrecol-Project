CREATE TABLE token_revocado (
    jti       VARCHAR(64) PRIMARY KEY,
    expira_en TIMESTAMPTZ NOT NULL
);
CREATE INDEX ix_token_revocado_exp ON token_revocado (expira_en);
INSERT INTO token_revocado (jti, expira_en) SELECT jti, expira_en FROM sesion_jwt WHERE revocado_en IS NOT NULL AND expira_en > now();
DROP TABLE sesion_jwt;

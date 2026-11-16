--
-- PostgreSQL database dump
--

-- Dumped from database version 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1)
-- Dumped by pg_dump version 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1)

--
-- Name: arl; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.arl (
    id_arl smallint NOT NULL,
    nombre character varying(80) NOT NULL
);

--
-- Name: arl_id_arl_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.arl ALTER COLUMN id_arl ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.arl_id_arl_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);

--
-- Name: auditoria; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.auditoria (
    id_auditoria bigint NOT NULL,
    id_usuario integer,
    nombre_usuario character varying(40),
    accion character varying(40) NOT NULL,
    entidad character varying(60),
    detalle text,
    ip character varying(45),
    fecha timestamp with time zone DEFAULT now() NOT NULL
);

--
-- Name: auditoria_id_auditoria_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.auditoria ALTER COLUMN id_auditoria ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.auditoria_id_auditoria_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);

--
-- Name: autor; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.autor (
    id_autor integer NOT NULL,
    nombre character varying(400) NOT NULL
);

--
-- Name: autor_id_autor_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.autor ALTER COLUMN id_autor ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.autor_id_autor_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);

--
-- Name: cargo; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cargo (
    id_cargo integer NOT NULL,
    id_dependencia smallint NOT NULL,
    nombre character varying(100) NOT NULL
);

--
-- Name: cargo_id_cargo_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.cargo ALTER COLUMN id_cargo ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.cargo_id_cargo_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);

--
-- Name: dependencia; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dependencia (
    id_dependencia smallint NOT NULL,
    nombre character varying(80) NOT NULL
);

--
-- Name: dependencia_id_dependencia_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.dependencia ALTER COLUMN id_dependencia ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.dependencia_id_dependencia_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);

--
-- Name: editorial; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.editorial (
    id_editorial integer NOT NULL,
    nombre character varying(300) NOT NULL
);

--
-- Name: editorial_id_editorial_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.editorial ALTER COLUMN id_editorial ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.editorial_id_editorial_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);

--
-- Name: empleado; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.empleado (
    codigo integer NOT NULL,
    apellidos character varying(80) NOT NULL,
    nombres character varying(80) NOT NULL,
    fecha_ingreso date NOT NULL,
    salario numeric(12,2) NOT NULL,
    id_cargo integer NOT NULL,
    id_eps smallint NOT NULL,
    id_arl smallint NOT NULL,
    id_fondo_pension smallint NOT NULL,
    CONSTRAINT empleado_codigo_check CHECK ((codigo > 0)),
    CONSTRAINT empleado_salario_check CHECK ((salario >= (0)::numeric))
);

--
-- Name: eps; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.eps (
    id_eps smallint NOT NULL,
    nombre character varying(80) NOT NULL
);

--
-- Name: eps_id_eps_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.eps ALTER COLUMN id_eps ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.eps_id_eps_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);

--
-- Name: fondo_pension; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.fondo_pension (
    id_fondo_pension smallint NOT NULL,
    nombre character varying(80) NOT NULL
);

--
-- Name: fondo_pension_id_fondo_pension_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.fondo_pension ALTER COLUMN id_fondo_pension ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.fondo_pension_id_fondo_pension_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);

--
-- Name: genero; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.genero (
    id_genero smallint NOT NULL,
    nombre character varying(40) NOT NULL
);

--
-- Name: genero_id_genero_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.genero ALTER COLUMN id_genero ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.genero_id_genero_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);

--
-- Name: idioma; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.idioma (
    codigo_idioma character varying(10) NOT NULL
);

--
-- Name: libro; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.libro (
    id_libro integer NOT NULL,
    titulo character varying(600) NOT NULL,
    isbn character varying(10),
    isbn13 character varying(13),
    codigo_idioma character varying(10),
    id_editorial integer,
    num_paginas integer,
    calificacion_promedio numeric(3,2) DEFAULT 0 NOT NULL,
    cantidad_calificaciones integer DEFAULT 0 NOT NULL,
    cantidad_resenas integer DEFAULT 0 NOT NULL,
    fecha_publicacion date,
    CONSTRAINT libro_calificacion_promedio_check CHECK (((calificacion_promedio >= (0)::numeric) AND (calificacion_promedio <= (5)::numeric))),
    CONSTRAINT libro_cantidad_calificaciones_check CHECK ((cantidad_calificaciones >= 0)),
    CONSTRAINT libro_cantidad_resenas_check CHECK ((cantidad_resenas >= 0)),
    CONSTRAINT libro_num_paginas_check CHECK ((num_paginas >= 0))
);

--
-- Name: libro_autor; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.libro_autor (
    id_libro integer NOT NULL,
    id_autor integer NOT NULL,
    orden smallint DEFAULT 1 NOT NULL,
    CONSTRAINT libro_autor_orden_check CHECK ((orden > 0))
);

--
-- Name: libro_id_libro_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.libro ALTER COLUMN id_libro ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.libro_id_libro_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);

--
-- Name: liquidacion_mensual; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.liquidacion_mensual (
    id_liquidacion bigint NOT NULL,
    codigo integer NOT NULL,
    anio smallint NOT NULL,
    mes smallint NOT NULL,
    bonificacion numeric(12,2) DEFAULT 0 NOT NULL,
    auxilio_transporte numeric(12,2) DEFAULT 0 NOT NULL,
    CONSTRAINT liquidacion_mensual_anio_check CHECK (((anio >= 2000) AND (anio <= 2100))),
    CONSTRAINT liquidacion_mensual_auxilio_transporte_check CHECK ((auxilio_transporte >= (0)::numeric)),
    CONSTRAINT liquidacion_mensual_bonificacion_check CHECK ((bonificacion >= (0)::numeric)),
    CONSTRAINT liquidacion_mensual_mes_check CHECK (((mes >= 1) AND (mes <= 12)))
);

--
-- Name: liquidacion_mensual_id_liquidacion_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.liquidacion_mensual ALTER COLUMN id_liquidacion ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.liquidacion_mensual_id_liquidacion_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);

--
-- Name: novedad; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.novedad (
    id_novedad bigint NOT NULL,
    codigo integer NOT NULL,
    id_tipo_novedad smallint NOT NULL,
    fecha_inicio date NOT NULL,
    fecha_fin date NOT NULL,
    dias smallint NOT NULL,
    CONSTRAINT ck_novedad_fechas CHECK ((fecha_fin >= fecha_inicio)),
    CONSTRAINT novedad_dias_check CHECK ((dias > 0))
);

--
-- Name: novedad_id_novedad_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.novedad ALTER COLUMN id_novedad ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.novedad_id_novedad_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);

--
-- Name: pelicula; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.pelicula (
    id_pelicula integer NOT NULL,
    titulo character varying(300) NOT NULL,
    anio_estreno smallint,
    CONSTRAINT pelicula_anio_estreno_check CHECK (((anio_estreno >= 1870) AND (anio_estreno <= 2100)))
);

--
-- Name: pelicula_genero; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.pelicula_genero (
    id_pelicula integer NOT NULL,
    id_genero smallint NOT NULL
);

--
-- Name: pelicula_id_pelicula_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.pelicula ALTER COLUMN id_pelicula ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.pelicula_id_pelicula_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);

--
-- Name: rol; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.rol (
    id_rol smallint NOT NULL,
    nombre character varying(30) NOT NULL,
    descripcion character varying(200) NOT NULL
);

--
-- Name: schema_migrations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.schema_migrations (
    version character varying(20) NOT NULL,
    nombre character varying(120) NOT NULL,
    checksum character(64) NOT NULL,
    aplicada_en timestamp with time zone DEFAULT now() NOT NULL
);

--
-- Name: sesion_jwt; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sesion_jwt (
    jti character varying(64) NOT NULL,
    id_usuario integer NOT NULL,
    emitido_en timestamp with time zone DEFAULT now() NOT NULL,
    expira_en timestamp with time zone NOT NULL,
    ip character varying(45),
    agente_hash character(64) NOT NULL,
    revocado_en timestamp with time zone,
    motivo_revocacion character varying(40),
    CONSTRAINT ck_sesion_fechas CHECK ((expira_en > emitido_en)),
    CONSTRAINT ck_sesion_revocacion CHECK (((revocado_en IS NULL) = (motivo_revocacion IS NULL)))
);

--
-- Name: tipo_novedad; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tipo_novedad (
    id_tipo_novedad smallint NOT NULL,
    nombre character varying(30) NOT NULL
);

--
-- Name: usuario; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.usuario (
    id_usuario integer NOT NULL,
    nombre_usuario character varying(40) NOT NULL,
    nombre_visible character varying(80) NOT NULL,
    password_hash text NOT NULL,
    id_rol smallint NOT NULL,
    activo boolean DEFAULT true NOT NULL,
    intentos_fallidos smallint DEFAULT 0 NOT NULL,
    bloqueado_hasta timestamp with time zone,
    creado_en timestamp with time zone DEFAULT now() NOT NULL,
    ultimo_acceso timestamp with time zone,
    CONSTRAINT ck_usuario_nombre CHECK ((((nombre_usuario)::text = lower((nombre_usuario)::text)) AND ((nombre_usuario)::text ~ '^[a-z0-9._-]{3,40}$'::text)))
);

--
-- Name: usuario_id_usuario_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.usuario ALTER COLUMN id_usuario ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.usuario_id_usuario_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);

--
-- Name: v_empleado_detalle; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_empleado_detalle AS
 SELECT e.codigo,
    e.apellidos,
    e.nombres,
    (((e.apellidos)::text || ' '::text) || (e.nombres)::text) AS nombre_completo,
    d.id_dependencia,
    d.nombre AS dependencia,
    c.id_cargo,
    c.nombre AS cargo,
    e.fecha_ingreso,
    ep.nombre AS eps,
    a.nombre AS arl,
    p.nombre AS pension,
    e.salario
   FROM (((((public.empleado e
     JOIN public.cargo c ON ((c.id_cargo = e.id_cargo)))
     JOIN public.dependencia d ON ((d.id_dependencia = c.id_dependencia)))
     JOIN public.eps ep ON ((ep.id_eps = e.id_eps)))
     JOIN public.arl a ON ((a.id_arl = e.id_arl)))
     JOIN public.fondo_pension p ON ((p.id_fondo_pension = e.id_fondo_pension)));

--
-- Name: v_frecuencia_dependencia; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_frecuencia_dependencia AS
 SELECT dependencia,
    (count(*))::integer AS cantidad
   FROM public.v_empleado_detalle
  GROUP BY dependencia;

--
-- Name: v_frecuencia_dependencia_cargo; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_frecuencia_dependencia_cargo AS
 SELECT dependencia,
    cargo,
    (count(*))::integer AS cantidad
   FROM public.v_empleado_detalle
  GROUP BY dependencia, cargo;

--
-- Name: v_frecuencia_eps; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_frecuencia_eps AS
 SELECT eps,
    (count(*))::integer AS cantidad
   FROM public.v_empleado_detalle
  GROUP BY eps;

--
-- Name: v_frecuencia_eps_dependencia; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_frecuencia_eps_dependencia AS
 SELECT dependencia,
    eps,
    (count(*))::integer AS cantidad
   FROM public.v_empleado_detalle
  GROUP BY dependencia, eps;

--
-- Name: v_frecuencia_libro_anio; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_frecuencia_libro_anio AS
 SELECT (EXTRACT(year FROM fecha_publicacion))::integer AS anio,
    (count(*))::integer AS cantidad
   FROM public.libro
  WHERE (fecha_publicacion IS NOT NULL)
  GROUP BY ((EXTRACT(year FROM fecha_publicacion))::integer);

--
-- Name: v_frecuencia_pelicula_genero; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_frecuencia_pelicula_genero AS
 SELECT g.nombre AS genero,
    (count(pg.id_pelicula))::integer AS cantidad
   FROM (public.genero g
     LEFT JOIN public.pelicula_genero pg ON ((pg.id_genero = g.id_genero)))
  GROUP BY g.nombre;

--
-- Name: v_frecuencia_pension; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_frecuencia_pension AS
 SELECT pension,
    (count(*))::integer AS cantidad
   FROM public.v_empleado_detalle
  GROUP BY pension;

--
-- Name: v_frecuencia_pension_dependencia; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_frecuencia_pension_dependencia AS
 SELECT dependencia,
    pension,
    (count(*))::integer AS cantidad
   FROM public.v_empleado_detalle
  GROUP BY dependencia, pension;

--
-- Name: v_libro_detalle; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_libro_detalle AS
SELECT
    NULL::integer AS id_libro,
    NULL::character varying(600) AS titulo,
    NULL::text AS autores,
    NULL::character varying(300) AS editorial,
    NULL::character varying(10) AS codigo_idioma,
    NULL::integer AS num_paginas,
    NULL::numeric(3,2) AS calificacion_promedio,
    NULL::integer AS cantidad_calificaciones,
    NULL::integer AS cantidad_resenas,
    NULL::date AS fecha_publicacion,
    NULL::integer AS anio_publicacion,
    NULL::character varying(10) AS isbn,
    NULL::character varying(13) AS isbn13;

--
-- Name: v_liquidacion_detalle; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_liquidacion_detalle AS
 SELECT l.id_liquidacion,
    l.codigo,
    v.nombre_completo,
    l.anio,
    l.mes,
    (GREATEST((0)::bigint, (30 - COALESCE(( SELECT sum(n.dias) AS sum
           FROM public.novedad n
          WHERE ((n.codigo = l.codigo) AND (n.fecha_inicio >= make_date((l.anio)::integer, (l.mes)::integer, 1)) AND (n.fecha_inicio < (make_date((l.anio)::integer, (l.mes)::integer, 1) + '1 mon'::interval)))), (0)::bigint))))::integer AS dias_trabajados,
    l.bonificacion,
    l.auxilio_transporte
   FROM (public.liquidacion_mensual l
     JOIN public.v_empleado_detalle v ON ((v.codigo = l.codigo)));

--
-- Name: v_novedad_detalle; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_novedad_detalle AS
 SELECT n.id_novedad,
    n.codigo,
    v.nombre_completo,
    v.dependencia,
    v.cargo,
    t.nombre AS tipo,
    n.fecha_inicio,
    n.fecha_fin,
    n.dias,
    (date_trunc('month'::text, (n.fecha_inicio)::timestamp with time zone))::date AS periodo
   FROM ((public.novedad n
     JOIN public.tipo_novedad t ON ((t.id_tipo_novedad = n.id_tipo_novedad)))
     JOIN public.v_empleado_detalle v ON ((v.codigo = n.codigo)));

--
-- Name: v_pelicula_detalle; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_pelicula_detalle AS
 SELECT p.id_pelicula,
    p.titulo,
    p.anio_estreno,
    (count(pg.id_genero))::integer AS num_generos,
    COALESCE(string_agg((g.nombre)::text, ', '::text ORDER BY (g.nombre)::text), ''::text) AS generos
   FROM ((public.pelicula p
     LEFT JOIN public.pelicula_genero pg ON ((pg.id_pelicula = p.id_pelicula)))
     LEFT JOIN public.genero g ON ((g.id_genero = pg.id_genero)))
  GROUP BY p.id_pelicula, p.titulo, p.anio_estreno;

--
-- Name: v_pelicula_por_genero; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_pelicula_por_genero AS
 SELECT g.nombre AS genero,
    p.id_pelicula,
    p.titulo,
    p.anio_estreno
   FROM ((public.genero g
     JOIN public.pelicula_genero pg ON ((pg.id_genero = g.id_genero)))
     JOIN public.pelicula p ON ((p.id_pelicula = pg.id_pelicula)));

--
-- Name: arl arl_nombre_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.arl
    ADD CONSTRAINT arl_nombre_key UNIQUE (nombre);

--
-- Name: arl arl_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.arl
    ADD CONSTRAINT arl_pkey PRIMARY KEY (id_arl);

--
-- Name: auditoria auditoria_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auditoria
    ADD CONSTRAINT auditoria_pkey PRIMARY KEY (id_auditoria);

--
-- Name: autor autor_nombre_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.autor
    ADD CONSTRAINT autor_nombre_key UNIQUE (nombre);

--
-- Name: autor autor_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.autor
    ADD CONSTRAINT autor_pkey PRIMARY KEY (id_autor);

--
-- Name: cargo cargo_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cargo
    ADD CONSTRAINT cargo_pkey PRIMARY KEY (id_cargo);

--
-- Name: dependencia dependencia_nombre_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dependencia
    ADD CONSTRAINT dependencia_nombre_key UNIQUE (nombre);

--
-- Name: dependencia dependencia_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dependencia
    ADD CONSTRAINT dependencia_pkey PRIMARY KEY (id_dependencia);

--
-- Name: editorial editorial_nombre_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.editorial
    ADD CONSTRAINT editorial_nombre_key UNIQUE (nombre);

--
-- Name: editorial editorial_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.editorial
    ADD CONSTRAINT editorial_pkey PRIMARY KEY (id_editorial);

--
-- Name: empleado empleado_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.empleado
    ADD CONSTRAINT empleado_pkey PRIMARY KEY (codigo);

--
-- Name: eps eps_nombre_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.eps
    ADD CONSTRAINT eps_nombre_key UNIQUE (nombre);

--
-- Name: eps eps_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.eps
    ADD CONSTRAINT eps_pkey PRIMARY KEY (id_eps);

--
-- Name: fondo_pension fondo_pension_nombre_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fondo_pension
    ADD CONSTRAINT fondo_pension_nombre_key UNIQUE (nombre);

--
-- Name: fondo_pension fondo_pension_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fondo_pension
    ADD CONSTRAINT fondo_pension_pkey PRIMARY KEY (id_fondo_pension);

--
-- Name: genero genero_nombre_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.genero
    ADD CONSTRAINT genero_nombre_key UNIQUE (nombre);

--
-- Name: genero genero_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.genero
    ADD CONSTRAINT genero_pkey PRIMARY KEY (id_genero);

--
-- Name: idioma idioma_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.idioma
    ADD CONSTRAINT idioma_pkey PRIMARY KEY (codigo_idioma);

--
-- Name: libro_autor libro_autor_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.libro_autor
    ADD CONSTRAINT libro_autor_pkey PRIMARY KEY (id_libro, id_autor);

--
-- Name: libro libro_isbn13_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.libro
    ADD CONSTRAINT libro_isbn13_key UNIQUE (isbn13);

--
-- Name: libro libro_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.libro
    ADD CONSTRAINT libro_pkey PRIMARY KEY (id_libro);

--
-- Name: liquidacion_mensual liquidacion_mensual_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.liquidacion_mensual
    ADD CONSTRAINT liquidacion_mensual_pkey PRIMARY KEY (id_liquidacion);

--
-- Name: novedad novedad_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.novedad
    ADD CONSTRAINT novedad_pkey PRIMARY KEY (id_novedad);

--
-- Name: pelicula_genero pelicula_genero_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pelicula_genero
    ADD CONSTRAINT pelicula_genero_pkey PRIMARY KEY (id_pelicula, id_genero);

--
-- Name: pelicula pelicula_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pelicula
    ADD CONSTRAINT pelicula_pkey PRIMARY KEY (id_pelicula);

--
-- Name: rol rol_nombre_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rol
    ADD CONSTRAINT rol_nombre_key UNIQUE (nombre);

--
-- Name: rol rol_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rol
    ADD CONSTRAINT rol_pkey PRIMARY KEY (id_rol);

--
-- Name: schema_migrations schema_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schema_migrations
    ADD CONSTRAINT schema_migrations_pkey PRIMARY KEY (version);

--
-- Name: sesion_jwt sesion_jwt_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sesion_jwt
    ADD CONSTRAINT sesion_jwt_pkey PRIMARY KEY (jti);

--
-- Name: tipo_novedad tipo_novedad_nombre_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tipo_novedad
    ADD CONSTRAINT tipo_novedad_nombre_key UNIQUE (nombre);

--
-- Name: tipo_novedad tipo_novedad_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tipo_novedad
    ADD CONSTRAINT tipo_novedad_pkey PRIMARY KEY (id_tipo_novedad);

--
-- Name: cargo uq_cargo_dependencia; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cargo
    ADD CONSTRAINT uq_cargo_dependencia UNIQUE (id_dependencia, nombre);

--
-- Name: liquidacion_mensual uq_liquidacion; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.liquidacion_mensual
    ADD CONSTRAINT uq_liquidacion UNIQUE (codigo, anio, mes);

--
-- Name: novedad uq_novedad; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.novedad
    ADD CONSTRAINT uq_novedad UNIQUE (codigo, id_tipo_novedad, fecha_inicio);

--
-- Name: usuario usuario_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT usuario_pkey PRIMARY KEY (id_usuario);

--
-- Name: ix_auditoria_fecha; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_auditoria_fecha ON public.auditoria USING btree (fecha DESC);

--
-- Name: ix_empleado_cargo; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_empleado_cargo ON public.empleado USING btree (id_cargo);

--
-- Name: ix_libro_autor_autor; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_libro_autor_autor ON public.libro_autor USING btree (id_autor);

--
-- Name: ix_libro_calificacion; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_libro_calificacion ON public.libro USING btree (calificacion_promedio DESC);

--
-- Name: ix_libro_fecha; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_libro_fecha ON public.libro USING btree (fecha_publicacion);

--
-- Name: ix_novedad_inicio; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_novedad_inicio ON public.novedad USING btree (fecha_inicio);

--
-- Name: ix_pelicula_anio; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_pelicula_anio ON public.pelicula USING btree (anio_estreno);

--
-- Name: ix_pelicula_genero_genero; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_pelicula_genero_genero ON public.pelicula_genero USING btree (id_genero);

--
-- Name: ix_sesion_expira; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sesion_expira ON public.sesion_jwt USING btree (expira_en);

--
-- Name: ix_sesion_usuario; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sesion_usuario ON public.sesion_jwt USING btree (id_usuario, revocado_en);

--
-- Name: uq_usuario_nombre; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_usuario_nombre ON public.usuario USING btree (nombre_usuario);

--
-- Name: v_libro_detalle _RETURN; Type: RULE; Schema: public; Owner: -
--

CREATE OR REPLACE VIEW public.v_libro_detalle AS
 SELECT l.id_libro,
    l.titulo,
    COALESCE(string_agg((a.nombre)::text, ' / '::text ORDER BY la.orden), ''::text) AS autores,
    ed.nombre AS editorial,
    l.codigo_idioma,
    l.num_paginas,
    l.calificacion_promedio,
    l.cantidad_calificaciones,
    l.cantidad_resenas,
    l.fecha_publicacion,
    (EXTRACT(year FROM l.fecha_publicacion))::integer AS anio_publicacion,
    l.isbn,
    l.isbn13
   FROM (((public.libro l
     LEFT JOIN public.editorial ed ON ((ed.id_editorial = l.id_editorial)))
     LEFT JOIN public.libro_autor la ON ((la.id_libro = l.id_libro)))
     LEFT JOIN public.autor a ON ((a.id_autor = la.id_autor)))
  GROUP BY l.id_libro, ed.nombre;

--
-- Name: auditoria auditoria_id_usuario_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auditoria
    ADD CONSTRAINT auditoria_id_usuario_fkey FOREIGN KEY (id_usuario) REFERENCES public.usuario(id_usuario) ON DELETE SET NULL;

--
-- Name: cargo cargo_id_dependencia_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cargo
    ADD CONSTRAINT cargo_id_dependencia_fkey FOREIGN KEY (id_dependencia) REFERENCES public.dependencia(id_dependencia) ON UPDATE CASCADE ON DELETE RESTRICT;

--
-- Name: empleado empleado_id_arl_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.empleado
    ADD CONSTRAINT empleado_id_arl_fkey FOREIGN KEY (id_arl) REFERENCES public.arl(id_arl) ON UPDATE CASCADE ON DELETE RESTRICT;

--
-- Name: empleado empleado_id_cargo_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.empleado
    ADD CONSTRAINT empleado_id_cargo_fkey FOREIGN KEY (id_cargo) REFERENCES public.cargo(id_cargo) ON UPDATE CASCADE ON DELETE RESTRICT;

--
-- Name: empleado empleado_id_eps_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.empleado
    ADD CONSTRAINT empleado_id_eps_fkey FOREIGN KEY (id_eps) REFERENCES public.eps(id_eps) ON UPDATE CASCADE ON DELETE RESTRICT;

--
-- Name: empleado empleado_id_fondo_pension_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.empleado
    ADD CONSTRAINT empleado_id_fondo_pension_fkey FOREIGN KEY (id_fondo_pension) REFERENCES public.fondo_pension(id_fondo_pension) ON UPDATE CASCADE ON DELETE RESTRICT;

--
-- Name: libro_autor libro_autor_id_autor_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.libro_autor
    ADD CONSTRAINT libro_autor_id_autor_fkey FOREIGN KEY (id_autor) REFERENCES public.autor(id_autor) ON UPDATE CASCADE ON DELETE RESTRICT;

--
-- Name: libro_autor libro_autor_id_libro_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.libro_autor
    ADD CONSTRAINT libro_autor_id_libro_fkey FOREIGN KEY (id_libro) REFERENCES public.libro(id_libro) ON UPDATE CASCADE ON DELETE CASCADE;

--
-- Name: libro libro_codigo_idioma_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.libro
    ADD CONSTRAINT libro_codigo_idioma_fkey FOREIGN KEY (codigo_idioma) REFERENCES public.idioma(codigo_idioma) ON UPDATE CASCADE ON DELETE RESTRICT;

--
-- Name: libro libro_id_editorial_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.libro
    ADD CONSTRAINT libro_id_editorial_fkey FOREIGN KEY (id_editorial) REFERENCES public.editorial(id_editorial) ON UPDATE CASCADE ON DELETE RESTRICT;

--
-- Name: liquidacion_mensual liquidacion_mensual_codigo_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.liquidacion_mensual
    ADD CONSTRAINT liquidacion_mensual_codigo_fkey FOREIGN KEY (codigo) REFERENCES public.empleado(codigo) ON UPDATE CASCADE ON DELETE CASCADE;

--
-- Name: novedad novedad_codigo_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.novedad
    ADD CONSTRAINT novedad_codigo_fkey FOREIGN KEY (codigo) REFERENCES public.empleado(codigo) ON UPDATE CASCADE ON DELETE CASCADE;

--
-- Name: novedad novedad_id_tipo_novedad_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.novedad
    ADD CONSTRAINT novedad_id_tipo_novedad_fkey FOREIGN KEY (id_tipo_novedad) REFERENCES public.tipo_novedad(id_tipo_novedad);

--
-- Name: pelicula_genero pelicula_genero_id_genero_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pelicula_genero
    ADD CONSTRAINT pelicula_genero_id_genero_fkey FOREIGN KEY (id_genero) REFERENCES public.genero(id_genero) ON UPDATE CASCADE ON DELETE RESTRICT;

--
-- Name: pelicula_genero pelicula_genero_id_pelicula_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pelicula_genero
    ADD CONSTRAINT pelicula_genero_id_pelicula_fkey FOREIGN KEY (id_pelicula) REFERENCES public.pelicula(id_pelicula) ON UPDATE CASCADE ON DELETE CASCADE;

--
-- Name: sesion_jwt sesion_jwt_id_usuario_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sesion_jwt
    ADD CONSTRAINT sesion_jwt_id_usuario_fkey FOREIGN KEY (id_usuario) REFERENCES public.usuario(id_usuario) ON UPDATE CASCADE ON DELETE CASCADE;

--
-- Name: usuario usuario_id_rol_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT usuario_id_rol_fkey FOREIGN KEY (id_rol) REFERENCES public.rol(id_rol);

--
-- PostgreSQL database dump complete
--


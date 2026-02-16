SET search_path TO public;

-- =====================================================
-- LIMPIEZA TOTAL
-- =====================================================
DROP TABLE IF EXISTS
    notificacion_destino,
    notificacion,
    qr,
    autorizacion_codigo,
    autorizacion_telefonica,
    acceso,
    visita,
    vehiculo,
    evento_cuenta,
    guardia,
    cuenta,
    miembro_vivienda,
    residente_vivienda,
    propietario_vivienda,
    persona_foto,
    persona,
    vivienda,
    bitacora
CASCADE;

-- =====================================================
-- VIVIENDA
-- =====================================================
CREATE TABLE vivienda (
    vivienda_pk SERIAL PRIMARY KEY,
    manzana VARCHAR(10) NOT NULL,
    villa VARCHAR(10) NOT NULL,
    estado VARCHAR(10) NOT NULL DEFAULT 'activo',
    eliminado BOOLEAN NOT NULL DEFAULT FALSE,
    motivo_eliminado TEXT,
    fecha_creado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usuario_creado VARCHAR(20) NOT NULL,
    fecha_actualizado TIMESTAMP,
    usuario_actualizado VARCHAR(20),
    CONSTRAINT uq_vivienda UNIQUE (manzana, villa),
    CONSTRAINT chk_vivienda_estado CHECK (estado IN ('activo','inactivo')),
    CONSTRAINT chk_vivienda_eliminado_estado
        CHECK (eliminado = FALSE OR estado = 'inactivo')
);

-- =====================================================
-- PERSONA
-- =====================================================
CREATE TABLE persona (
    persona_pk SERIAL PRIMARY KEY,
    identificacion VARCHAR(20) NOT NULL,
    tipo_identificacion VARCHAR(10) NOT NULL,
    nacionalidad VARCHAR(50) DEFAULT 'Ecuador',
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    fecha_nacimiento DATE NOT NULL,
    correo VARCHAR(100),
    celular VARCHAR(10),
    direccion_alternativa VARCHAR(120),
    estado VARCHAR(10) NOT NULL DEFAULT 'activo',
    eliminado BOOLEAN NOT NULL DEFAULT FALSE,
    motivo_eliminado TEXT,
    fecha_creado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usuario_creado VARCHAR(20) NOT NULL,
    fecha_actualizado TIMESTAMP,
    usuario_actualizado VARCHAR(20),
    CONSTRAINT chk_persona_estado CHECK (estado IN ('activo','inactivo')),
    CONSTRAINT chk_persona_eliminado_estado
        CHECK (eliminado = FALSE OR estado = 'inactivo')
);

CREATE UNIQUE INDEX uq_persona_identificacion_activa
ON persona (identificacion)
WHERE estado = 'activo' AND eliminado = FALSE;

-- =====================================================
-- PERSONA_FOTO
-- =====================================================
CREATE TABLE persona_foto (
    foto_pk SERIAL PRIMARY KEY,
    persona_titular_fk INTEGER NOT NULL REFERENCES persona(persona_pk),
    ruta_imagen TEXT NOT NULL,
    formato VARCHAR(10) NOT NULL,
    eliminado BOOLEAN NOT NULL DEFAULT FALSE,
    motivo_eliminado TEXT,
    fecha_creado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usuario_creado VARCHAR(20) NOT NULL,
    fecha_actualizado TIMESTAMP,
    usuario_actualizado VARCHAR(20)
);

-- =====================================================
-- PERSONA_FOTO
-- =====================================================
CREATE TABLE persona_foto (
    embedding_pk SERIAL PRIMARY KEY,
    persona_titular_fk INTEGER NOT NULL REFERENCES persona(persona_pk),
    rostro_embedding TEXT NOT NULL
);

-- =====================================================
-- PROPIETARIO_VIVIENDA
-- =====================================================
CREATE TABLE propietario_vivienda (
	propietario_vivienda_pk serial4 NOT NULL,
	vivienda_propiedad_fk int4 NOT NULL,
	persona_propietario_fk int4 NOT NULL,
	estado varchar(10) DEFAULT 'activo'::character varying NOT NULL,
	eliminado bool DEFAULT false NOT NULL,
	motivo_eliminado text NULL,
	motivo_inactivo text NULL,
	fecha_desde date DEFAULT CURRENT_DATE NULL,
	fecha_hasta date NULL,
	motivo text NULL,
	fecha_creado timestamp DEFAULT CURRENT_TIMESTAMP NULL,
	usuario_creado varchar(20) NOT NULL,
	fecha_actualizado timestamp NULL,
	usuario_actualizado varchar(20) NULL,
	tipo_propietario varchar(20) DEFAULT 'titular'::character varying NOT NULL,
	CONSTRAINT chk_propietario_eliminado_estado CHECK (((eliminado = false) OR ((estado)::text = 'inactivo'::text))),
	CONSTRAINT chk_propietario_estado CHECK (((estado)::text = ANY ((ARRAY['activo'::character varying, 'inactivo'::character varying])::text[]))),
	CONSTRAINT chk_propietario_tipo CHECK (((tipo_propietario)::text = ANY ((ARRAY['titular'::character varying, 'conyuge'::character varying, 'copropietario'::character varying, 'hijo'::character varying])::text[]))),
	CONSTRAINT propietario_vivienda_pkey PRIMARY KEY (propietario_vivienda_pk),
	CONSTRAINT propietario_vivienda_persona_propietario_fk_fkey FOREIGN KEY (persona_propietario_fk) REFERENCES public.persona(persona_pk),
	CONSTRAINT propietario_vivienda_vivienda_propiedad_fk_fkey FOREIGN KEY (vivienda_propiedad_fk) REFERENCES public.vivienda(vivienda_pk)
);
CREATE UNIQUE INDEX uq_propietario_persona_unica_por_casa ON public.propietario_vivienda USING btree (vivienda_propiedad_fk, persona_propietario_fk) WHERE (((estado)::text = 'activo'::text) AND (eliminado = false));
CREATE UNIQUE INDEX uq_propietario_titular_unico ON public.propietario_vivienda USING btree (vivienda_propiedad_fk) WHERE (((tipo_propietario)::text = 'titular'::text) AND ((estado)::text = 'activo'::text) AND (eliminado = false));



-- =====================================================
-- RESIDENTE_VIVIENDA
-- =====================================================
CREATE TABLE residente_vivienda (
    residente_vivienda_pk SERIAL PRIMARY KEY,
    vivienda_reside_fk INTEGER NOT NULL REFERENCES vivienda(vivienda_pk),
    persona_residente_fk INTEGER NOT NULL REFERENCES persona(persona_pk),
    estado VARCHAR(10) NOT NULL DEFAULT 'activo',
    eliminado BOOLEAN NOT NULL DEFAULT FALSE,
    motivo_eliminado TEXT,
    doc_autorizacion_pdf TEXT,
    fecha_desde DATE DEFAULT CURRENT_DATE,
    fecha_hasta DATE,
    motivo TEXT,
    fecha_creado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usuario_creado VARCHAR(20) NOT NULL,
    fecha_actualizado TIMESTAMP,
    usuario_actualizado VARCHAR(20),
    CONSTRAINT chk_residente_estado CHECK (estado IN ('activo','inactivo')),
    CONSTRAINT chk_residente_activo_sin_fecha_hasta
        CHECK (estado <> 'activo' OR fecha_hasta IS NULL),
    CONSTRAINT chk_residente_eliminado_estado
        CHECK (eliminado = FALSE OR estado = 'inactivo')
);

CREATE UNIQUE INDEX uq_residente_activo_vivienda
ON residente_vivienda (vivienda_reside_fk)
WHERE estado = 'activo' AND eliminado = FALSE;

-- =====================================================
-- MIEMBRO_VIVIENDA
-- =====================================================
CREATE TABLE miembro_vivienda (
    miembro_vivienda_pk SERIAL PRIMARY KEY,
    vivienda_familia_fk INTEGER NOT NULL REFERENCES vivienda(vivienda_pk),
    persona_residente_fk INTEGER NOT NULL REFERENCES persona(persona_pk),
    persona_miembro_fk INTEGER NOT NULL REFERENCES persona(persona_pk),
    parentesco VARCHAR(20) NOT NULL,
    parentesco_otro_desc VARCHAR(100),
    estado VARCHAR(10) NOT NULL DEFAULT 'activo',
    eliminado BOOLEAN NOT NULL DEFAULT FALSE,
    motivo_eliminado TEXT,
    fecha_creado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usuario_creado VARCHAR(20) NOT NULL,
    fecha_actualizado TIMESTAMP,
    usuario_actualizado VARCHAR(20),
    CONSTRAINT chk_miembro_vivienda_estado CHECK (estado IN ('activo','inactivo')),
    CONSTRAINT chk_miembro_vivienda_parentesco CHECK (
        parentesco IN ('padre','madre','esposo','esposa','hijo','hija','otro')
    ),
    CONSTRAINT chk_miembro_vivienda_parentesco_otro CHECK (
        parentesco <> 'otro'
        OR (parentesco_otro_desc IS NOT NULL
            AND length(trim(parentesco_otro_desc)) > 0)
    ),
    CONSTRAINT chk_miembro_vivienda_eliminado_estado
        CHECK (eliminado = FALSE OR estado = 'inactivo')
);

CREATE UNIQUE INDEX uq_miembro_vivienda_activo_unico
ON miembro_vivienda (vivienda_familia_fk, persona_miembro_fk)
WHERE estado = 'activo' AND eliminado = FALSE;

CREATE UNIQUE INDEX uq_miembro_vivienda_parentesco_unico
ON miembro_vivienda (vivienda_familia_fk, parentesco)
WHERE parentesco IN ('padre','madre','esposo','esposa')
  AND estado = 'activo'
  AND eliminado = FALSE;

-- =====================================================
-- CUENTA
-- =====================================================
CREATE TABLE cuenta (
    cuenta_pk SERIAL PRIMARY KEY,
    persona_titular_fk INTEGER NOT NULL REFERENCES persona(persona_pk),
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash TEXT,
    firebase_uid VARCHAR(128) NOT NULL UNIQUE,
    estado VARCHAR(10) NOT NULL DEFAULT 'activo',
    eliminado BOOLEAN NOT NULL DEFAULT FALSE,
    motivo_eliminado TEXT,
    ultimo_login TIMESTAMP,
    fecha_creado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usuario_creado VARCHAR(20) NOT NULL,
    fecha_actualizado TIMESTAMP,
    usuario_actualizado VARCHAR(20),
    CONSTRAINT chk_cuenta_estado CHECK (estado IN ('activo','inactivo')),
    CONSTRAINT chk_cuenta_eliminado_estado
        CHECK (eliminado = FALSE OR estado = 'inactivo')
);

-- =====================================================
-- GUARDIA
-- =====================================================
CREATE TABLE guardia (
    guardia_pk SERIAL PRIMARY KEY,
    persona_guardia_fk INTEGER NOT NULL REFERENCES persona(persona_pk),
    codigo_guardia VARCHAR(20) NOT NULL UNIQUE,
    estado VARCHAR(10) NOT NULL DEFAULT 'activo',
    eliminado BOOLEAN NOT NULL DEFAULT FALSE,
    motivo_eliminado TEXT,
    fecha_creado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usuario_creado VARCHAR(20) NOT NULL,
    fecha_actualizado TIMESTAMP,
    usuario_actualizado VARCHAR(20),
    CONSTRAINT chk_guardia_estado CHECK (estado IN ('activo','inactivo')),
    CONSTRAINT chk_guardia_eliminado_estado
        CHECK (eliminado = FALSE OR estado = 'inactivo')
);

CREATE UNIQUE INDEX uq_guardia_persona_activa
ON guardia (persona_guardia_fk)
WHERE estado = 'activo' AND eliminado = FALSE;

-- =====================================================
-- EVENTO_CUENTA
-- =====================================================
CREATE TABLE evento_cuenta (
    evento_cuenta_pk SERIAL PRIMARY KEY,
    cuenta_afectada_fk INTEGER NOT NULL REFERENCES cuenta(cuenta_pk),
    tipo_evento VARCHAR(30) NOT NULL,
    motivo TEXT,
    persona_actor_fk INTEGER REFERENCES persona(persona_pk),
    eliminado BOOLEAN NOT NULL DEFAULT FALSE,
    motivo_eliminado TEXT,
    fecha_creado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usuario_creado VARCHAR(20) NOT NULL,
    fecha_actualizado TIMESTAMP,
    usuario_actualizado VARCHAR(20),
    CONSTRAINT chk_evento_cuenta_tipo CHECK (
        tipo_evento IN (
            'login_exitoso','login_fallido','logout','sesion_expirada',
            'cuenta_bloqueada','cuenta_desbloqueada','intentos_excedidos',
            'credenciales_invalidas','actividad_sospechosa',
            'cuenta_creada','cuenta_activada','cuenta_inactivada',
            'cuenta_eliminada','cuenta_reactivada',
            'password_cambiado','password_restablecido','password_expirado',
            'cambio_username','cambio_rol','asignacion_guardia','revocacion_guardia'
        )
    )
);

-- =====================================================
-- VEHICULO
-- =====================================================
CREATE TABLE vehiculo (
    vehiculo_pk SERIAL PRIMARY KEY,
    persona_residente_fk INTEGER NOT NULL REFERENCES persona(persona_pk),
    placa VARCHAR(10) NOT NULL UNIQUE,
    estado VARCHAR(10) NOT NULL DEFAULT 'activo',
    eliminado BOOLEAN NOT NULL DEFAULT FALSE,
    motivo_eliminado TEXT,
    fecha_creado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usuario_creado VARCHAR(20) NOT NULL,
    fecha_actualizado TIMESTAMP,
    usuario_actualizado VARCHAR(20),
    CONSTRAINT chk_vehiculo_estado CHECK (estado IN ('activo','inactivo')),
    CONSTRAINT chk_vehiculo_eliminado_estado
        CHECK (eliminado = FALSE OR estado = 'inactivo')
);

-- =====================================================
-- VISITA
-- =====================================================
CREATE TABLE visita (
    visita_pk SERIAL PRIMARY KEY,
    vivienda_visita_fk INTEGER NOT NULL REFERENCES vivienda(vivienda_pk),
    identificacion VARCHAR(20),
    nombres VARCHAR(100),
    apellidos VARCHAR(100),
    eliminado BOOLEAN NOT NULL DEFAULT FALSE,
    motivo_eliminado TEXT,
    fecha_creado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usuario_creado VARCHAR(20) NOT NULL,
    fecha_actualizado TIMESTAMP,
    usuario_actualizado VARCHAR(20)
);

-- =====================================================
-- ACCESO
-- =====================================================
CREATE TABLE acceso (
    acceso_pk SERIAL PRIMARY KEY,
    tipo VARCHAR(30) NOT NULL,
    vivienda_visita_fk INTEGER NOT NULL REFERENCES vivienda(vivienda_pk),
    resultado VARCHAR(30) NOT NULL,
    motivo VARCHAR(30),
    persona_guardia_fk INTEGER REFERENCES persona(persona_pk),
    persona_residente_autoriza_fk INTEGER REFERENCES persona(persona_pk),
    visita_ingreso_fk INTEGER REFERENCES visita(visita_pk),
    vehiculo_ingreso_fk INTEGER REFERENCES vehiculo(vehiculo_pk),
    placa_detectada VARCHAR(10),
    biometria_ok BOOLEAN,
    placa_ok BOOLEAN,
    intentos INTEGER NOT NULL DEFAULT 0,
    observacion TEXT,
    eliminado BOOLEAN NOT NULL DEFAULT FALSE,
    motivo_eliminado TEXT,
    fecha_creado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usuario_creado VARCHAR(20) NOT NULL,
    fecha_actualizado TIMESTAMP,
    usuario_actualizado VARCHAR(20),
    CONSTRAINT chk_acceso_tipo CHECK (
        tipo IN (
            'qr_residente','qr_visita','visita_sin_qr',
            'visita_peatonal','residente_automatico','manual_guardia'
        )
    ),
    CONSTRAINT chk_acceso_resultado CHECK (
        resultado IN (
            'autorizado','rechazado','no_autorizado','fallo_biometrico',
            'fallo_placa','codigo_expirado','codigo_invalido',
            'cuenta_bloqueada','error_sistema','cancelado'
        )
    )
);

-- =====================================================
-- AUTORIZACION_TELEFONICA
-- =====================================================
CREATE TABLE autorizacion_telefonica (
    autorizacion_tel_pk SERIAL PRIMARY KEY,
    acceso_ingreso_fk INTEGER NOT NULL REFERENCES acceso(acceso_pk),
    telefono VARCHAR(15),
    respuesta VARCHAR(20),
    numero_intentos INTEGER,
    hora_inicio TIMESTAMP,
    hora_fin TIMESTAMP,
    eliminado BOOLEAN NOT NULL DEFAULT FALSE,
    motivo_eliminado TEXT,
    fecha_creado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usuario_creado VARCHAR(20) NOT NULL,
    fecha_actualizado TIMESTAMP,
    usuario_actualizado VARCHAR(20),
    CONSTRAINT chk_respuesta_tel CHECK (
        respuesta IN (
            'aceptado','rechazado','sin_respuesta',
            'numero_invalido','fallo_proveedor'
        )
    )
);

-- =====================================================
-- AUTORIZACION_CODIGO
-- =====================================================
CREATE TABLE autorizacion_codigo (
    autorizacion_codigo_pk SERIAL PRIMARY KEY,
    persona_residente_fk INTEGER NOT NULL REFERENCES persona(persona_pk),
    codigo_hash TEXT NOT NULL,
    hora_generado TIMESTAMP NOT NULL,
    hora_expira TIMESTAMP NOT NULL,
    hora_usado TIMESTAMP,
    estado VARCHAR(20) NOT NULL,
    eliminado BOOLEAN NOT NULL DEFAULT FALSE,
    motivo_eliminado TEXT,
    fecha_creado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usuario_creado VARCHAR(20) NOT NULL,
    fecha_actualizado TIMESTAMP,
    usuario_actualizado VARCHAR(20),
    CONSTRAINT chk_estado_codigo CHECK (
        estado IN ('vigente','expirado','usado','anulado')
    )
);

-- =====================================================
-- QR
-- =====================================================
CREATE TABLE qr (
    qr_pk SERIAL PRIMARY KEY,
    cuenta_autoriza_fk INTEGER NOT NULL REFERENCES cuenta(cuenta_pk),
    vivienda_visita_fk INTEGER NOT NULL REFERENCES vivienda(vivienda_pk),
    visita_ingreso_fk INTEGER REFERENCES visita(visita_pk),
    hora_inicio_vigencia TIMESTAMP NOT NULL,
    hora_fin_vigencia TIMESTAMP NOT NULL,
    hora_usado TIMESTAMP,
    estado VARCHAR(20) NOT NULL,
    token TEXT NOT NULL,
    eliminado BOOLEAN NOT NULL DEFAULT FALSE,
    motivo_eliminado TEXT,
    fecha_creado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usuario_creado VARCHAR(20) NOT NULL,
    fecha_actualizado TIMESTAMP,
    usuario_actualizado VARCHAR(20),
    CONSTRAINT chk_estado_qr CHECK (
        estado IN ('vigente','expirado','usado','anulado')
    )
);

-- =====================================================
-- NOTIFICACION
-- =====================================================
CREATE TABLE notificacion (
    notificacion_pk SERIAL PRIMARY KEY,
    tipo VARCHAR(30) NOT NULL,
    mensaje TEXT NOT NULL,
    persona_emisor_fk INTEGER REFERENCES persona(persona_pk),
    eliminado BOOLEAN NOT NULL DEFAULT FALSE,
    motivo_eliminado TEXT,
    fecha_creado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usuario_creado VARCHAR(20) NOT NULL,
    fecha_actualizado TIMESTAMP,
    usuario_actualizado VARCHAR(20),
    CONSTRAINT chk_notificacion_tipo CHECK (
        tipo IN (
            'solicitud_autorizacion','ingreso_autorizado','ingreso_rechazado',
            'intento_fallido','qr_generado','qr_expirado',
            'codigo_generado','codigo_usado','alerta_seguridad',
            'cuenta_bloqueada','acceso_manual',
            'alta_usuario','baja_usuario',
            'cambio_estado','actualizacion_datos'
        )
    )
);

-- =====================================================
-- NOTIFICACION_DESTINO
-- =====================================================
CREATE TABLE notificacion_destino (
    notificacion_destino_pk SERIAL PRIMARY KEY,
    notificacion_envio_fk INTEGER NOT NULL REFERENCES notificacion(notificacion_pk),
    persona_receptor_fk INTEGER NOT NULL REFERENCES persona(persona_pk),
    entregada BOOLEAN NOT NULL DEFAULT FALSE,
    hora_entregado TIMESTAMP,
    error TEXT,
    eliminado BOOLEAN NOT NULL DEFAULT FALSE,
    motivo_eliminado TEXT,
    fecha_creado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usuario_creado VARCHAR(20) NOT NULL,
    fecha_actualizado TIMESTAMP,
    usuario_actualizado VARCHAR(20)
);

-- =====================================================
-- BITACORA
-- =====================================================
CREATE TABLE bitacora (
    bitacora_pk SERIAL PRIMARY KEY,
    entidad VARCHAR(50) NOT NULL,
    entidad_id VARCHAR(50) NOT NULL,
    operacion VARCHAR(20) NOT NULL,
    persona_actor_fk INTEGER REFERENCES persona(persona_pk),
    valor_anterior JSONB,
    valor_nuevo JSONB,
    descripcion TEXT
);
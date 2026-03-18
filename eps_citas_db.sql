-- ════════════════════════════════════════════════════════════════
--  EPS CITAS v2.0 — Script completo de Base de Datos
--  Incluye: sistema de usuarios, roles, médicos, notas clínicas
--
--  ⚠ IMPORTANTE:
--    · Instalación nueva  → ejecuta TODO el archivo de corrido
--    · Ya tenías v1.0     → lee la sección MIGRACIÓN al final
--
--  Terminal: mysql -u root -p < eps_citas_db.sql
-- ════════════════════════════════════════════════════════════════

-- ── 1. Base de datos ─────────────────────────────────────────────
CREATE DATABASE IF NOT EXISTS eps_citas
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE eps_citas;

SET FOREIGN_KEY_CHECKS = 0;


-- ════════════════════════════════════════════════════════════════
--  TABLAS  (orden respeta FK: usuarios → pacientes/medicos → citas → notas)
-- ════════════════════════════════════════════════════════════════

-- ── 2. usuarios ──────────────────────────────────────────────────
--  Concentra el login de los 3 roles.
--  password_hash: SIEMPRE guardado con bcrypt, nunca en texto plano.
-- ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS usuarios (
  id             INT AUTO_INCREMENT  PRIMARY KEY,
  documento      VARCHAR(15)         NOT NULL UNIQUE,
  password_hash  VARCHAR(255)        NOT NULL,
  rol            ENUM('paciente','medico','admin') NOT NULL DEFAULT 'paciente',
  activo         TINYINT(1)          NOT NULL DEFAULT 1,
  creado_en      TIMESTAMP           DEFAULT CURRENT_TIMESTAMP,
  actualizado_en TIMESTAMP           DEFAULT CURRENT_TIMESTAMP
                                     ON UPDATE CURRENT_TIMESTAMP,

  INDEX idx_usu_documento (documento),
  INDEX idx_usu_rol       (rol)
);


-- ── 3. pacientes ─────────────────────────────────────────────────
--  Perfil extendido; se crea junto con el usuario en el registro.
-- ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS pacientes (
  id          INT AUTO_INCREMENT  PRIMARY KEY,
  usuario_id  INT                 NOT NULL UNIQUE,
  documento   VARCHAR(15)         NOT NULL UNIQUE,
  nombre      VARCHAR(80)         NOT NULL,
  apellido    VARCHAR(80)         NOT NULL,
  telefono    VARCHAR(20)         NOT NULL,
  correo      VARCHAR(100)        NOT NULL,
  eps         VARCHAR(100)        NOT NULL,
  creado_en   TIMESTAMP           DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT fk_pac_usuario
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
    ON DELETE CASCADE ON UPDATE CASCADE,

  INDEX idx_pac_documento (documento),
  INDEX idx_pac_usuario   (usuario_id)
);


-- ── 4. medicos ───────────────────────────────────────────────────
--  Creado por el administrador.
--  direccion_eps: sede habitual de atención.
-- ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS medicos (
  id             INT AUTO_INCREMENT  PRIMARY KEY,
  usuario_id     INT                 NOT NULL UNIQUE,
  nombre         VARCHAR(80)         NOT NULL,
  apellido       VARCHAR(80)         NOT NULL,
  especialidad   ENUM('General','Odontología','Especialista') NOT NULL,
  telefono       VARCHAR(20)         NOT NULL,
  correo         VARCHAR(100)        NOT NULL,
  direccion_eps  VARCHAR(150)        NOT NULL,
  activo         TINYINT(1)          NOT NULL DEFAULT 1,
  creado_en      TIMESTAMP           DEFAULT CURRENT_TIMESTAMP,
  actualizado_en TIMESTAMP           DEFAULT CURRENT_TIMESTAMP
                                     ON UPDATE CURRENT_TIMESTAMP,

  CONSTRAINT fk_med_usuario
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
    ON DELETE CASCADE ON UPDATE CASCADE,

  INDEX idx_med_especialidad (especialidad),
  INDEX idx_med_activo       (activo)
);


-- ── 5. citas ─────────────────────────────────────────────────────
--  paciente_id y medico_id reemplazan los campos de texto anteriores.
--  estado: ciclo de vida de la cita.
-- ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS citas (
  id             INT AUTO_INCREMENT  PRIMARY KEY,
  paciente_id    INT                 NOT NULL,
  medico_id      INT                 NOT NULL,
  tipo_cita      ENUM('General','Odontología','Especialista') NOT NULL,
  fecha          DATE                NOT NULL,
  hora           TIME                NOT NULL,
  direccion_eps  VARCHAR(150)        NOT NULL,
  estado         ENUM('Pendiente','Atendida','Cancelada','No asistió')
                                     NOT NULL DEFAULT 'Pendiente',
  creado_en      TIMESTAMP           DEFAULT CURRENT_TIMESTAMP,
  actualizado_en TIMESTAMP           DEFAULT CURRENT_TIMESTAMP
                                     ON UPDATE CURRENT_TIMESTAMP,

  CONSTRAINT fk_cita_paciente
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id)
    ON DELETE CASCADE ON UPDATE CASCADE,

  CONSTRAINT fk_cita_medico
    FOREIGN KEY (medico_id) REFERENCES medicos(id)
    ON DELETE RESTRICT ON UPDATE CASCADE,

  INDEX idx_cita_paciente (paciente_id),
  INDEX idx_cita_medico   (medico_id),
  INDEX idx_cita_fecha    (fecha),
  INDEX idx_cita_estado   (estado)
);


-- ── 6. notas_cita ────────────────────────────────────────────────
--  Notas clínicas que agrega el médico a cada cita.
--  Una cita puede acumular varias notas (historial de observaciones).
-- ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS notas_cita (
  id         INT AUTO_INCREMENT  PRIMARY KEY,
  cita_id    INT                 NOT NULL,
  medico_id  INT                 NOT NULL,
  nota       TEXT                NOT NULL,
  creado_en  TIMESTAMP           DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT fk_nota_cita
    FOREIGN KEY (cita_id)   REFERENCES citas(id)
    ON DELETE CASCADE ON UPDATE CASCADE,

  CONSTRAINT fk_nota_medico
    FOREIGN KEY (medico_id) REFERENCES medicos(id)
    ON DELETE RESTRICT ON UPDATE CASCADE,

  INDEX idx_nota_cita   (cita_id),
  INDEX idx_nota_medico (medico_id)
);

SET FOREIGN_KEY_CHECKS = 1;


-- ════════════════════════════════════════════════════════════════
--  DATOS INICIALES OBLIGATORIOS
-- ════════════════════════════════════════════════════════════════

-- ── Administrador por defecto ─────────────────────────────────────
--
--  Documento : 0000000000
--  Contraseña: Admin2024*
--
--  El hash fue generado con:
--    python -c "import bcrypt; print(bcrypt.hashpw(b'Admin2024*', bcrypt.gensalt(12)).decode())"
--
--  ⚠ CAMBIA LA CONTRASEÑA tras el primer login desde el panel admin.
-- ─────────────────────────────────────────────────────────────────
INSERT INTO usuarios (documento, password_hash, rol, activo)
VALUES (
  '0000000000',
  '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMaZoY1YkADJYrJG4zFGH3tVzW',
  'admin',
  1
)
ON DUPLICATE KEY UPDATE documento = documento;


-- ════════════════════════════════════════════════════════════════
--  DATOS DE PRUEBA — comentar / eliminar en producción
--  Contraseña para todos: Test1234*
-- ════════════════════════════════════════════════════════════════

SET @pwd = '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC.CLnNxZmtYjGh0dOfa';

-- Usuarios --------------------------------------------------------
INSERT INTO usuarios (documento, password_hash, rol) VALUES
('1012345678', @pwd, 'paciente'),
('987654321',  @pwd, 'paciente'),
('1122334455', @pwd, 'paciente'),
('2000000001', @pwd, 'medico'),
('2000000002', @pwd, 'medico'),
('2000000003', @pwd, 'medico')
ON DUPLICATE KEY UPDATE documento = documento;

-- Pacientes -------------------------------------------------------
INSERT INTO pacientes (usuario_id, documento, nombre, apellido, telefono, correo, eps)
SELECT id, '1012345678', 'María José',    'Rodríguez García', '3001234567', 'maria@correo.com',  'Sura EPS'
FROM usuarios WHERE documento = '1012345678'
ON DUPLICATE KEY UPDATE documento = documento;

INSERT INTO pacientes (usuario_id, documento, nombre, apellido, telefono, correo, eps)
SELECT id, '987654321', 'Carlos Andrés', 'Martínez López', '3109876543', 'carlos@correo.com', 'Nueva EPS'
FROM usuarios WHERE documento = '987654321'
ON DUPLICATE KEY UPDATE documento = documento;

INSERT INTO pacientes (usuario_id, documento, nombre, apellido, telefono, correo, eps)
SELECT id, '1122334455', 'Ana Sofía', 'Torres Vargas', '3201122334', 'ana@correo.com', 'Sanitas EPS'
FROM usuarios WHERE documento = '1122334455'
ON DUPLICATE KEY UPDATE documento = documento;

-- Médicos ---------------------------------------------------------
INSERT INTO medicos (usuario_id, nombre, apellido, especialidad, telefono, correo, direccion_eps)
SELECT id, 'Juan',   'Pérez',  'General',      '3011111111', 'jperez@eps.com',   'Calle 45 # 12-30, Bogotá'
FROM usuarios WHERE documento = '2000000001'
ON DUPLICATE KEY UPDATE nombre = nombre;

INSERT INTO medicos (usuario_id, nombre, apellido, especialidad, telefono, correo, direccion_eps)
SELECT id, 'Laura',  'Gómez',  'Odontología',  '3022222222', 'lgomez@eps.com',   'Av. 68 # 23-15, Bogotá'
FROM usuarios WHERE documento = '2000000002'
ON DUPLICATE KEY UPDATE nombre = nombre;

INSERT INTO medicos (usuario_id, nombre, apellido, especialidad, telefono, correo, direccion_eps)
SELECT id, 'Hernán', 'Suárez', 'Especialista', '3033333333', 'hsuarez@eps.com',  'Cra. 7 # 45-10, Bogotá'
FROM usuarios WHERE documento = '2000000003'
ON DUPLICATE KEY UPDATE nombre = nombre;

-- Citas -----------------------------------------------------------
INSERT INTO citas (paciente_id, medico_id, tipo_cita, fecha, hora, direccion_eps, estado)
SELECT p.id, m.id, 'General', '2026-07-10', '09:00:00', 'Calle 45 # 12-30, Bogotá', 'Pendiente'
FROM pacientes p JOIN medicos m ON m.correo = 'jperez@eps.com'
WHERE p.documento = '1012345678' LIMIT 1;

INSERT INTO citas (paciente_id, medico_id, tipo_cita, fecha, hora, direccion_eps, estado)
SELECT p.id, m.id, 'Odontología', '2026-07-15', '14:30:00', 'Av. 68 # 23-15, Bogotá', 'Pendiente'
FROM pacientes p JOIN medicos m ON m.correo = 'lgomez@eps.com'
WHERE p.documento = '1012345678' LIMIT 1;

INSERT INTO citas (paciente_id, medico_id, tipo_cita, fecha, hora, direccion_eps, estado)
SELECT p.id, m.id, 'Especialista', '2026-06-18', '11:00:00', 'Cra. 7 # 45-10, Bogotá', 'Atendida'
FROM pacientes p JOIN medicos m ON m.correo = 'hsuarez@eps.com'
WHERE p.documento = '987654321' LIMIT 1;

INSERT INTO citas (paciente_id, medico_id, tipo_cita, fecha, hora, direccion_eps, estado)
SELECT p.id, m.id, 'General', '2026-07-20', '10:00:00', 'Calle 45 # 12-30, Bogotá', 'Pendiente'
FROM pacientes p JOIN medicos m ON m.correo = 'jperez@eps.com'
WHERE p.documento = '1122334455' LIMIT 1;

-- Nota clínica de prueba ------------------------------------------
INSERT INTO notas_cita (cita_id, medico_id, nota)
SELECT c.id, m.id,
  'Paciente presenta mejoría notable. Control de presión arterial estable. Se recomienda seguimiento en 30 días y mantener medicación actual.'
FROM citas c
JOIN medicos m ON c.medico_id = m.id
WHERE m.correo = 'hsuarez@eps.com' AND c.estado = 'Atendida'
LIMIT 1;


-- ════════════════════════════════════════════════════════════════
--  VISTAS
-- ════════════════════════════════════════════════════════════════

-- v_citas_completas: join completo para consultas de paciente/admin
CREATE OR REPLACE VIEW v_citas_completas AS
SELECT
  c.id                                            AS cita_id,
  c.fecha,
  c.hora,
  c.tipo_cita,
  c.estado,
  c.direccion_eps,
  c.creado_en,
  -- Paciente
  p.id                                            AS paciente_id,
  p.documento                                     AS paciente_documento,
  CONCAT(p.nombre, ' ', p.apellido)               AS paciente_nombre,
  p.telefono                                      AS paciente_telefono,
  p.correo                                        AS paciente_correo,
  p.eps                                           AS paciente_eps,
  -- Médico
  m.id                                            AS medico_id,
  CONCAT('Dr(a). ', m.nombre, ' ', m.apellido)    AS medico_nombre,
  m.especialidad                                  AS medico_especialidad,
  m.correo                                        AS medico_correo
FROM citas c
JOIN pacientes p ON c.paciente_id = p.id
JOIN medicos   m ON c.medico_id   = m.id;


-- v_agenda_medico: citas pendientes desde hoy para el panel médico
CREATE OR REPLACE VIEW v_agenda_medico AS
SELECT
  c.id            AS cita_id,
  c.fecha,
  c.hora,
  c.tipo_cita,
  c.estado,
  c.direccion_eps,
  m.id            AS medico_id,
  CONCAT(m.nombre, ' ', m.apellido)  AS medico_nombre,
  p.id            AS paciente_id,
  CONCAT(p.nombre, ' ', p.apellido)  AS paciente_nombre,
  p.documento     AS paciente_documento,
  p.telefono      AS paciente_telefono,
  p.eps           AS paciente_eps
FROM citas c
JOIN medicos   m ON c.medico_id   = m.id
JOIN pacientes p ON c.paciente_id = p.id
WHERE c.estado = 'Pendiente'
  AND c.fecha >= CURDATE()
ORDER BY c.fecha ASC, c.hora ASC;


-- v_resumen_admin: métricas para el dashboard del administrador
CREATE OR REPLACE VIEW v_resumen_admin AS
SELECT
  (SELECT COUNT(*) FROM usuarios  WHERE rol    = 'paciente' AND activo = 1) AS total_pacientes,
  (SELECT COUNT(*) FROM usuarios  WHERE rol    = 'medico'   AND activo = 1) AS total_medicos,
  (SELECT COUNT(*) FROM citas     WHERE estado = 'Pendiente')               AS citas_pendientes,
  (SELECT COUNT(*) FROM citas     WHERE estado = 'Atendida')                AS citas_atendidas,
  (SELECT COUNT(*) FROM citas     WHERE estado = 'Cancelada')               AS citas_canceladas,
  (SELECT COUNT(*) FROM citas     WHERE estado = 'No asistió')              AS citas_no_asistio,
  (SELECT COUNT(*) FROM citas     WHERE fecha  = CURDATE())                 AS citas_hoy,
  (SELECT COUNT(*) FROM citas)                                              AS total_citas;


-- ════════════════════════════════════════════════════════════════
--  MIGRACIÓN DESDE v1.0
--  Solo si ya tenías la base de datos instalada anteriormente.
--  Si es instalación nueva IGNORA esta sección completamente.
-- ════════════════════════════════════════════════════════════════

/*

-- PASO 1: Backup obligatorio antes de migrar
--   mysqldump -u root -p eps_citas > eps_citas_backup_v1_$(date +%Y%m%d).sql

-- PASO 2: Eliminar tablas viejas (orden inverso por FK)
DROP TABLE IF EXISTS citas;
DROP TABLE IF EXISTS pacientes;

-- PASO 3: Ejecutar este archivo completo desde el principio
--   mysql -u root -p eps_citas < eps_citas_db.sql

-- PASO 4: Verificar resultado
SHOW TABLES;
-- Resultado esperado: citas | medicos | notas_cita | pacientes | usuarios

SELECT TABLE_NAME, TABLE_ROWS
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'eps_citas';

*/


-- ════════════════════════════════════════════════════════════════
--  QUERIES DE VERIFICACIÓN — ejecuta para confirmar instalación
-- ════════════════════════════════════════════════════════════════

/*
SHOW TABLES;
SELECT id, documento, rol, activo FROM usuarios ORDER BY rol;
SELECT id, nombre, apellido, especialidad, activo FROM medicos;
SELECT id, nombre, apellido, eps FROM pacientes;
SELECT * FROM v_resumen_admin;
SELECT cita_id, paciente_nombre, medico_nombre, tipo_cita, fecha, estado
FROM v_citas_completas ORDER BY fecha;
*/

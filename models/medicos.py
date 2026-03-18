from database import get_connection, close_connection
from mysql.connector import Error

ESPECIALIDADES = ["General", "Odontología", "Especialista"]
ESTADOS_CITA   = ["Pendiente", "Atendida", "Cancelada", "No asistió"]


class Medico:
    """Modelo para gestión de médicos y sus citas."""

    # ─────────────────────────────────────────
    #  VALIDACIONES
    # ─────────────────────────────────────────

    @staticmethod
    def validar_datos(nombre, apellido, especialidad, telefono, correo, direccion_eps):
        errores = []
        if not nombre or len(nombre.strip()) < 2:
            errores.append("El nombre debe tener al menos 2 caracteres.")
        if not apellido or len(apellido.strip()) < 2:
            errores.append("El apellido debe tener al menos 2 caracteres.")
        if especialidad not in ESPECIALIDADES:
            errores.append(f"Especialidad inválida. Opciones: {', '.join(ESPECIALIDADES)}.")
        if not telefono or not telefono.strip().replace("+", "").replace(" ", "").isdigit():
            errores.append("El teléfono solo puede contener números.")
        if not correo or "@" not in correo or "." not in correo.split("@")[-1]:
            errores.append("El correo no tiene un formato válido.")
        if not direccion_eps or len(direccion_eps.strip()) < 5:
            errores.append("La dirección de la EPS es obligatoria.")
        return errores

    # ─────────────────────────────────────────
    #  CRUD MÉDICOS
    # ─────────────────────────────────────────

    @staticmethod
    def crear(usuario_id, nombre, apellido, especialidad, telefono, correo, direccion_eps):
        """Crea el perfil del médico vinculado a un usuario_id existente."""
        errores = Medico.validar_datos(nombre, apellido, especialidad, telefono, correo, direccion_eps)
        if errores:
            return False, errores

        conn = get_connection()
        if not conn:
            return False, ["No se pudo conectar a la base de datos."]
        cursor = None
        try:
            cursor = conn.cursor()
            sql = """
                INSERT INTO medicos
                  (usuario_id, nombre, apellido, especialidad, telefono, correo, direccion_eps)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                usuario_id,
                nombre.strip(), apellido.strip(), especialidad,
                telefono.strip(), correo.strip().lower(), direccion_eps.strip()
            ))
            conn.commit()
            return True, "Médico registrado exitosamente."
        except Error as e:
            conn.rollback()
            if e.errno == 1062:
                return False, ["Ya existe un perfil de médico para ese usuario."]
            return False, [f"Error al registrar el médico: {str(e)}"]
        finally:
            close_connection(conn, cursor)

    @staticmethod
    def obtener_todos(solo_activos=False) -> list:
        conn = get_connection()
        if not conn:
            return []
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            sql = """
                SELECT m.*, u.documento, u.activo AS usuario_activo
                FROM medicos m
                JOIN usuarios u ON m.usuario_id = u.id
                {where}
                ORDER BY m.especialidad, m.apellido
            """.format(where="WHERE m.activo = 1 AND u.activo = 1" if solo_activos else "")
            cursor.execute(sql)
            return cursor.fetchall()
        except Error as e:
            print(f"[ERROR] Medico.obtener_todos: {e}")
            return []
        finally:
            close_connection(conn, cursor)

    @staticmethod
    def obtener_por_id(medico_id: int):
        conn = get_connection()
        if not conn:
            return None
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """SELECT m.*, u.documento
                   FROM medicos m JOIN usuarios u ON m.usuario_id = u.id
                   WHERE m.id = %s""",
                (medico_id,)
            )
            return cursor.fetchone()
        except Error as e:
            print(f"[ERROR] Medico.obtener_por_id: {e}")
            return None
        finally:
            close_connection(conn, cursor)

    @staticmethod
    def obtener_por_usuario_id(usuario_id: int):
        """Obtiene el perfil médico a partir del id de usuario (para sesión)."""
        conn = get_connection()
        if not conn:
            return None
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM medicos WHERE usuario_id = %s", (usuario_id,))
            return cursor.fetchone()
        except Error as e:
            print(f"[ERROR] Medico.obtener_por_usuario_id: {e}")
            return None
        finally:
            close_connection(conn, cursor)

    @staticmethod
    def obtener_por_especialidad(especialidad: str) -> list:
        """Lista médicos activos filtrados por especialidad."""
        conn = get_connection()
        if not conn:
            return []
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """SELECT m.id, m.nombre, m.apellido, m.especialidad, m.direccion_eps
                   FROM medicos m JOIN usuarios u ON m.usuario_id = u.id
                   WHERE m.especialidad = %s AND m.activo = 1 AND u.activo = 1
                   ORDER BY m.apellido""",
                (especialidad,)
            )
            return cursor.fetchall()
        except Error as e:
            print(f"[ERROR] Medico.obtener_por_especialidad: {e}")
            return []
        finally:
            close_connection(conn, cursor)

    @staticmethod
    def actualizar(medico_id, nombre, apellido, especialidad, telefono, correo, direccion_eps):
        errores = Medico.validar_datos(nombre, apellido, especialidad, telefono, correo, direccion_eps)
        if errores:
            return False, errores

        conn = get_connection()
        if not conn:
            return False, ["No se pudo conectar a la base de datos."]
        cursor = None
        try:
            cursor = conn.cursor()
            sql = """
                UPDATE medicos
                SET nombre=%s, apellido=%s, especialidad=%s,
                    telefono=%s, correo=%s, direccion_eps=%s
                WHERE id=%s
            """
            cursor.execute(sql, (
                nombre.strip(), apellido.strip(), especialidad,
                telefono.strip(), correo.strip().lower(), direccion_eps.strip(),
                medico_id
            ))
            conn.commit()
            if cursor.rowcount == 0:
                return False, ["No se encontró el médico."]
            return True, "Datos del médico actualizados."
        except Error as e:
            conn.rollback()
            return False, [f"Error al actualizar: {str(e)}"]
        finally:
            close_connection(conn, cursor)

    @staticmethod
    def toggle_activo(medico_id: int):
        conn = get_connection()
        if not conn:
            return False, "No se pudo conectar a la base de datos."
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE medicos SET activo = NOT activo WHERE id = %s", (medico_id,))
            conn.commit()
            return True, "Estado del médico actualizado."
        except Error as e:
            conn.rollback()
            return False, f"Error: {str(e)}"
        finally:
            close_connection(conn, cursor)

    # ─────────────────────────────────────────
    #  CITAS DEL MÉDICO
    # ─────────────────────────────────────────

    @staticmethod
    def obtener_citas(medico_id: int, estado=None, fecha=None) -> list:
        """
        Retorna las citas asignadas a un médico.
        Filtros opcionales: estado (str) y/o fecha (str YYYY-MM-DD).
        """
        conn = get_connection()
        if not conn:
            return []
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            condiciones = ["c.medico_id = %s"]
            params = [medico_id]

            if estado and estado in ESTADOS_CITA:
                condiciones.append("c.estado = %s")
                params.append(estado)
            if fecha:
                condiciones.append("c.fecha = %s")
                params.append(fecha)

            sql = """
                SELECT
                  c.id          AS cita_id,
                  c.fecha,
                  c.hora,
                  c.tipo_cita,
                  c.estado,
                  c.direccion_eps,
                  c.creado_en,
                  p.id          AS paciente_id,
                  p.documento   AS paciente_documento,
                  CONCAT(p.nombre, ' ', p.apellido) AS paciente_nombre,
                  p.telefono    AS paciente_telefono,
                  p.eps         AS paciente_eps
                FROM citas c
                JOIN pacientes p ON c.paciente_id = p.id
                WHERE {where}
                ORDER BY c.fecha ASC, c.hora ASC
            """.format(where=" AND ".join(condiciones))

            cursor.execute(sql, params)
            return cursor.fetchall()
        except Error as e:
            print(f"[ERROR] Medico.obtener_citas: {e}")
            return []
        finally:
            close_connection(conn, cursor)

    @staticmethod
    def citas_hoy(medico_id: int) -> list:
        """Atajo: citas del día de hoy para el dashboard del médico."""
        from datetime import date
        return Medico.obtener_citas(medico_id, fecha=str(date.today()))

    @staticmethod
    def cambiar_estado_cita(cita_id: int, medico_id: int, nuevo_estado: str):
        """
        El médico cambia el estado de UNA de sus citas.
        Verifica que la cita pertenezca a ese médico.
        """
        if nuevo_estado not in ESTADOS_CITA:
            return False, f"Estado inválido. Opciones: {', '.join(ESTADOS_CITA)}."

        conn = get_connection()
        if not conn:
            return False, "No se pudo conectar a la base de datos."
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE citas SET estado = %s WHERE id = %s AND medico_id = %s",
                (nuevo_estado, cita_id, medico_id)
            )
            conn.commit()
            if cursor.rowcount == 0:
                return False, "No se encontró la cita o no tienes permisos para modificarla."
            return True, f"Estado actualizado a '{nuevo_estado}'."
        except Error as e:
            conn.rollback()
            return False, f"Error al actualizar el estado: {str(e)}"
        finally:
            close_connection(conn, cursor)

    # ─────────────────────────────────────────
    #  NOTAS CLÍNICAS
    # ─────────────────────────────────────────

    @staticmethod
    def agregar_nota(cita_id: int, medico_id: int, nota: str):
        """Agrega una nota clínica a una cita. Verifica pertenencia."""
        if not nota or len(nota.strip()) < 5:
            return False, "La nota debe tener al menos 5 caracteres."
        if len(nota.strip()) > 2000:
            return False, "La nota no puede superar los 2000 caracteres."

        conn = get_connection()
        if not conn:
            return False, "No se pudo conectar a la base de datos."
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)

            # Verificar que la cita pertenece al médico
            cursor.execute(
                "SELECT id FROM citas WHERE id = %s AND medico_id = %s",
                (cita_id, medico_id)
            )
            if not cursor.fetchone():
                return False, "No tienes permisos para agregar notas a esta cita."

            cursor.execute(
                "INSERT INTO notas_cita (cita_id, medico_id, nota) VALUES (%s, %s, %s)",
                (cita_id, medico_id, nota.strip())
            )
            conn.commit()
            return True, "Nota clínica guardada exitosamente."
        except Error as e:
            conn.rollback()
            return False, f"Error al guardar la nota: {str(e)}"
        finally:
            close_connection(conn, cursor)

    @staticmethod
    def obtener_notas(cita_id: int) -> list:
        """Retorna todas las notas clínicas de una cita, ordenadas por fecha."""
        conn = get_connection()
        if not conn:
            return []
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """SELECT n.id, n.nota, n.creado_en,
                          CONCAT('Dr(a). ', m.nombre, ' ', m.apellido) AS medico_nombre
                   FROM notas_cita n
                   JOIN medicos m ON n.medico_id = m.id
                   WHERE n.cita_id = %s
                   ORDER BY n.creado_en ASC""",
                (cita_id,)
            )
            return cursor.fetchall()
        except Error as e:
            print(f"[ERROR] Medico.obtener_notas: {e}")
            return []
        finally:
            close_connection(conn, cursor)

    # ─────────────────────────────────────────
    #  ESTADÍSTICAS DEL MÉDICO
    # ─────────────────────────────────────────

    @staticmethod
    def estadisticas(medico_id: int) -> dict:
        """Retorna métricas rápidas para el dashboard del médico."""
        conn = get_connection()
        if not conn:
            return {}
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT
                  COUNT(*)                                         AS total_citas,
                  SUM(estado = 'Pendiente')                        AS pendientes,
                  SUM(estado = 'Atendida')                         AS atendidas,
                  SUM(estado = 'Cancelada')                        AS canceladas,
                  SUM(estado = 'No asistió')                       AS no_asistio,
                  SUM(fecha = CURDATE())                           AS hoy,
                  SUM(fecha >= CURDATE() AND estado = 'Pendiente') AS proximas
                FROM citas
                WHERE medico_id = %s
            """, (medico_id,))
            return cursor.fetchone() or {}
        except Error as e:
            print(f"[ERROR] Medico.estadisticas: {e}")
            return {}
        finally:
            close_connection(conn, cursor)

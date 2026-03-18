from database import get_connection, close_connection
from mysql.connector import Error
from datetime import date, datetime

TIPOS_CITA   = ["General", "Odontología", "Especialista"]
ESTADOS_CITA = ["Pendiente", "Atendida", "Cancelada", "No asistió"]


class Cita:
    """Modelo para gestión de citas médicas (v2 con roles)."""

    # ─────────────────────────────────────────
    #  VALIDACIONES
    # ─────────────────────────────────────────

    @staticmethod
    def validar_datos(medico_id, tipo_cita, fecha, hora, direccion_eps):
        errores = []
        if not medico_id:
            errores.append("Debe seleccionar un médico.")
        if tipo_cita not in TIPOS_CITA:
            errores.append(f"Tipo de cita inválido. Opciones: {', '.join(TIPOS_CITA)}.")
        if not fecha:
            errores.append("La fecha es obligatoria.")
        else:
            try:
                fecha_obj = datetime.strptime(str(fecha), "%Y-%m-%d").date()
                if fecha_obj < date.today():
                    errores.append("La fecha no puede ser en el pasado.")
            except ValueError:
                errores.append("Formato de fecha inválido (YYYY-MM-DD).")
        if not hora:
            errores.append("La hora es obligatoria.")
        else:
            try:
                datetime.strptime(str(hora), "%H:%M")
            except ValueError:
                errores.append("Formato de hora inválido (HH:MM).")
        if not direccion_eps or not direccion_eps.strip():
            errores.append("La dirección de la EPS es obligatoria.")
        return errores

    # ─────────────────────────────────────────
    #  CRUD
    # ─────────────────────────────────────────

    @staticmethod
    def reservar(paciente_id, medico_id, tipo_cita, fecha, hora, direccion_eps):
        """Crea una nueva cita. paciente_id viene del perfil del paciente autenticado."""
        errores = Cita.validar_datos(medico_id, tipo_cita, fecha, hora, direccion_eps)
        if errores:
            return False, errores

        conn = get_connection()
        if not conn:
            return False, ["No se pudo conectar a la base de datos."]
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)

            # Verificar que el médico existe y está activo
            cursor.execute(
                "SELECT m.id FROM medicos m JOIN usuarios u ON m.usuario_id = u.id "
                "WHERE m.id = %s AND m.activo = 1 AND u.activo = 1",
                (medico_id,)
            )
            if not cursor.fetchone():
                return False, ["El médico seleccionado no está disponible."]

            cursor.execute("""
                INSERT INTO citas (paciente_id, medico_id, tipo_cita, fecha, hora, direccion_eps)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (paciente_id, medico_id, tipo_cita, fecha, hora, direccion_eps.strip()))
            conn.commit()
            return True, "Cita médica reservada exitosamente."
        except Error as e:
            conn.rollback()
            return False, [f"Error al reservar la cita: {str(e)}"]
        finally:
            close_connection(conn, cursor)

    @staticmethod
    def obtener_por_paciente(paciente_id: int) -> list:
        """Retorna todas las citas de un paciente con datos del médico."""
        conn = get_connection()
        if not conn:
            return []
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT
                  c.id            AS cita_id,
                  c.fecha,
                  c.hora,
                  c.tipo_cita,
                  c.estado,
                  c.direccion_eps,
                  c.creado_en,
                  CONCAT('Dr(a). ', m.nombre, ' ', m.apellido) AS medico_nombre,
                  m.especialidad  AS medico_especialidad,
                  m.id            AS medico_id
                FROM citas c
                JOIN medicos m ON c.medico_id = m.id
                WHERE c.paciente_id = %s
                ORDER BY c.fecha ASC, c.hora ASC
            """, (paciente_id,))
            return cursor.fetchall()
        except Error as e:
            print(f"[ERROR] Cita.obtener_por_paciente: {e}")
            return []
        finally:
            close_connection(conn, cursor)

    @staticmethod
    def obtener_por_id(cita_id: int):
        """Retorna datos completos de una cita (join paciente + médico)."""
        conn = get_connection()
        if not conn:
            return None
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT
                  c.*,
                  CONCAT(p.nombre, ' ', p.apellido)            AS paciente_nombre,
                  p.documento AS paciente_documento,
                  p.telefono  AS paciente_telefono,
                  p.eps       AS paciente_eps,
                  CONCAT('Dr(a). ', m.nombre, ' ', m.apellido) AS medico_nombre,
                  m.especialidad AS medico_especialidad
                FROM citas c
                JOIN pacientes p ON c.paciente_id = p.id
                JOIN medicos   m ON c.medico_id   = m.id
                WHERE c.id = %s
            """, (cita_id,))
            return cursor.fetchone()
        except Error as e:
            print(f"[ERROR] Cita.obtener_por_id: {e}")
            return None
        finally:
            close_connection(conn, cursor)

    @staticmethod
    def actualizar(cita_id, paciente_id, medico_id, tipo_cita, fecha, hora, direccion_eps):
        """
        Actualiza una cita. Verifica que pertenece al paciente_id que la edita.
        Solo se pueden editar citas en estado 'Pendiente'.
        """
        errores = Cita.validar_datos(medico_id, tipo_cita, fecha, hora, direccion_eps)
        if errores:
            return False, errores

        conn = get_connection()
        if not conn:
            return False, ["No se pudo conectar a la base de datos."]
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE citas
                SET medico_id=%s, tipo_cita=%s, fecha=%s, hora=%s, direccion_eps=%s
                WHERE id=%s AND paciente_id=%s AND estado='Pendiente'
            """, (medico_id, tipo_cita, fecha, hora, direccion_eps.strip(), cita_id, paciente_id))
            conn.commit()
            if cursor.rowcount == 0:
                return False, ["No se puede modificar esta cita. Solo citas pendientes pueden editarse."]
            return True, "Cita actualizada exitosamente."
        except Error as e:
            conn.rollback()
            return False, [f"Error al actualizar: {str(e)}"]
        finally:
            close_connection(conn, cursor)

    @staticmethod
    def cancelar(cita_id: int, paciente_id: int):
        """El paciente cancela su propia cita (solo si está Pendiente)."""
        conn = get_connection()
        if not conn:
            return False, "No se pudo conectar a la base de datos."
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE citas SET estado = 'Cancelada'
                WHERE id = %s AND paciente_id = %s AND estado = 'Pendiente'
            """, (cita_id, paciente_id))
            conn.commit()
            if cursor.rowcount == 0:
                return False, "No se puede cancelar esta cita."
            return True, "Cita cancelada exitosamente."
        except Error as e:
            conn.rollback()
            return False, f"Error al cancelar: {str(e)}"
        finally:
            close_connection(conn, cursor)

    @staticmethod
    def obtener_todas_admin() -> list:
        """Vista completa para el administrador."""
        conn = get_connection()
        if not conn:
            return []
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT * FROM v_citas_completas
                ORDER BY fecha DESC, hora DESC
            """)
            return cursor.fetchall()
        except Error as e:
            print(f"[ERROR] Cita.obtener_todas_admin: {e}")
            return []
        finally:
            close_connection(conn, cursor)

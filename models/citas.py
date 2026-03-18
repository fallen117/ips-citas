from database import get_connection, close_connection
from mysql.connector import Error
from datetime import date, datetime

TIPOS_CITA   = ["General", "Odontología", "Especialista"]
ESTADOS_CITA = ["Pendiente", "Atendida", "Cancelada", "No asistió"]

# Mapa especialidad del médico → tipos de cita permitidos
ESPECIALIDAD_TIPOS = {
    "General":      ["General"],
    "Odontología":  ["Odontología"],
    "Especialista": ["Especialista"],
}


class Cita:

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

    @staticmethod
    def validar_medico_tipo(medico_id: int, tipo_cita: str) -> list:
        """
        Verifica que el tipo de cita sea compatible con la especialidad del médico.
        Retorna lista de errores; vacía si es válido.
        """
        conn = get_connection()
        if not conn:
            return []
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT especialidad FROM medicos WHERE id = %s AND activo = 1",
                (medico_id,)
            )
            medico = cursor.fetchone()
            if not medico:
                return ["El médico seleccionado no está disponible."]

            especialidad = medico["especialidad"]
            tipos_permitidos = ESPECIALIDAD_TIPOS.get(especialidad, [])

            if tipo_cita not in tipos_permitidos:
                return [
                    f"El tipo de cita '{tipo_cita}' no corresponde a la especialidad "
                    f"'{especialidad}' del médico seleccionado. "
                    f"Tipo permitido: {', '.join(tipos_permitidos)}."
                ]
            return []
        except Error as e:
            print(f"[ERROR] validar_medico_tipo: {e}")
            return []
        finally:
            close_connection(conn, cursor)

    # ─────────────────────────────────────────
    #  CRUD
    # ─────────────────────────────────────────

    @staticmethod
    def reservar(paciente_id, medico_id, tipo_cita, fecha, hora, direccion_eps):
        """Crea una nueva cita para el paciente autenticado."""

        # 1. Validaciones básicas de campos
        errores = Cita.validar_datos(medico_id, tipo_cita, fecha, hora, direccion_eps)
        if errores:
            return False, errores

        # 2. Validar compatibilidad médico / tipo de cita
        try:
            medico_id_int = int(medico_id)
        except (ValueError, TypeError):
            return False, ["El médico seleccionado no es válido."]

        errores_tipo = Cita.validar_medico_tipo(medico_id_int, tipo_cita)
        if errores_tipo:
            return False, errores_tipo

        conn = get_connection()
        if not conn:
            return False, ["No se pudo conectar a la base de datos."]
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)

            # Verificar médico activo
            cursor.execute(
                "SELECT m.id FROM medicos m JOIN usuarios u ON m.usuario_id = u.id "
                "WHERE m.id = %s AND m.activo = 1 AND u.activo = 1",
                (medico_id_int,)
            )
            if not cursor.fetchone():
                return False, ["El médico seleccionado no está disponible."]

            cursor.execute("""
                INSERT INTO citas (paciente_id, medico_id, tipo_cita, fecha, hora, direccion_eps)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (paciente_id, medico_id_int, tipo_cita, fecha, hora, direccion_eps.strip()))
            conn.commit()
            return True, "Cita médica reservada exitosamente."
        except Error as e:
            conn.rollback()
            return False, [f"Error al reservar la cita: {str(e)}"]
        finally:
            close_connection(conn, cursor)

    @staticmethod
    def obtener_por_paciente(paciente_id: int) -> list:
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
        errores = Cita.validar_datos(medico_id, tipo_cita, fecha, hora, direccion_eps)
        if errores:
            return False, errores

        try:
            medico_id_int = int(medico_id)
        except (ValueError, TypeError):
            return False, ["El médico seleccionado no es válido."]

        errores_tipo = Cita.validar_medico_tipo(medico_id_int, tipo_cita)
        if errores_tipo:
            return False, errores_tipo

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
            """, (medico_id_int, tipo_cita, fecha, hora, direccion_eps.strip(), cita_id, paciente_id))
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
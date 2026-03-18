from database import get_connection, close_connection
from mysql.connector import Error


class Paciente:
    """Modelo para gestión del perfil de pacientes."""

    # ─────────────────────────────────────────
    #  VALIDACIONES
    # ─────────────────────────────────────────

    @staticmethod
    def validar_datos(documento, nombre, apellido, telefono, correo, eps):
        errores = []
        if not documento or not str(documento).strip().isdigit():
            errores.append("El documento debe contener solo números.")
        elif not (5 <= len(str(documento).strip()) <= 15):
            errores.append("El documento debe tener entre 5 y 15 dígitos.")
        if not nombre or len(nombre.strip()) < 2:
            errores.append("El nombre debe tener al menos 2 caracteres.")
        if not apellido or len(apellido.strip()) < 2:
            errores.append("El apellido debe tener al menos 2 caracteres.")
        if not telefono or not telefono.strip().replace("+", "").replace(" ", "").isdigit():
            errores.append("El teléfono solo puede contener números.")
        if not correo or "@" not in correo or "." not in correo.split("@")[-1]:
            errores.append("El correo electrónico no es válido.")
        if not eps or not eps.strip():
            errores.append("La EPS es obligatoria.")
        return errores

    # ─────────────────────────────────────────
    #  CRUD
    # ─────────────────────────────────────────

    @staticmethod
    def crear(usuario_id, documento, nombre, apellido, telefono, correo, eps):
        """
        Crea el perfil del paciente vinculado a un usuario_id.
        Llamado justo después de Usuario.registrar_paciente().
        """
        errores = Paciente.validar_datos(documento, nombre, apellido, telefono, correo, eps)
        if errores:
            return False, errores

        conn = get_connection()
        if not conn:
            return False, ["No se pudo conectar a la base de datos."]
        cursor = None
        try:
            cursor = conn.cursor()
            sql = """
                INSERT INTO pacientes (usuario_id, documento, nombre, apellido, telefono, correo, eps)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                usuario_id,
                documento.strip(), nombre.strip(), apellido.strip(),
                telefono.strip(), correo.strip().lower(), eps.strip()
            ))
            conn.commit()
            return True, "Paciente registrado exitosamente."
        except Error as e:
            conn.rollback()
            if e.errno == 1062:
                return False, ["Ya existe un paciente con ese documento."]
            return False, [f"Error al registrar el paciente: {str(e)}"]
        finally:
            close_connection(conn, cursor)

    @staticmethod
    def obtener_por_usuario_id(usuario_id: int):
        """Retorna el perfil del paciente a partir del id de sesión."""
        conn = get_connection()
        if not conn:
            return None
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM pacientes WHERE usuario_id = %s", (usuario_id,))
            return cursor.fetchone()
        except Error as e:
            print(f"[ERROR] Paciente.obtener_por_usuario_id: {e}")
            return None
        finally:
            close_connection(conn, cursor)

    @staticmethod
    def obtener_por_documento(documento: str):
        conn = get_connection()
        if not conn:
            return None
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM pacientes WHERE documento = %s", (documento.strip(),))
            return cursor.fetchone()
        except Error as e:
            print(f"[ERROR] Paciente.obtener_por_documento: {e}")
            return None
        finally:
            close_connection(conn, cursor)

    @staticmethod
    def obtener_por_id(paciente_id: int):
        conn = get_connection()
        if not conn:
            return None
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM pacientes WHERE id = %s", (paciente_id,))
            return cursor.fetchone()
        except Error as e:
            print(f"[ERROR] Paciente.obtener_por_id: {e}")
            return None
        finally:
            close_connection(conn, cursor)

    @staticmethod
    def obtener_todos() -> list:
        conn = get_connection()
        if not conn:
            return []
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT p.*, u.activo AS usuario_activo
                FROM pacientes p
                JOIN usuarios u ON p.usuario_id = u.id
                ORDER BY p.apellido, p.nombre
            """)
            return cursor.fetchall()
        except Error as e:
            print(f"[ERROR] Paciente.obtener_todos: {e}")
            return []
        finally:
            close_connection(conn, cursor)

    @staticmethod
    def actualizar(paciente_id, nombre, apellido, telefono, correo, eps):
        errores = []
        if not nombre or len(nombre.strip()) < 2:
            errores.append("El nombre debe tener al menos 2 caracteres.")
        if not apellido or len(apellido.strip()) < 2:
            errores.append("El apellido debe tener al menos 2 caracteres.")
        if not telefono or not telefono.strip().replace("+", "").replace(" ", "").isdigit():
            errores.append("El teléfono solo puede contener números.")
        if not correo or "@" not in correo:
            errores.append("El correo no es válido.")
        if not eps or not eps.strip():
            errores.append("La EPS es obligatoria.")
        if errores:
            return False, errores

        conn = get_connection()
        if not conn:
            return False, ["No se pudo conectar a la base de datos."]
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE pacientes
                SET nombre=%s, apellido=%s, telefono=%s, correo=%s, eps=%s
                WHERE id=%s
            """, (nombre.strip(), apellido.strip(), telefono.strip(),
                  correo.strip().lower(), eps.strip(), paciente_id))
            conn.commit()
            if cursor.rowcount == 0:
                return False, ["No se encontró el paciente."]
            return True, "Datos actualizados correctamente."
        except Error as e:
            conn.rollback()
            return False, [f"Error al actualizar: {str(e)}"]
        finally:
            close_connection(conn, cursor)

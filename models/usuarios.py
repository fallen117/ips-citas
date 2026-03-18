import bcrypt
from database import get_connection, close_connection
from mysql.connector import Error


class Usuario:
    """Modelo de autenticación — gestiona login, registro y sesión."""

    # ─────────────────────────────────────────
    #  HELPERS PRIVADOS
    # ─────────────────────────────────────────

    @staticmethod
    def _hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(12)).decode("utf-8")

    @staticmethod
    def _verificar_password(password: str, hash_guardado: str) -> bool:
        try:
            return bcrypt.checkpw(password.encode("utf-8"), hash_guardado.encode("utf-8"))
        except Exception:
            return False

    # ─────────────────────────────────────────
    #  VALIDACIONES
    # ─────────────────────────────────────────

    @staticmethod
    def validar_password(password: str) -> list:
        errores = []
        if not password or len(password) < 8:
            errores.append("La contraseña debe tener al menos 8 caracteres.")
        if not any(c.isupper() for c in password):
            errores.append("Debe contener al menos una mayúscula.")
        if not any(c.isdigit() for c in password):
            errores.append("Debe contener al menos un número.")
        return errores

    # ─────────────────────────────────────────
    #  AUTENTICACIÓN
    # ─────────────────────────────────────────

    @staticmethod
    def login(documento: str, password: str):
        if not documento or not password:
            return None, "Documento y contraseña son obligatorios."

        conn = get_connection()
        if not conn:
            return None, "No se pudo conectar a la base de datos."

        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, documento, password_hash, rol, activo FROM usuarios WHERE documento = %s",
                (documento.strip(),)
            )
            usuario = cursor.fetchone()

            if not usuario:
                return None, "Documento o contraseña incorrectos."
            if not usuario["activo"]:
                return None, "Tu cuenta está desactivada. Contacta al administrador."
            if not Usuario._verificar_password(password, usuario["password_hash"]):
                return None, "Documento o contraseña incorrectos."

            del usuario["password_hash"]
            return usuario, None
        except Error as e:
            print(f"[ERROR] login: {e}")
            return None, "Error interno al iniciar sesión."
        finally:
            close_connection(conn, cursor)

    # ─────────────────────────────────────────
    #  CREACIÓN DE USUARIOS
    # ─────────────────────────────────────────

    @staticmethod
    def registrar_paciente(documento: str, password: str):
        errores = []
        doc = str(documento).strip() if documento else ""
        if not doc.isdigit() or not (5 <= len(doc) <= 15):
            errores.append("Documento inválido (solo números, 5-15 dígitos).")
        errores += Usuario.validar_password(password)
        if errores:
            return None, errores
        if Usuario.existe(doc):
            return None, ["Ya existe un usuario con ese documento."]

        conn = get_connection()
        if not conn:
            return None, ["No se pudo conectar a la base de datos."]
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO usuarios (documento, password_hash, rol) VALUES (%s, %s, 'paciente')",
                (doc, Usuario._hash_password(password))
            )
            conn.commit()
            return cursor.lastrowid, None
        except Error as e:
            conn.rollback()
            if e.errno == 1062:
                return None, ["Ya existe un usuario con ese documento."]
            return None, [f"Error al crear el usuario: {str(e)}"]
        finally:
            close_connection(conn, cursor)

    @staticmethod
    def crear_medico(documento: str, password: str):
        errores = []
        doc = str(documento).strip() if documento else ""
        if not doc.isdigit() or not (5 <= len(doc) <= 15):
            errores.append("Documento inválido (solo números, 5-15 dígitos).")
        errores += Usuario.validar_password(password)
        if errores:
            return None, errores
        if Usuario.existe(doc):
            return None, ["Ya existe un usuario con ese documento."]

        conn = get_connection()
        if not conn:
            return None, ["No se pudo conectar a la base de datos."]
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO usuarios (documento, password_hash, rol) VALUES (%s, %s, 'medico')",
                (doc, Usuario._hash_password(password))
            )
            conn.commit()
            return cursor.lastrowid, None
        except Error as e:
            conn.rollback()
            if e.errno == 1062:
                return None, ["Ya existe un usuario con ese documento."]
            return None, [f"Error al crear el médico: {str(e)}"]
        finally:
            close_connection(conn, cursor)

    # ─────────────────────────────────────────
    #  CONSULTAS
    # ─────────────────────────────────────────

    @staticmethod
    def existe(documento: str) -> bool:
        conn = get_connection()
        if not conn:
            return False
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM usuarios WHERE documento = %s", (documento,))
            return cursor.fetchone() is not None
        except Error:
            return False
        finally:
            close_connection(conn, cursor)

    @staticmethod
    def obtener_por_id(usuario_id: int):
        conn = get_connection()
        if not conn:
            return None
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, documento, rol, activo, creado_en FROM usuarios WHERE id = %s",
                (usuario_id,)
            )
            return cursor.fetchone()
        except Error as e:
            print(f"[ERROR] obtener_por_id: {e}")
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
            sql = """
                SELECT
                  u.id,
                  u.documento,
                  u.rol,
                  u.activo,
                  u.creado_en,
                  COALESCE(
                    CONCAT(p.nombre, ' ', p.apellido),
                    CONCAT(m.nombre, ' ', m.apellido),
                    '—'
                  ) AS nombre_completo
                FROM usuarios u
                LEFT JOIN pacientes p ON p.usuario_id = u.id
                LEFT JOIN medicos   m ON m.usuario_id = u.id
                ORDER BY u.rol, u.creado_en DESC
            """
            cursor.execute(sql)
            return cursor.fetchall()
        except Error as e:
            print(f"[ERROR] obtener_todos: {e}")
            return []
        finally:
            close_connection(conn, cursor)

    # ─────────────────────────────────────────
    #  ADMINISTRACIÓN
    # ─────────────────────────────────────────

    @staticmethod
    def toggle_activo(usuario_id: int):
        conn = get_connection()
        if not conn:
            return False, "No se pudo conectar a la base de datos."
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE usuarios SET activo = NOT activo WHERE id = %s AND rol != 'admin'",
                (usuario_id,)
            )
            conn.commit()
            if cursor.rowcount == 0:
                return False, "No se puede modificar este usuario."
            return True, "Estado actualizado correctamente."
        except Error as e:
            conn.rollback()
            return False, f"Error: {str(e)}"
        finally:
            close_connection(conn, cursor)

    @staticmethod
    def cambiar_password(usuario_id: int, nueva_password: str):
        errores = Usuario.validar_password(nueva_password)
        if errores:
            return False, errores
        conn = get_connection()
        if not conn:
            return False, ["No se pudo conectar a la base de datos."]
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE usuarios SET password_hash = %s WHERE id = %s",
                (Usuario._hash_password(nueva_password), usuario_id)
            )
            conn.commit()
            return True, "Contraseña actualizada exitosamente."
        except Error as e:
            conn.rollback()
            return False, [f"Error al actualizar: {str(e)}"]
        finally:
            close_connection(conn, cursor)

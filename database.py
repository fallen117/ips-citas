import mysql.connector
from mysql.connector import Error
from config import Config


def get_connection():
    """
    Crea y retorna una conexión a la base de datos MySQL.
    Retorna None si la conexión falla.
    """
    try:
        conexion = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB,
            port=Config.MYSQL_PORT
        )
        if conexion.is_connected():
            return conexion
    except Error as e:
        print(f"[ERROR] No se pudo conectar a MySQL: {e}")
        return None


def close_connection(conexion, cursor=None):
    """
    Cierra de forma segura el cursor y la conexión a la base de datos.
    """
    try:
        if cursor:
            cursor.close()
        if conexion and conexion.is_connected():
            conexion.close()
    except Error as e:
        print(f"[ERROR] Al cerrar la conexión: {e}")


def test_connection():
    """
    Prueba la conexión a la base de datos.
    Retorna True si la conexión es exitosa, False en caso contrario.
    """
    conn = get_connection()
    if conn:
        close_connection(conn)
        return True
    return False

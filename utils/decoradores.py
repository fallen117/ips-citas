from functools import wraps
from flask import session, redirect, url_for, flash


def login_required(f):
    """Protege rutas que requieren sesión activa."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "usuario_id" not in session:
            flash("Debes iniciar sesión para acceder.", "error")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


def rol_required(*roles):
    """
    Protege rutas para roles específicos.
    Uso: @rol_required("admin") o @rol_required("medico", "admin")
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if "usuario_id" not in session:
                flash("Debes iniciar sesión para acceder.", "error")
                return redirect(url_for("auth.login"))

            rol_actual = session.get("rol")
            if rol_actual not in roles:
                flash("No tienes permisos para acceder a esta sección.", "error")
                return redirect(url_for(_dashboard_por_rol(rol_actual)))

            return f(*args, **kwargs)
        return decorated
    return decorator


def _dashboard_por_rol(rol: str) -> str:
    return {
        "paciente": "paciente.dashboard",
        "medico":   "medico.dashboard",
        "admin":    "admin.dashboard",
    }.get(rol, "auth.login")


def get_usuario_sesion() -> dict:
    """Datos del usuario en sesión para pasar a templates."""
    return {
        "usuario_id": session.get("usuario_id"),
        "documento":  session.get("documento"),
        "rol":        session.get("rol"),
        "nombre":     session.get("nombre"),
        "perfil_id":  session.get("perfil_id"),
    }


def set_sesion(usuario: dict, nombre: str, perfil_id: int):
    """Guarda los datos del usuario en la sesión tras login exitoso."""
    session.permanent = True
    session["usuario_id"] = usuario["id"]
    session["documento"]  = usuario["documento"]
    session["rol"]        = usuario["rol"]
    session["nombre"]     = nombre
    session["perfil_id"]  = perfil_id


def clear_sesion():
    """Limpia la sesión completa."""
    session.clear()

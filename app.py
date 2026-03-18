from flask import Flask, render_template, redirect, url_for, session
from config import Config
from database import test_connection

# ── Blueprints ────────────────────────────────────────────────────
from routes.auth     import auth
from routes.paciente import paciente
from routes.medico   import medico
from routes.admin    import admin

app = Flask(__name__)
app.config.from_object(Config)


# ── Registrar blueprints ──────────────────────────────────────────
app.register_blueprint(auth)
app.register_blueprint(paciente)
app.register_blueprint(medico)
app.register_blueprint(admin)


# ── Ruta raíz ────────────────────────────────────────────────────
@app.route("/")
def index():
    # Si hay sesión activa → redirigir al dashboard del rol
    if "usuario_id" in session:
        rol = session.get("rol")
        destinos = {
            "paciente": "paciente.dashboard",
            "medico":   "medico.dashboard",
            "admin":    "admin.dashboard",
        }
        return redirect(url_for(destinos.get(rol, "auth.login")))

    # Sin sesión → página de inicio pública
    db_status = test_connection()
    return render_template("index.html", db_status=db_status)


# ── Filtros Jinja2 ────────────────────────────────────────────────
@app.template_filter("fecha_formato")
def fecha_formato(fecha):
    """YYYY-MM-DD → DD/MM/YYYY"""
    if not fecha:
        return ""
    try:
        if hasattr(fecha, "strftime"):
            return fecha.strftime("%d/%m/%Y")
        from datetime import datetime
        return datetime.strptime(str(fecha), "%Y-%m-%d").strftime("%d/%m/%Y")
    except Exception:
        return str(fecha)


@app.template_filter("hora_formato")
def hora_formato(hora):
    """HH:MM:SS → HH:MM AM/PM"""
    if not hora:
        return ""
    try:
        hora_str = str(hora)
        if ":" in hora_str:
            partes = hora_str.split(":")
            h, m = int(partes[0]), int(partes[1])
            sufijo = "AM" if h < 12 else "PM"
            h12 = h % 12 or 12
            return f"{h12:02d}:{m:02d} {sufijo}"
        return hora_str
    except Exception:
        return str(hora)


@app.template_filter("estado_clase")
def estado_clase(estado):
    """Retorna la clase CSS del badge según el estado de la cita."""
    clases = {
        "Pendiente":  "badge-pendiente",
        "Atendida":   "badge-atendida",
        "Cancelada":  "badge-cancelada",
        "No asistió": "badge-noasistio",
    }
    return clases.get(estado, "badge-general")


@app.template_filter("estado_icono")
def estado_icono(estado):
    """Retorna el emoji/icono según el estado de la cita."""
    iconos = {
        "Pendiente":  "",
        "Atendida":   "",
        "Cancelada":  "",
        "No asistió": "",
    }
    return iconos.get(estado, "")


# ── Manejo de errores ─────────────────────────────────────────────
@app.errorhandler(404)
def pagina_no_encontrada(e):
    return render_template("error.html", codigo=404,
                           mensaje="Página no encontrada"), 404


@app.errorhandler(403)
def prohibido(e):
    return render_template("error.html", codigo=403,
                           mensaje="No tienes permisos para acceder aquí"), 403


@app.errorhandler(500)
def error_interno(e):
    return render_template("error.html", codigo=500,
                           mensaje="Error interno del servidor"), 500


# ── Contexto global para templates ───────────────────────────────
@app.context_processor
def contexto_global():
    """Variables disponibles en todos los templates."""
    return {
        "app_nombre":  Config.APP_NAME,
        "app_version": Config.APP_VERSION,
        "usuario_sesion": {
            "id":        session.get("usuario_id"),
            "documento": session.get("documento"),
            "rol":       session.get("rol"),
            "nombre":    session.get("nombre"),
            "perfil_id": session.get("perfil_id"),
        } if "usuario_id" in session else None
    }


# ── Inicio ────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=Config.DEBUG, host="0.0.0.0", port=5000)

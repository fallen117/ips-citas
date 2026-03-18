from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.usuarios  import Usuario
from models.pacientes import Paciente
from models.medicos   import Medico
from utils.decoradores import set_sesion, clear_sesion, _dashboard_por_rol

auth = Blueprint("auth", __name__, url_prefix="/auth")


# ── Login ──────────────────────────────────────────────────────────
@auth.route("/login", methods=["GET", "POST"])
def login():
    # Si ya tiene sesión activa, redirige a su dashboard
    if "usuario_id" in session:
        return redirect(url_for(_dashboard_por_rol(session.get("rol"))))

    if request.method == "POST":
        documento = request.form.get("documento", "").strip()
        password  = request.form.get("password", "")

        usuario, error = Usuario.login(documento, password)

        if error:
            flash(error, "error")
            return render_template("auth/login.html", documento=documento)

        # Obtener nombre y perfil_id según el rol
        nombre    = ""
        perfil_id = None

        if usuario["rol"] == "paciente":
            perfil = Paciente.obtener_por_usuario_id(usuario["id"])
            if perfil:
                nombre    = f"{perfil['nombre']} {perfil['apellido']}"
                perfil_id = perfil["id"]

        elif usuario["rol"] == "medico":
            perfil = Medico.obtener_por_usuario_id(usuario["id"])
            if perfil:
                nombre    = f"Dr(a). {perfil['nombre']} {perfil['apellido']}"
                perfil_id = perfil["id"]

        elif usuario["rol"] == "admin":
            nombre    = "Administrador"
            perfil_id = usuario["id"]

        set_sesion(usuario, nombre, perfil_id)

        flash(f"Bienvenido/a, {nombre}.", "success")
        return redirect(url_for(_dashboard_por_rol(usuario["rol"])))

    return render_template("auth/login.html", documento="")


# ── Logout ─────────────────────────────────────────────────────────
@auth.route("/logout")
def logout():
    nombre = session.get("nombre", "")
    clear_sesion()
    flash(f"Sesión cerrada correctamente. ¡Hasta pronto, {nombre}!", "info")
    return redirect(url_for("auth.login"))


# ── Registro (solo pacientes) ──────────────────────────────────────
@auth.route("/registro", methods=["GET", "POST"])
def registro():
    if "usuario_id" in session:
        return redirect(url_for(_dashboard_por_rol(session.get("rol"))))

    lista_eps = [
        "Sura EPS", "Nueva EPS", "Sanitas EPS", "Compensar EPS",
        "Coomeva EPS", "Famisanar EPS", "Salud Total EPS",
        "Aliansalud EPS", "Medimás EPS", "Coosalud EPS"
    ]

    if request.method == "POST":
        documento  = request.form.get("documento", "").strip()
        password   = request.form.get("password", "")
        confirmar  = request.form.get("confirmar", "")
        nombre     = request.form.get("nombre", "").strip()
        apellido   = request.form.get("apellido", "").strip()
        telefono   = request.form.get("telefono", "").strip()
        correo     = request.form.get("correo", "").strip()
        eps        = request.form.get("eps", "").strip()

        # Validar que las contraseñas coincidan
        if password != confirmar:
            flash("Las contraseñas no coinciden.", "error")
            return render_template("auth/registro.html",
                                   datos=request.form, lista_eps=lista_eps)

        # Crear usuario
        usuario_id, errores = Usuario.registrar_paciente(documento, password)
        if errores:
            for e in errores:
                flash(e, "error")
            return render_template("auth/registro.html",
                                   datos=request.form, lista_eps=lista_eps)

        # Crear perfil de paciente
        ok, resultado = Paciente.crear(usuario_id, documento, nombre, apellido,
                                       telefono, correo, eps)
        if not ok:
            # Revertir el usuario si falla el perfil
            # (en producción usar transacciones)
            errores = resultado if isinstance(resultado, list) else [resultado]
            for e in errores:
                flash(e, "error")
            return render_template("auth/registro.html",
                                   datos=request.form, lista_eps=lista_eps)

        flash("¡Registro exitoso! Ya puedes iniciar sesión.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/registro.html", datos={}, lista_eps=lista_eps)

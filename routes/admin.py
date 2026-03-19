from flask import Blueprint, render_template, request, redirect, url_for, flash
from models.usuarios  import Usuario
from models.medicos   import Medico, ESPECIALIDADES
from models.pacientes import Paciente
from models.citas     import Cita
from utils.decoradores import rol_required, get_usuario_sesion
from database import get_connection, close_connection

admin = Blueprint("admin", __name__, url_prefix="/admin")


# ── Dashboard ──────────────────────────────────────────────────────
@admin.route("/dashboard")
@rol_required("admin")
def dashboard():
    u = get_usuario_sesion()

    # Métricas calculadas con consultas directas (no depende de vista)
    metricas = _obtener_metricas()

    medicos_recientes  = Medico.obtener_todos()[:5]
    usuarios_recientes = Usuario.obtener_todos()[:8]

    return render_template("admin/dashboard.html",
                           usuario=u,
                           metricas=metricas,
                           medicos_recientes=medicos_recientes,
                           usuarios_recientes=usuarios_recientes)


def _obtener_metricas() -> dict:
    """
    Calcula las métricas del dashboard con consultas directas.
    No depende de la vista v_resumen_admin.
    """
    conn = get_connection()
    if not conn:
        print("[ERROR] _obtener_metricas: no hay conexión a BD")
        return {}
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT
              (SELECT COUNT(*) FROM usuarios WHERE rol = 'paciente' AND activo = 1)
                AS total_pacientes,
              (SELECT COUNT(*) FROM usuarios WHERE rol = 'medico' AND activo = 1)
                AS total_medicos,
              (SELECT COUNT(*) FROM citas WHERE estado = 'Pendiente')
                AS citas_pendientes,
              (SELECT COUNT(*) FROM citas WHERE estado = 'Atendida')
                AS citas_atendidas,
              (SELECT COUNT(*) FROM citas WHERE estado = 'Cancelada')
                AS citas_canceladas,
              (SELECT COUNT(*) FROM citas WHERE fecha = CURDATE())
                AS citas_hoy,
              (SELECT COUNT(*) FROM citas)
                AS total_citas
        """)
        resultado = cursor.fetchone()
        print(f"[INFO] Métricas obtenidas: {resultado}")
        return resultado or {}
    except Exception as e:
        print(f"[ERROR] _obtener_metricas: {e}")
        return {}
    finally:
        close_connection(conn, cursor)


# ══════════════════════════════════════════════
#  GESTIÓN DE USUARIOS
# ══════════════════════════════════════════════

@admin.route("/usuarios")
@rol_required("admin")
def usuarios():
    u             = get_usuario_sesion()
    rol_filtro    = request.args.get("rol", "")
    lista_usuarios = Usuario.obtener_todos()

    if rol_filtro:
        lista_usuarios = [usr for usr in lista_usuarios if usr["rol"] == rol_filtro]

    return render_template("admin/usuarios.html",
                           usuario=u,
                           usuarios=lista_usuarios,
                           rol_filtro=rol_filtro)


@admin.route("/usuarios/<int:usuario_id>/toggle", methods=["POST"])
@rol_required("admin")
def toggle_usuario(usuario_id):
    exito, mensaje = Usuario.toggle_activo(usuario_id)
    flash(mensaje, "success" if exito else "error")
    return redirect(url_for("admin.usuarios"))


# ══════════════════════════════════════════════
#  GESTIÓN DE MÉDICOS
# ══════════════════════════════════════════════

@admin.route("/medicos")
@rol_required("admin")
def medicos():
    u               = get_usuario_sesion()
    esp_filtro      = request.args.get("especialidad", "")
    lista_medicos   = Medico.obtener_todos()

    if esp_filtro:
        lista_medicos = [m for m in lista_medicos if m["especialidad"] == esp_filtro]

    return render_template("admin/medicos.html",
                           usuario=u,
                           lista_medicos=lista_medicos,
                           especialidades=ESPECIALIDADES,
                           esp_filtro=esp_filtro)


@admin.route("/medicos/nuevo", methods=["GET", "POST"])
@rol_required("admin")
def nuevo_medico():
    u = get_usuario_sesion()

    if request.method == "POST":
        documento     = request.form.get("documento", "").strip()
        password      = request.form.get("password", "").strip()
        confirmar     = request.form.get("confirmar", "").strip()
        nombre        = request.form.get("nombre", "").strip()
        apellido      = request.form.get("apellido", "").strip()
        especialidad  = request.form.get("especialidad", "").strip()
        telefono      = request.form.get("telefono", "").strip()
        correo        = request.form.get("correo", "").strip()
        direccion_eps = request.form.get("direccion_eps", "").strip()

        # Validar coincidencia de contraseñas
        if password != confirmar:
            flash("Las contraseñas no coinciden.", "error")
            return render_template("admin/nuevo_medico.html",
                                   usuario=u,
                                   especialidades=ESPECIALIDADES,
                                   datos=request.form)

        # 1. Crear usuario con rol médico
        usuario_id, errores = Usuario.crear_medico(documento, password)
        if errores:
            for e in errores:
                flash(e, "error")
            return render_template("admin/nuevo_medico.html",
                                   usuario=u,
                                   especialidades=ESPECIALIDADES,
                                   datos=request.form)

        # 2. Crear perfil del médico
        exito, resultado = Medico.crear(
            usuario_id, nombre, apellido,
            especialidad, telefono, correo, direccion_eps
        )
        if not exito:
            errores = resultado if isinstance(resultado, list) else [resultado]
            for e in errores:
                flash(e, "error")
            return render_template("admin/nuevo_medico.html",
                                   usuario=u,
                                   especialidades=ESPECIALIDADES,
                                   datos=request.form)

        flash(f"Médico Dr(a). {nombre} {apellido} registrado exitosamente.", "success")
        return redirect(url_for("admin.medicos"))

    return render_template("admin/nuevo_medico.html",
                           usuario=u,
                           especialidades=ESPECIALIDADES,
                           datos={})


@admin.route("/medicos/<int:medico_id>/editar", methods=["GET", "POST"])
@rol_required("admin")
def editar_medico(medico_id):
    u      = get_usuario_sesion()
    perfil = Medico.obtener_por_id(medico_id)

    if not perfil:
        flash("Médico no encontrado.", "error")
        return redirect(url_for("admin.medicos"))

    if request.method == "POST":
        nombre        = request.form.get("nombre", "").strip()
        apellido      = request.form.get("apellido", "").strip()
        especialidad  = request.form.get("especialidad", "").strip()
        telefono      = request.form.get("telefono", "").strip()
        correo        = request.form.get("correo", "").strip()
        direccion_eps = request.form.get("direccion_eps", "").strip()

        exito, resultado = Medico.actualizar(
            medico_id, nombre, apellido,
            especialidad, telefono, correo, direccion_eps
        )

        if exito:
            flash(resultado, "success")
            return redirect(url_for("admin.medicos"))

        errores = resultado if isinstance(resultado, list) else [resultado]
        for e in errores:
            flash(e, "error")

    return render_template("admin/editar_medico.html",
                           usuario=u,
                           perfil=perfil,
                           especialidades=ESPECIALIDADES)


@admin.route("/medicos/<int:medico_id>/toggle", methods=["POST"])
@rol_required("admin")
def toggle_medico(medico_id):
    exito, mensaje = Medico.toggle_activo(medico_id)
    flash(mensaje, "success" if exito else "error")
    return redirect(url_for("admin.medicos"))
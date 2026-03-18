from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.citas     import Cita, TIPOS_CITA, ESTADOS_CITA
from models.pacientes import Paciente
from models.medicos   import Medico, ESPECIALIDADES
from utils.decoradores import rol_required, get_usuario_sesion

paciente = Blueprint("paciente", __name__, url_prefix="/paciente")


# ── Dashboard ──────────────────────────────────────────────────────
@paciente.route("/dashboard")
@rol_required("paciente")
def dashboard():
    u      = get_usuario_sesion()
    perfil = Paciente.obtener_por_id(u["perfil_id"])
    citas  = Cita.obtener_por_paciente(u["perfil_id"])

    proximas  = [c for c in citas if c["estado"] == "Pendiente"]
    historial = [c for c in citas if c["estado"] != "Pendiente"]

    return render_template("paciente/dashboard.html",
                           usuario=u,
                           perfil=perfil,
                           proximas=proximas,
                           historial=historial)


# ── Mis citas (listado completo con filtro) ────────────────────────
@paciente.route("/mis-citas")
@rol_required("paciente")
def mis_citas():
    u             = get_usuario_sesion()
    estado_filtro = request.args.get("estado", "")
    citas         = Cita.obtener_por_paciente(u["perfil_id"])

    if estado_filtro:
        citas = [c for c in citas if c["estado"] == estado_filtro]

    return render_template("paciente/mis_citas.html",
                           usuario=u,
                           citas=citas,
                           estado_filtro=estado_filtro,
                           estados=ESTADOS_CITA)


# ── Reservar nueva cita ────────────────────────────────────────────
@paciente.route("/reservar-cita", methods=["GET", "POST"])
@rol_required("paciente")
def reservar_cita():
    u               = get_usuario_sesion()
    medicos_activos = Medico.obtener_todos(solo_activos=True)

    if request.method == "POST":
        medico_id     = request.form.get("medico_id", "").strip()
        tipo_cita     = request.form.get("tipo_cita", "").strip()
        fecha         = request.form.get("fecha", "").strip()
        hora          = request.form.get("hora", "").strip()
        direccion_eps = request.form.get("direccion_eps", "").strip()

        exito, resultado = Cita.reservar(
            paciente_id=u["perfil_id"],
            medico_id=medico_id,
            tipo_cita=tipo_cita,
            fecha=fecha,
            hora=hora,
            direccion_eps=direccion_eps
        )

        if exito:
            flash(resultado, "success")
            return redirect(url_for("paciente.mis_citas"))

        errores = resultado if isinstance(resultado, list) else [resultado]
        for e in errores:
            flash(e, "error")

    return render_template("paciente/reservar_cita.html",
                           usuario=u,
                           tipos_cita=TIPOS_CITA,
                           especialidades=ESPECIALIDADES,
                           medicos=medicos_activos,
                           datos=request.form if request.method == "POST" else {},
                           edicion=False)


# ── Editar cita (solo Pendiente) ───────────────────────────────────
@paciente.route("/cita/<int:cita_id>/editar", methods=["GET", "POST"])
@rol_required("paciente")
def editar_cita(cita_id):
    u    = get_usuario_sesion()
    cita = Cita.obtener_por_id(cita_id)

    if not cita or cita["paciente_id"] != u["perfil_id"]:
        flash("No tienes permisos para editar esta cita.", "error")
        return redirect(url_for("paciente.mis_citas"))

    if cita["estado"] != "Pendiente":
        flash("Solo puedes editar citas en estado Pendiente.", "error")
        return redirect(url_for("paciente.mis_citas"))

    medicos_activos = Medico.obtener_todos(solo_activos=True)

    if request.method == "POST":
        medico_id     = request.form.get("medico_id", "").strip()
        tipo_cita     = request.form.get("tipo_cita", "").strip()
        fecha         = request.form.get("fecha", "").strip()
        hora          = request.form.get("hora", "").strip()
        direccion_eps = request.form.get("direccion_eps", "").strip()

        exito, resultado = Cita.actualizar(
            cita_id=cita_id,
            paciente_id=u["perfil_id"],
            medico_id=medico_id,
            tipo_cita=tipo_cita,
            fecha=fecha,
            hora=hora,
            direccion_eps=direccion_eps
        )

        if exito:
            flash(resultado, "success")
            return redirect(url_for("paciente.mis_citas"))

        errores = resultado if isinstance(resultado, list) else [resultado]
        for e in errores:
            flash(e, "error")

    return render_template("paciente/reservar_cita.html",
                           usuario=u,
                           tipos_cita=TIPOS_CITA,
                           especialidades=ESPECIALIDADES,
                           medicos=medicos_activos,
                           datos=cita,
                           edicion=True,
                           cita_id=cita_id)


# ── Cancelar cita ──────────────────────────────────────────────────
@paciente.route("/cita/<int:cita_id>/cancelar", methods=["POST"])
@rol_required("paciente")
def cancelar_cita(cita_id):
    u = get_usuario_sesion()
    exito, mensaje = Cita.cancelar(cita_id, u["perfil_id"])
    flash(mensaje, "success" if exito else "error")
    return redirect(url_for("paciente.mis_citas"))


# ── Perfil del paciente ────────────────────────────────────────────
@paciente.route("/perfil", methods=["GET", "POST"])
@rol_required("paciente")
def perfil():
    u      = get_usuario_sesion()
    perfil = Paciente.obtener_por_id(u["perfil_id"])

    lista_eps = [
        "Sura EPS", "Nueva EPS", "Sanitas EPS", "Compensar EPS",
        "Coomeva EPS", "Famisanar EPS", "Salud Total EPS",
        "Aliansalud EPS", "Medimás EPS", "Coosalud EPS"
    ]

    if request.method == "POST":
        nombre   = request.form.get("nombre",   "").strip()
        apellido = request.form.get("apellido", "").strip()
        telefono = request.form.get("telefono", "").strip()
        correo   = request.form.get("correo",   "").strip()
        eps      = request.form.get("eps",      "").strip()

        exito, resultado = Paciente.actualizar(
            u["perfil_id"], nombre, apellido, telefono, correo, eps
        )

        if exito:
            session["nombre"] = f"{nombre} {apellido}"
            flash(resultado, "success")
            return redirect(url_for("paciente.perfil"))
        else:
            errores = resultado if isinstance(resultado, list) else [resultado]
            for error in errores:
                flash(error, "error")

    return render_template("paciente/perfil.html",
                           u=u, perfil=perfil, lista_eps=lista_eps)
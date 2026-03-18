from flask import Blueprint, render_template, request, redirect, url_for, flash
from models.medicos  import Medico, ESTADOS_CITA
from models.citas    import Cita
from utils.decoradores import rol_required, get_usuario_sesion

medico = Blueprint("medico", __name__, url_prefix="/medico")


# ── Dashboard ──────────────────────────────────────────────────────
@medico.route("/dashboard")
@rol_required("medico")
def dashboard():
    u          = get_usuario_sesion()
    medico_id  = u["perfil_id"]

    citas_hoy  = Medico.citas_hoy(medico_id)
    stats      = Medico.estadisticas(medico_id) or {}
    perfil     = Medico.obtener_por_id(medico_id)

    # Próximas 5 citas pendientes (desde hoy en adelante)
    proximas = Medico.obtener_citas(medico_id, estado="Pendiente")[:5]

    return render_template("medico/dashboard.html",
                           usuario=u,
                           perfil=perfil,
                           citas_hoy=citas_hoy,
                           proximas=proximas,
                           stats=stats)


# ── Listado de todas sus citas ─────────────────────────────────────
@medico.route("/mis-citas")
@rol_required("medico")
def mis_citas():
    u         = get_usuario_sesion()
    medico_id = u["perfil_id"]

    estado_filtro = request.args.get("estado", "")
    fecha_filtro  = request.args.get("fecha", "")

    citas = Medico.obtener_citas(
        medico_id,
        estado = estado_filtro if estado_filtro else None,
        fecha  = fecha_filtro  if fecha_filtro  else None
    )

    return render_template("medico/mis_citas.html",
                           usuario=u,
                           citas=citas,
                           estado_filtro=estado_filtro,
                           fecha_filtro=fecha_filtro,
                           estados=ESTADOS_CITA)


# ── Detalle de una cita ────────────────────────────────────────────
@medico.route("/cita/<int:cita_id>")
@rol_required("medico")
def detalle_cita(cita_id):
    u         = get_usuario_sesion()
    medico_id = u["perfil_id"]

    cita = Cita.obtener_por_id(cita_id)

    # Verificar que la cita pertenece a este médico
    if not cita or cita["medico_id"] != medico_id:
        flash("No tienes permisos para ver esta cita.", "error")
        return redirect(url_for("medico.mis_citas"))

    notas = Medico.obtener_notas(cita_id)

    return render_template("medico/detalle_cita.html",
                           usuario=u,
                           cita=cita,
                           notas=notas,
                           estados=ESTADOS_CITA)


# ── Cambiar estado de una cita ─────────────────────────────────────
@medico.route("/cita/<int:cita_id>/estado", methods=["POST"])
@rol_required("medico")
def cambiar_estado(cita_id):
    u           = get_usuario_sesion()
    medico_id   = u["perfil_id"]
    nuevo_estado = request.form.get("estado", "").strip()

    exito, mensaje = Medico.cambiar_estado_cita(cita_id, medico_id, nuevo_estado)
    flash(mensaje, "success" if exito else "error")
    return redirect(url_for("medico.detalle_cita", cita_id=cita_id))


# ── Agregar nota clínica ───────────────────────────────────────────
@medico.route("/cita/<int:cita_id>/nota", methods=["POST"])
@rol_required("medico")
def agregar_nota(cita_id):
    u         = get_usuario_sesion()
    medico_id = u["perfil_id"]
    nota      = request.form.get("nota", "").strip()

    exito, mensaje = Medico.agregar_nota(cita_id, medico_id, nota)
    flash(mensaje, "success" if exito else "error")
    return redirect(url_for("medico.detalle_cita", cita_id=cita_id))


# ── Perfil del médico (solo lectura) ──────────────────────────────
@medico.route("/perfil")
@rol_required("medico")
def perfil():
    u      = get_usuario_sesion()
    perfil = Medico.obtener_por_id(u["perfil_id"])
    return render_template("medico/perfil.html", u=u, perfil=perfil)

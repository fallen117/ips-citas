/* ════════════════════════════════════════════════
   EPS CITAS — JavaScript Principal
   ════════════════════════════════════════════════ */

document.addEventListener("DOMContentLoaded", () => {

  // ── Navbar móvil ──────────────────────────────
  const toggle = document.getElementById("navbar-toggle");
  const navMenu = document.getElementById("navbar-menu");
  if (toggle && navMenu) {
    toggle.addEventListener("click", () => {
      navMenu.classList.toggle("abierto");
      toggle.setAttribute("aria-expanded", navMenu.classList.contains("abierto"));
    });

    // Cerrar al hacer clic fuera
    document.addEventListener("click", (e) => {
      if (!toggle.contains(e.target) && !navMenu.contains(e.target)) {
        navMenu.classList.remove("abierto");
      }
    });
  }

  // ── Dropdown de usuario ───────────────────────
  const usuarioBtn = document.getElementById("navbar-usuario-btn");
  if (usuarioBtn) {
    usuarioBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      usuarioBtn.classList.toggle("abierto");
    });
    document.addEventListener("click", (e) => {
      if (!usuarioBtn.contains(e.target)) usuarioBtn.classList.remove("abierto");
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") usuarioBtn.classList.remove("abierto");
    });
  }

  // ── Marcar enlace activo en la navbar ─────────
  const rutaActual = window.location.pathname;
  document.querySelectorAll(".navbar-nav a").forEach(link => {
    if (link.getAttribute("href") === rutaActual) {
      link.classList.add("activo");
    }
  });

  // ── Auto-cerrar alertas después de 5s ─────────
  document.querySelectorAll(".alerta").forEach(alerta => {
    setTimeout(() => {
      alerta.style.transition = "opacity 0.4s, transform 0.4s";
      alerta.style.opacity = "0";
      alerta.style.transform = "translateY(-8px)";
      setTimeout(() => alerta.remove(), 400);
    }, 5000);
  });

  // ── Validación del formulario registro paciente ──
  const formPaciente = document.getElementById("form-paciente");
  if (formPaciente) {
    formPaciente.addEventListener("submit", (e) => {
      const errores = validarFormularioPaciente();
      if (errores.length > 0) {
        e.preventDefault();
        mostrarErroresCliente(errores);
      }
    });
  }

  // ── Validación del formulario reservar/editar cita ──
  const formCita = document.getElementById("form-cita");
  if (formCita) {
    formCita.addEventListener("submit", (e) => {
      const errores = validarFormularioCita();
      if (errores.length > 0) {
        e.preventDefault();
        mostrarErroresCliente(errores);
      }
    });
  }

  // ── Confirmación de cancelación de cita ───────
  document.querySelectorAll(".btn-cancelar-cita").forEach(btn => {
    btn.addEventListener("click", (e) => {
      if (!confirm("¿Estás seguro de que deseas cancelar esta cita? Esta acción no se puede deshacer.")) {
        e.preventDefault();
      }
    });
  });

  // ── Fecha mínima = hoy en inputs de fecha ─────
  const inputsFecha = document.querySelectorAll('input[type="date"]');
  const hoy = new Date().toISOString().split("T")[0];
  inputsFecha.forEach(input => {
    if (!input.hasAttribute("min")) {
      input.setAttribute("min", hoy);
    }
  });

  // ── Solo números en campo documento y teléfono ─
  document.querySelectorAll('input[data-solo-numeros]').forEach(input => {
    input.addEventListener("input", () => {
      input.value = input.value.replace(/[^0-9+\s]/g, "");
    });
  });

  // ── Capitalizar primera letra en nombre/apellido ─
  document.querySelectorAll('input[data-capitalizar]').forEach(input => {
    input.addEventListener("blur", () => {
      input.value = input.value
        .split(" ")
        .map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
        .join(" ");
    });
  });

});

/* ── Validaciones cliente ─────────────────────── */

function validarFormularioPaciente() {
  const errores = [];
  const doc  = document.getElementById("documento")?.value.trim();
  const nom  = document.getElementById("nombre")?.value.trim();
  const ape  = document.getElementById("apellido")?.value.trim();
  const tel  = document.getElementById("telefono")?.value.trim();
  const cor  = document.getElementById("correo")?.value.trim();
  const eps  = document.getElementById("eps")?.value.trim();

  if (!doc)                          errores.push("El documento es obligatorio.");
  else if (!/^\d{5,15}$/.test(doc)) errores.push("El documento debe tener entre 5 y 15 dígitos.");

  if (!nom || nom.length < 2)        errores.push("El nombre debe tener al menos 2 caracteres.");
  if (!ape || ape.length < 2)        errores.push("El apellido debe tener al menos 2 caracteres.");

  if (!tel)                          errores.push("El teléfono es obligatorio.");
  else if (!/^[\d+\s]{7,20}$/.test(tel)) errores.push("El teléfono no tiene un formato válido.");

  if (!cor)                          errores.push("El correo es obligatorio.");
  else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(cor)) errores.push("El correo no tiene un formato válido.");

  if (!eps)                          errores.push("La EPS es obligatoria.");

  return errores;
}

function validarFormularioCita() {
  const errores = [];
  const doc  = document.getElementById("documento")?.value.trim();
  const med  = document.getElementById("medico")?.value.trim();
  const tipo = document.getElementById("tipo_cita")?.value;
  const fec  = document.getElementById("fecha")?.value;
  const hor  = document.getElementById("hora")?.value;
  const dir  = document.getElementById("direccion_eps")?.value.trim();

  // El campo documento solo existe en el formulario de nueva cita
  if (doc !== undefined && !doc) errores.push("El documento del paciente es obligatorio.");

  if (!med || med.length < 3) errores.push("El nombre del médico debe tener al menos 3 caracteres.");
  if (!tipo)                  errores.push("Debe seleccionar el tipo de cita.");

  if (!fec) {
    errores.push("La fecha de la cita es obligatoria.");
  } else {
    const hoy = new Date(); hoy.setHours(0, 0, 0, 0);
    const fechaSeleccionada = new Date(fec + "T00:00:00");
    if (fechaSeleccionada < hoy) errores.push("La fecha no puede ser en el pasado.");
  }

  if (!hor)  errores.push("La hora de la cita es obligatoria.");
  if (!dir)  errores.push("La dirección de la EPS es obligatoria.");

  return errores;
}

/* ── Mostrar errores del lado del cliente ──────── */
function mostrarErroresCliente(errores) {
  // Remover errores previos del cliente
  document.querySelectorAll(".alerta-cliente").forEach(a => a.remove());

  const contenedor = document.querySelector(".alertas, .alertas-wide");
  if (!contenedor) return;

  errores.forEach(msg => {
    const div = document.createElement("div");
    div.className = "alerta alerta-error alerta-cliente";
    div.innerHTML = `<span>⚠</span> ${msg}`;
    contenedor.prepend(div);
  });

  // Scroll al primer error
  contenedor.scrollIntoView({ behavior: "smooth", block: "start" });
}
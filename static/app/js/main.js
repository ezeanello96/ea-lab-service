/**
 * PC Service Manager — JavaScript principal
 * Funcionalidad mínima: sidebar móvil + auto-dismiss de alertas.
 */

(function () {
  "use strict";

  /* -------- Sidebar toggle (móvil) -------- */
  const sidebar      = document.getElementById("sidebar");
  const overlay      = document.getElementById("sidebarOverlay");
  const toggleBtn    = document.getElementById("sidebarToggle");
  const closeBtn     = document.getElementById("sidebarClose");

  function openSidebar() {
    if (!sidebar) return;
    sidebar.classList.add("is-open");
    overlay && overlay.classList.add("is-open");
    document.body.style.overflow = "hidden";
  }

  function closeSidebar() {
    if (!sidebar) return;
    sidebar.classList.remove("is-open");
    overlay && overlay.classList.remove("is-open");
    document.body.style.overflow = "";
  }

  toggleBtn && toggleBtn.addEventListener("click", openSidebar);
  closeBtn  && closeBtn.addEventListener("click", closeSidebar);
  overlay   && overlay.addEventListener("click", closeSidebar);

  /* Cerrar sidebar con Escape */
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") closeSidebar();
  });

  /* -------- Alertas: botón de cierre manual -------- */
  document.addEventListener("click", function (e) {
    const closeButton = e.target.closest(".alert-close");
    if (closeButton) {
      const alert = closeButton.closest(".alert");
      if (alert) dismissAlert(alert);
    }
  });

  /* -------- Alertas: auto-dismiss -------- */
  function dismissAlert(el) {
    el.style.transition = "opacity 300ms ease, transform 300ms ease, margin 300ms ease, padding 300ms ease";
    el.style.opacity    = "0";
    el.style.transform  = "translateY(-8px)";
    el.style.overflow   = "hidden";
    el.style.maxHeight  = el.offsetHeight + "px";

    setTimeout(function () {
      el.style.maxHeight = "0";
      el.style.margin    = "0";
      el.style.padding   = "0";
    }, 280);

    setTimeout(function () {
      el.remove();
    }, 600);
  }

  function scheduleAutoDismiss() {
    document.querySelectorAll(".alert[data-auto-dismiss]").forEach(function (alert) {
      const delay = parseInt(alert.dataset.autoDismiss, 10) || 5000;
      setTimeout(function () {
        if (alert.isConnected) dismissAlert(alert);
      }, delay);
    });
  }

  scheduleAutoDismiss();

  /* Re-ejecutar cuando HTMX inyecte nuevo contenido */
  document.addEventListener("htmx:afterSwap", scheduleAutoDismiss);

  /* -------- HTMX: indicador de carga global -------- */
  document.addEventListener("htmx:beforeRequest", function () {
    document.body.classList.add("htmx-loading");
  });
  document.addEventListener("htmx:afterRequest", function () {
    document.body.classList.remove("htmx-loading");
  });

})();

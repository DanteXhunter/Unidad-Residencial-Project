/**
 * Interacciones de la interfaz. Todo el estado real vive en el servidor:
 * este archivo solo abre/cierra diálogos, alterna el menú lateral y descarta
 * los avisos. Sin dependencias externas.
 */
(function () {
  "use strict";

  /* ------------------------------------------------------------- diálogos */
  function openAutoDialogs(root) {
    (root || document)
      .querySelectorAll("dialog[data-autoopen]:not([open])")
      .forEach(function (dialog) {
        dialog.showModal();
      });
  }

  document.addEventListener("click", function (event) {
    var opener = event.target.closest("[data-modal-open]");
    if (opener) {
      var target = document.querySelector(opener.dataset.modalOpen);
      if (target) target.showModal();
      return;
    }

    var closer = event.target.closest("[data-modal-close]");
    if (closer) {
      var dialog = closer.closest("dialog");
      if (dialog) dialog.close();
      return;
    }

    // Un solo diálogo de confirmación sirve para todos los botones eliminar:
    // se le inyecta la URL y el mensaje del registro correspondiente.
    var deleteBtn = event.target.closest("[data-confirm-delete]");
    if (deleteBtn) {
      var confirmDialog = document.getElementById("confirm-dialog");
      if (!confirmDialog) return;
      document.getElementById("confirm-form").action = deleteBtn.dataset.action;
      document.getElementById("confirm-message").textContent = deleteBtn.dataset.message;
      confirmDialog.showModal();
    }
  });

  /* --------------------------------------------------------- menú lateral */
  function initSidebar() {
    var sidebar = document.getElementById("sidebar");
    var toggle = document.getElementById("sidebar-toggle");
    var overlay = document.getElementById("sidebar-overlay");
    if (!sidebar || !toggle || !overlay) return;

    function setOpen(open) {
      sidebar.classList.toggle("-translate-x-full", !open);
      overlay.classList.toggle("hidden", !open);
    }

    toggle.addEventListener("click", function () {
      setOpen(sidebar.classList.contains("-translate-x-full"));
    });
    overlay.addEventListener("click", function () {
      setOpen(false);
    });
  }

  /* -------------------------------------------------------------- avisos */
  function initToasts() {
    document.querySelectorAll(".toast").forEach(function (toast) {
      var dismiss = function () {
        toast.classList.add("opacity-0", "-translate-y-2");
        setTimeout(function () {
          toast.remove();
        }, 300);
      };
      var closeBtn = toast.querySelector("[data-toast-close]");
      if (closeBtn) closeBtn.addEventListener("click", dismiss);
      setTimeout(dismiss, 4500);
    });
  }

  /* --------------------------------------------------------------- inicio */
  document.addEventListener("DOMContentLoaded", function () {
    initSidebar();
    initToasts();
    openAutoDialogs();
  });

  // htmx trae los formularios de edición ya renderizados desde el servidor.
  document.body.addEventListener("htmx:afterSwap", function (event) {
    openAutoDialogs(event.target);
  });

  // Al cerrar un diálogo cargado por htmx se limpia el contenedor para que no
  // queden formularios viejos en el DOM.
  document.addEventListener("close", function (event) {
    var container = document.getElementById("modal-container");
    if (container && container.contains(event.target)) container.innerHTML = "";
  }, true);
})();

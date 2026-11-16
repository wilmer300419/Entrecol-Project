(function () {
  "use strict";
  var raiz = document.documentElement;

  // ---- Tema claro / oscuro
  var btnTema = document.getElementById("btn-tema");
  function etiquetaTema() {
    var oscuro = raiz.dataset.tema === "dark";
    btnTema.setAttribute("aria-label", oscuro ? "Cambiar a modo claro" : "Cambiar a modo oscuro");
    btnTema.setAttribute("aria-pressed", oscuro ? "true" : "false");
  }
  if (btnTema) {
    etiquetaTema();
    btnTema.addEventListener("click", function () {
      var nuevo = raiz.dataset.tema === "dark" ? "light" : "dark";
      raiz.dataset.tema = nuevo;
      try { localStorage.setItem("tema", nuevo); } catch (e) {}
      etiquetaTema();
      document.dispatchEvent(new CustomEvent("tema-cambiado"));
    });
  }

  // ---- Menú lateral en móvil
  var btnMenu = document.getElementById("btn-menu"), menu = document.getElementById("menu"), telon = document.getElementById("telon");
  function alternarMenu(abrir) {
    document.body.classList.toggle("menu-abierto", abrir);
    btnMenu.setAttribute("aria-expanded", abrir ? "true" : "false");
    btnMenu.setAttribute("aria-label", abrir ? "Cerrar menú" : "Abrir menú");
    telon.hidden = !abrir;
    if (abrir) { var a = menu.querySelector("a"); if (a) a.focus(); } else { btnMenu.focus(); }
  }
  if (btnMenu && menu) {
    btnMenu.addEventListener("click", function () { alternarMenu(!document.body.classList.contains("menu-abierto")); });
    telon.addEventListener("click", function () { alternarMenu(false); });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape" && document.body.classList.contains("menu-abierto")) alternarMenu(false); });
  }

  // ---- Confirmación de acciones destructivas
  document.addEventListener("submit", function (e) {
    var msg = e.target.getAttribute && e.target.getAttribute("data-confirmar");
    if (msg && !window.confirm(msg)) e.preventDefault();
  });

  // ---- CAPTCHA: pedir un código nuevo
  var nuevo = document.getElementById("captcha-nuevo");
  if (nuevo) {
    nuevo.addEventListener("click", function () {
      fetch(nuevo.dataset.url, { headers: { Accept: "application/json" }, cache: "no-store" })
        .then(function (r) { return r.json(); })
        .then(function (d) {
          document.getElementById("captcha-img").innerHTML = d.svg;
          document.getElementById("captcha_token").value = d.token;
          var campo = document.getElementById("captcha"); campo.value = ""; campo.focus();
        });
    });
  }

  // ---- Vista previa PDF: imprimir
  var imprimir = document.getElementById("btn-imprimir");
  if (imprimir) {
    imprimir.addEventListener("click", function () {
      var visor = document.getElementById("visor-pdf");
      try { visor.contentWindow.focus(); visor.contentWindow.print(); } catch (e) { window.open(visor.src, "_blank"); }
    });
  }
})();

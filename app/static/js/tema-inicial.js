// Se ejecuta antes de pintar: el tema por defecto es CLARO; solo pasa a oscuro si el usuario lo eligió.
try { document.documentElement.dataset.tema = localStorage.getItem("tema") === "dark" ? "dark" : "light"; }
catch (e) { document.documentElement.dataset.tema = "light"; }

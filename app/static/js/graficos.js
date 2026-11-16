(function () {
  "use strict";
  var PALETA = ["#4f46e5", "#0ea5e9", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#14b8a6", "#f97316", "#64748b", "#ec4899", "#84cc16", "#06b6d4"];
  var graficos = [];
  function css(nombre) { return getComputedStyle(document.documentElement).getPropertyValue(nombre).trim(); }

  function crear(canvas) {
    var g = JSON.parse(canvas.getAttribute("data-grafico"));
    var caja = canvas.parentElement, horizontal = g.tipo === "barh", n = g.etiquetas.length;
    caja.style.height = (g.tipo === "pie" ? 320 : horizontal ? Math.max(260, 40 + n * 26) : 320) + "px";
    var multi = g.series.length > 1;
    var datasets = g.series.map(function (s, i) {
      return { label: s.nombre, data: s.valores,
               backgroundColor: g.tipo === "pie" || (!multi && horizontal) ? g.etiquetas.map(function (_, j) { return PALETA[j % PALETA.length]; }) : PALETA[i % PALETA.length],
               borderWidth: g.tipo === "pie" ? 2 : 0 };
    });
    var texto = css("--texto"), rejilla = css("--borde");
    var config = {
      type: g.tipo === "pie" ? "pie" : "bar",
      data: { labels: g.etiquetas, datasets: datasets },
      options: {
        responsive: true, maintainAspectRatio: false, indexAxis: horizontal ? "y" : "x",
        plugins: { legend: { display: g.tipo === "pie" || multi, position: g.tipo === "pie" ? "right" : "bottom", labels: { color: texto } } },
        scales: g.tipo === "pie" ? {} : {
          x: { ticks: { color: texto }, grid: { color: rejilla }, beginAtZero: true },
          y: { ticks: { color: texto, precision: 0 }, grid: { color: rejilla }, beginAtZero: true } }
      }
    };
    if (g.tipo === "pie") config.options.borderColor = css("--superficie");
    graficos.push({ canvas: canvas, chart: new Chart(canvas, config) });
  }
  document.querySelectorAll("canvas[data-grafico]").forEach(crear);
  document.addEventListener("tema-cambiado", function () {      // re-colorear al cambiar de tema
    graficos.forEach(function (x) {
      var o = x.chart.options, t = css("--texto"), r = css("--borde");
      if (o.plugins.legend.labels) o.plugins.legend.labels.color = t;
      ["x", "y"].forEach(function (ejes) { if (o.scales[ejes]) { o.scales[ejes].ticks.color = t; o.scales[ejes].grid.color = r; } });
      x.chart.update();
    });
  });
})();

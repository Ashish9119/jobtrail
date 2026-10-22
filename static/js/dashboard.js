(function () {
  var dataEl = document.getElementById("chart-data");
  var canvas = document.getElementById("trend-chart");
  if (!dataEl || !canvas || !window.Chart) return;

  var data = JSON.parse(dataEl.textContent);
  var css = getComputedStyle(document.documentElement);
  var accent = css.getPropertyValue("--accent").trim();
  var interview = css.getPropertyValue("--interview").trim();

  new Chart(canvas, {
    type: "bar",
    data: {
      labels: data.labels,
      datasets: [
        { type: "bar", label: "Applications", data: data.applications, backgroundColor: accent, borderRadius: 3 },
        { type: "line", label: "Reached an interview", data: data.interviews, borderColor: interview, backgroundColor: interview, tension: 0.25, pointRadius: 3 },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
      plugins: { legend: { position: "bottom" } },
    },
  });
})();

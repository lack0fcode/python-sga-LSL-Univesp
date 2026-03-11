document.addEventListener('DOMContentLoaded', function () {
  const rangeSelect = document.getElementById('range-select');
  const kpiQueue = document.getElementById('kpi-queue');
  const kpiAvgWait = document.getElementById('kpi-avg-wait');
  const kpiP95 = document.getElementById('kpi-p95-wait');
  const kpiAbandon = document.getElementById('kpi-abandonment');

  const throughputCtx = document.getElementById('chart-throughput').getContext('2d');
  const breakdownCtx = document.getElementById('chart-breakdown').getContext('2d');

  let throughputChart = null;
  let breakdownChart = null;

  function formatMinutes(seconds) {
    if (seconds === null || seconds === undefined) return '—';
    return (seconds / 60).toFixed(1);
  }

  async function fetchOverview(days) {
    const params = new URLSearchParams();
    params.set('start', new Date(Date.now() - days * 24 * 60 * 60 * 1000).toISOString());
    params.set('end', new Date().toISOString());
    const res = await fetch(`/administrador/dashboard-analise/api/?${params.toString()}`);
    return await res.json();
  }

  function renderThroughput(chartData) {
    const labels = chartData.map(d => new Date(d.day).toLocaleDateString());
    const data = chartData.map(d => d.count);
    const cfg = {
      type: 'line',
      data: { labels, datasets: [{ label: 'Senhas geradas', data, borderColor: '#17a2b8', backgroundColor: 'rgba(23,162,184,0.1)', fill: true }] },
      options: { responsive: true, maintainAspectRatio: false }
    };
    if (throughputChart) throughputChart.destroy();
    throughputChart = new Chart(throughputCtx, cfg);
  }

  function renderBreakdown(obj) {
    const labels = ['Priority', 'Normal'];
    const data = [obj.priority || 0, obj.normal || 0];
    const cfg = { type: 'doughnut', data: { labels, datasets: [{ data, backgroundColor: ['#dc3545', '#28a745'] }] }, options: { responsive: true, maintainAspectRatio: false } };
    if (breakdownChart) breakdownChart.destroy();
    breakdownChart = new Chart(breakdownCtx, cfg);
  }

  async function refresh(days) {
    const overview = await fetchOverview(days);
    // KPIs
    kpiQueue.textContent = overview.current_queue_length ?? '—';
    kpiAvgWait.textContent = formatMinutes(overview.avg_wait_seconds);
    kpiP95.textContent = formatMinutes(overview.p95_wait_seconds);
    kpiAbandon.textContent = overview.abandonment_rate != null ? (overview.abandonment_rate * 100).toFixed(1) + '%' : '—';
    // Charts
    if (overview.throughput) renderThroughput(overview.throughput);
    if (overview.queue_breakdown) renderBreakdown(overview.queue_breakdown);
  }

  // initialize Chart.js if available
  if (typeof Chart === 'undefined') {
    const s = document.createElement('script');
    s.src = 'https://cdn.jsdelivr.net/npm/chart.js';
    s.onload = () => refresh(parseInt(rangeSelect.value, 10));
    document.head.appendChild(s);
  } else {
    refresh(parseInt(rangeSelect.value, 10));
  }

  rangeSelect.addEventListener('change', function () {
    refresh(parseInt(this.value, 10));
  });
});

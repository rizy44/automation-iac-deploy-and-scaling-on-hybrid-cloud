(function () {
  const BASE_URL = (window.BACKEND_BASE_URL || 'http://localhost:8000').replace(/\/$/, '');

  async function fetchStacks() {
    const res = await fetch(`${BASE_URL}/scaling/stacks`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  }

  function pricePerHour(type) {
    const m = (type || '').toLowerCase();
    const table = {
      't3.micro': 0.0104,
      't3.medium': 0.0416,
      'm5.large': 0.096,
      'c5.xlarge': 0.17,
      'r5.xlarge': 0.252,
      'i3.xlarge': 0.312
    };
    if (table[m]) return table[m];
    // fallback by family
    if (m.startsWith('t3.')) return 0.02;
    if (m.startsWith('m5.')) return 0.12;
    if (m.startsWith('c5.')) return 0.2;
    if (m.startsWith('r5.')) return 0.25;
    if (m.startsWith('i3.')) return 0.3;
    return 0.1;
  }

  function dollars(v) {
    return `$${(Math.round(v * 100) / 100).toLocaleString()}`;
  }

  function drawBarChart(canvas, data) {
    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    const max = Math.max(...data, 1);
    const padding = 24;
    const barW = (w - padding * 2) / data.length - 10;
    data.forEach((v, i) => {
      const x = padding + i * (barW + 10);
      const barH = (h - padding * 2) * (v / max);
      const y = h - padding - barH;
      ctx.fillStyle = '#22c55e';
      ctx.fillRect(x, y, barW, barH);
      ctx.globalAlpha = 0.25;
      ctx.fillStyle = '#94a3b8';
      ctx.fillRect(x, y + barH, barW, 2);
      ctx.globalAlpha = 1;
    });
  }

  function setGauge(percent) {
    const clamp = Math.max(0, Math.min(100, Math.round(percent)));
    const gauge = document.getElementById('utilGauge');
    const span = document.getElementById('utilPercent');
    if (gauge) {
      gauge.style.setProperty('--p', `${clamp}`);
    }
    if (span) span.textContent = `${clamp}%`;
  }

  function setZeroState() {
    const zero = '$0';
    const ids = ['kpiBilling', 'kpiSavings', 'kpiToday', 'kpiEfficiency', 'totalSavings', 'costCompute', 'costStorage', 'costDb', 'costNet'];
    ids.forEach((id) => {
      const el = document.getElementById(id);
      if (!el) return;
      if (id === 'kpiEfficiency') el.textContent = '0%';
      else el.textContent = zero;
    });
    setGauge(0);
    const canvas = document.getElementById('barChart');
    if (canvas) drawBarChart(canvas, [0, 0, 0, 0]);
  }

  async function init() {
    try {
      const data = await fetchStacks();
      const stacks = data.stacks || [];
      // Aggregate
      let monthly = 0;
      let desiredSum = 0;
      let currentSum = 0;
      stacks.forEach((s) => {
        const ctx = (s && s.metadata && s.metadata.context) || {};
        const type = ctx.instance_type || 't3.micro';
        const desired = ctx.instance_count || 0;
        const current = s.current_instance_count || desired;
        const pph = pricePerHour(type);
        monthly += pph * 730 * current;
        desiredSum += desired;
        currentSum += current;
      });

      // KPIs
      const billing = monthly;
      const today = monthly / 30;
      const baseline = currentSum * pricePerHour('t3.micro') * 730;
      const savings = Math.max(0, baseline - monthly);
      const efficiency = desiredSum ? (currentSum / desiredSum) * 100 : 100;
      document.getElementById('kpiBilling').textContent = dollars(billing);
      document.getElementById('kpiSavings').textContent = dollars(savings);
      document.getElementById('kpiToday').textContent = dollars(today);
      document.getElementById('kpiEfficiency').textContent = `${Math.round(efficiency)}%`;
      document.getElementById('totalSavings').textContent = dollars(savings);
      setGauge(efficiency);

      // Chart numbers
      const compute = billing;
      const storage = Math.max(50, billing * 0.35);
      const db = Math.max(40, billing * 0.3);
      const net = Math.max(30, billing * 0.25);
      document.getElementById('costCompute').textContent = dollars(compute);
      document.getElementById('costStorage').textContent = dollars(storage);
      document.getElementById('costDb').textContent = dollars(db);
      document.getElementById('costNet').textContent = dollars(net);
      const canvas = document.getElementById('barChart');
      drawBarChart(canvas, [compute, storage, db, net]);
    } catch (e) {
      console.error(e);
      setZeroState();
    }
  }

  init();
})();



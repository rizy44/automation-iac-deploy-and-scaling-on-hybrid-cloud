(function () {
  const BASE_URL = (window.BACKEND_BASE_URL || 'http://localhost:8000').replace(/\/$/, '');
  const projectSelect = document.getElementById('projectSelect');
  const currentCountEl = document.getElementById('currentCount');
  const targetCountEl = document.getElementById('targetCount');
  const reasonInput = document.getElementById('reasonInput');
  const applyBtn = document.getElementById('applyScaleBtn');
  const stackInfo = document.getElementById('stackInfo');
  const historyContainer = document.getElementById('historyContainer');
  const scaleResult = document.getElementById('scaleResult');
  const incBtn = document.getElementById('increaseBtn');
  const decBtn = document.getElementById('decreaseBtn');

  let stacks = [];

  async function fetchStacks() {
    const res = await fetch(`${BASE_URL}/scaling/stacks`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  }

  async function fetchStackInfo(stackId) {
    const res = await fetch(`${BASE_URL}/scaling/stack/${encodeURIComponent(stackId)}/info`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  }

  async function scaleStack(stackId, target, reason) {
    const res = await fetch(`${BASE_URL}/scaling/stack/scale`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ stack_id: stackId, target_count: target, reason })
    });
    const contentType = res.headers.get('content-type') || '';
    const isJson = contentType.includes('application/json');
    const body = isJson ? await res.json() : await res.text();
    if (!res.ok) {
      const detail = (body && body.detail) || body;
      throw detail;
    }
    return body;
  }

  function populateProjects(list) {
    projectSelect.innerHTML = '';
    for (const p of list) {
      const id = p.stack_id || p.stackId || '';
      const name = (p.metadata && p.metadata.context && p.metadata.context.name_prefix) || id;
      const opt = document.createElement('option');
      opt.value = id; opt.textContent = `${name} (${id})`;
      projectSelect.appendChild(opt);
    }
  }

  function renderStackDetails(info) {
    const s = info.stack || info;
    const ctx = (s && s.metadata && s.metadata.context) || {};
    const items = [
      s.stack_id ? `<div><strong>Stack ID:</strong> ${s.stack_id}</div>` : '',
      ctx.name_prefix ? `<div><strong>Project:</strong> ${ctx.name_prefix}</div>` : '',
      s.region ? `<div><strong>Region:</strong> ${s.region}</div>` : '',
      s.current_instance_count != null ? `<div><strong>Instances:</strong> ${s.current_instance_count}</div>` : '',
      s.nlb_dns ? `<div><strong>NLB:</strong> ${s.nlb_dns}</div>` : '',
      s.deployed_at ? `<div><strong>Deployed:</strong> ${s.deployed_at}</div>` : '',
    ].filter(Boolean).join(' ');
    stackInfo.innerHTML = `<div style="display:flex; gap:12px; flex-wrap:wrap; color:#334155;">${items}</div>`;
  }

  function renderHistory(info) {
    const s = info.stack || info;
    const meta = (s && s.metadata) || {};
    const history = Array.isArray(meta.scaling_history) ? [...meta.scaling_history] : [];
    if (!history.length) {
      historyContainer.innerHTML = `<div style="color:#64748b;">No scaling history.</div>`;
      return;
    }
    history.sort((a, b) => (b.timestamp || '').localeCompare(a.timestamp || ''));
    const rows = history.map((h) => {
      const ts = h.timestamp || '';
      const action = h.action || '';
      const oldc = h.old_count ?? '';
      const newc = h.new_count ?? '';
      const reason = h.reason || '';
      return (
        `<tr>` +
          `<td style=\"padding:8px; white-space:nowrap;\">${ts}</td>` +
          `<td style=\"padding:8px; text-transform:capitalize;\">${action}</td>` +
          `<td style=\"padding:8px;\">${oldc} → ${newc}</td>` +
          `<td style=\"padding:8px;\">${reason}</td>` +
        `</tr>`
      );
    });
    historyContainer.innerHTML = (
      `<table style=\"width:100%; border-collapse:collapse;\">` +
        `<thead>` +
          `<tr>` +
            `<th style=\"text-align:left; padding:8px;\">Time</th>` +
            `<th style=\"text-align:left; padding:8px;\">Action</th>` +
            `<th style=\"text-align:left; padding:8px;\">Count</th>` +
            `<th style=\"text-align:left; padding:8px;\">Reason</th>` +
          `</tr>` +
        `</thead>` +
        `<tbody>${rows.join('')}</tbody>` +
      `</table>`
    );
  }

  function renderScaleResultSuccess(res) {
    const oldc = res.old_count ?? '';
    const newc = res.new_count ?? '';
    const action = res.action || '';
    scaleResult.innerHTML = `
      <div style="color:#14532d; background:#dcfce7; border:1px solid #86efac; padding:12px; border-radius:10px;">
        <div><strong>Success:</strong> ${action ? action.replace('_',' ') : 'scaled'} (${oldc} → ${newc})</div>
      </div>
    `;
  }

  function renderScaleResultError(err) {
    let message = typeof err === 'string' ? err : (err && err.error) || 'Scaling failed';
    const logs = err && err.logs && (err.logs.apply || err.logs.init || '');
    scaleResult.innerHTML = `
      <div style="color:#7f1d1d; background:#fee2e2; border:1px solid #fecaca; padding:12px; border-radius:10px;">
        <div style="margin-bottom:8px;"><strong>Error:</strong> ${message}</div>
        ${logs ? `<details><summary style="cursor:pointer;">Show Terraform logs</summary><pre style="white-space:pre-wrap; overflow:auto; max-height:280px;">${logs.replace(/[\u00A0]/g,' ')}</pre></details>` : ''}
      </div>
    `;
  }

  async function onProjectChange() {
    const id = projectSelect.value;
    if (!id) return;
    stackInfo.innerHTML = 'Loading...';
    try {
      const info = await fetchStackInfo(id);
      const stack = info.stack || info;
      const count = (stack && (stack.current_instance_count ?? (Array.isArray(stack.instances) ? stack.instances.length : undefined))) || 1;
      currentCountEl.value = String(count);
      targetCountEl.value = String(count);
      renderStackDetails(info);
      renderHistory(info);
    } catch (e) {
      stackInfo.innerHTML = `<div style="color:#b91c1c;">Failed to load: ${e && e.message ? e.message : e}</div>`;
      if (historyContainer) historyContainer.innerHTML = `<div style=\"color:#b91c1c;\">Failed to load history.</div>`;
    }
  }

  projectSelect.addEventListener('change', onProjectChange);
  incBtn.addEventListener('click', () => {
    const v = parseInt(targetCountEl.value || '1', 10) + 1;
    targetCountEl.value = String(v);
  });
  decBtn.addEventListener('click', () => {
    const v = Math.max(1, parseInt(targetCountEl.value || '1', 10) - 1);
    targetCountEl.value = String(v);
  });
  applyBtn.addEventListener('click', async () => {
    const id = projectSelect.value;
    const target = parseInt(targetCountEl.value, 10);
    const reason = reasonInput.value.trim() || undefined;
    if (!id || !target || target < 1) return;
    applyBtn.disabled = true;
    applyBtn.textContent = 'Scaling...';
    try {
      const res = await scaleStack(id, target, reason);
      renderScaleResultSuccess(res);
      await onProjectChange();
    } catch (e) {
      renderScaleResultError(e);
    } finally {
      applyBtn.disabled = false;
      applyBtn.textContent = 'Apply Scaling';
    }
  });

  (async function init() {
    try {
      const data = await fetchStacks();
      stacks = data.stacks || [];
      populateProjects(stacks);
      if (stacks.length) {
        projectSelect.value = stacks[0].stack_id || stacks[0].stackId;
        onProjectChange();
      } else {
        stackInfo.innerHTML = '<div style="color:#64748b;">No active projects.</div>';
      }
    } catch (e) {
      stackInfo.innerHTML = `<div style="color:#b91c1c;">Failed to list stacks: ${e && e.message ? e.message : e}</div>`;
    }
  })();
})();



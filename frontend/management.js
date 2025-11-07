(function () {
  const BASE_URL = (window.BACKEND_BASE_URL || 'http://localhost:8000').replace(/\/$/, '');
  const refreshBtn = document.getElementById('refreshProjects');
  const tableBody = document.getElementById('projectsTableBody');
  const instancesContainer = document.getElementById('instancesContainer');
  const selectedProjectLabel = document.getElementById('selectedProjectLabel');
  let currentStackId = '';
  let currentRegion = '';

  async function fetchProjects() {
    const res = await fetch(`${BASE_URL}/elb/projects`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  }

  async function fetchInstances(stackId) {
    const res = await fetch(`${BASE_URL}/ec2/stack/${encodeURIComponent(stackId)}/instances`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  }

  async function startInstance(instanceId, region) {
    const res = await fetch(`${BASE_URL}/ec2/instance/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ instance_id: instanceId, region })
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  }

  async function stopInstance(instanceId, region) {
    const res = await fetch(`${BASE_URL}/ec2/instance/stop`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ instance_id: instanceId, region })
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  }

  function renderProjects(projects) {
    if (!Array.isArray(projects) || projects.length === 0) {
      tableBody.innerHTML = `<tr><td colspan="5" style="padding:8px; color:#64748b;">No projects found</td></tr>`;
      return;
    }

    const rows = projects.map((p) => {
      const id = p.stack_id || p.stackId || '';
      const region = p.region || (p.metadata && p.metadata.region) || '';
      const instCount = p.current_instance_count ?? (Array.isArray(p.instances) ? p.instances.length : '');
      const nlb = p.nlb_dns || p.nlb_dns_name || '';
      const name = (p.metadata && p.metadata.context && p.metadata.context.name_prefix) || id;
      return (
        `<tr>` +
          `<td style="padding:8px; white-space:nowrap;">${name}</td>` +
          `<td style="padding:8px;">${region || ''}</td>` +
          `<td style="padding:8px;">${instCount || 0}</td>` +
          `<td style="padding:8px;">${nlb || ''}</td>` +
          `<td style="padding:8px;">` +
            `<button class="btn btn-secondary" data-action="view" data-id="${id}">View Instances</button>` +
          `</td>` +
        `</tr>`
      );
    });
    tableBody.innerHTML = rows.join('');
  }

  function renderInstances(stackId, data) {
    selectedProjectLabel.textContent = stackId ? `Project: ${stackId}` : '';
    currentStackId = stackId;
    currentRegion = (data && data.stack_info && data.stack_info.region) || '';

    if (!data || !Array.isArray(data.instances) || data.instances.length === 0) {
      instancesContainer.innerHTML = `<div style="color:#64748b;">No instances found for this project.</div>`;
      return;
    }

    const items = data.instances.map((inst, idx) => {
      const id = inst.instance_id || inst.id || '';
      const ip = inst.public_ip || inst.ip || '';
      const dns = inst.public_dns || inst.dns || '';
      const status = inst.status || '';
      const canStart = status === 'stopped' || status === 'stopping' || status === 'terminated';
      const canStop = status === 'running' || status === 'pending';
      return (
        `<div style="padding:8px; border:1px solid #e2e8f0; border-radius:8px; margin-bottom:8px;">` +
          `<div style="display:flex; gap:12px; flex-wrap:wrap; align-items:center;">` +
            `<div><strong>#${idx + 1}</strong></div>` +
            `<div><strong>ID:</strong> ${id}</div>` +
            (ip ? `<div><strong>IP:</strong> ${ip}</div>` : '') +
            (dns ? `<div><strong>DNS:</strong> ${dns}</div>` : '') +
            (status ? `<div><strong>Status:</strong> ${status}</div>` : '') +
            `<span style="margin-left:auto; display:flex; gap:8px;">` +
              `<button class="btn btn-secondary" data-action="start" data-id="${id}" ${canStart ? '' : 'disabled'}>Start</button>` +
              `<button class="btn" style="background:#ef4444; color:#fff;" data-action="stop" data-id="${id}" ${canStop ? '' : 'disabled'}>Stop</button>` +
            `</span>` +
          `</div>` +
        `</div>`
      );
    });

    // Stack info header
    const hdr = data.stack_info || {};
    const meta = hdr || {};
    const extra = [
      hdr.region ? `<div><strong>Region:</strong> ${hdr.region}</div>` : '',
      hdr.nlb_dns ? `<div><strong>NLB:</strong> ${hdr.nlb_dns}</div>` : '',
      meta.deployed_at ? `<div><strong>Deployed:</strong> ${meta.deployed_at}</div>` : '',
    ].filter(Boolean).join(' ');

    instancesContainer.innerHTML = (
      (extra ? `<div style="margin-bottom:8px; color:#334155; display:flex; gap:12px; flex-wrap:wrap;">${extra}</div>` : '') +
      items.join('')
    );
  }

  async function refresh() {
    try {
      tableBody.innerHTML = `<tr><td colspan="5" style="padding:8px;">Loading...</td></tr>`;
      const data = await fetchProjects();
      renderProjects(data.projects || []);
    } catch (e) {
      tableBody.innerHTML = `<tr><td colspan="5" style="padding:8px; color:#b91c1c;">Failed to load projects: ${e && e.message ? e.message : e}</td></tr>`;
    }
  }

  tableBody.addEventListener('click', async (e) => {
    const t = e.target;
    if (t && t.matches('button[data-action="view"]')) {
      const stackId = t.getAttribute('data-id');
      if (!stackId) return;
      instancesContainer.innerHTML = `<div>Loading instances...</div>`;
      try {
        const data = await fetchInstances(stackId);
        renderInstances(stackId, data);
      } catch (err) {
        instancesContainer.innerHTML = `<div style="color:#b91c1c;">Failed to load instances: ${err && err.message ? err.message : err}</div>`;
      }
    }
  });

  instancesContainer.addEventListener('click', async (e) => {
    const t = e.target;
    if (!t || !t.matches('button[data-action]')) return;
    const action = t.getAttribute('data-action');
    const instanceId = t.getAttribute('data-id');
    if (!instanceId) return;
    t.disabled = true;
    try {
      if (action === 'start') {
        await startInstance(instanceId, currentRegion);
      } else if (action === 'stop') {
        await stopInstance(instanceId, currentRegion);
      }
    } catch (err) {
      alert(`Action failed: ${err && err.message ? err.message : err}`);
    } finally {
      if (currentStackId) {
        try {
          const data = await fetchInstances(currentStackId);
          renderInstances(currentStackId, data);
        } catch (_) {}
      }
    }
  });

  if (refreshBtn) refreshBtn.addEventListener('click', refresh);
  refresh();
})();



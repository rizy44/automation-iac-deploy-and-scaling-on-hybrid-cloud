/* Simple front-end "AI" recommender using heuristics + BE integration */
(function () {
  const BASE_URL = (window.BACKEND_BASE_URL || 'http://localhost:8000').replace(/\/$/, '');
  const providerEl = document.getElementById('provider');
  const regionEl = document.getElementById('region');
  const vcpuEl = document.getElementById('vcpu');
  const memoryEl = document.getElementById('memory');
  const storageEl = document.getElementById('storage');
  const recommendBtn = document.getElementById('recommendBtn');
  const recommendationEl = document.getElementById('recommendation');
  const rationaleEl = document.getElementById('rationale');
  const formEl = document.getElementById('projectForm');
  const deployResult = document.getElementById('deployResult');
  const deployResultBody = document.getElementById('deployResultBody');
  const refreshBtn = document.getElementById('refreshProjects');
  const projectsList = document.getElementById('projectsList');

  const providerRegions = {
    aws: [
      { id: 'ap-southeast-1', name: 'Asia Pacific (Singapore)' },
      { id: 'ap-southeast-2', name: 'Asia Pacific (Sydney)' },
      { id: 'ap-northeast-1', name: 'Asia Pacific (Tokyo)' },
      { id: 'us-east-1', name: 'US East (N. Virginia)' },
      { id: 'eu-central-1', name: 'EU (Frankfurt)' },
    ],
    azure: [
      { id: 'southeastasia', name: 'Southeast Asia' },
      { id: 'australiaeast', name: 'Australia East' },
      { id: 'japaneast', name: 'Japan East' },
      { id: 'eastus', name: 'East US' },
      { id: 'westeurope', name: 'West Europe' },
    ],
    gcp: [
      { id: 'asia-southeast1', name: 'Singapore' },
      { id: 'australia-southeast1', name: 'Sydney' },
      { id: 'asia-northeast1', name: 'Tokyo' },
      { id: 'us-east1', name: 'South Carolina' },
      { id: 'europe-west3', name: 'Frankfurt' },
    ],
  };

  function populateRegions() {
    const selected = providerEl.value;
    const regions = providerRegions[selected] || [];
    regionEl.innerHTML = '';
    for (const r of regions) {
      const o = document.createElement('option');
      o.value = r.id; o.textContent = r.name;
      regionEl.appendChild(o);
    }
  }

  providerEl.addEventListener('change', populateRegions);
  populateRegions();

  // Heuristic-based recommender
  function recommendInstance(vcpu, memoryGb, storageGb) {
    if (!vcpu || !memoryGb || !storageGb) {
      return { type: '', rationale: 'Please enter vCPU, memory and storage to get a recommendation.' };
    }

    // Primary selection by workload focus
    const memPerVcpu = memoryGb / vcpu;
    const storageHeavy = storageGb >= 500;

    let family = 'm5'; // general purpose default
    if (storageHeavy) {
      family = 'i3'; // storage-optimized (NVMe)
    } else if (memPerVcpu > 6) {
      family = 'r5'; // memory-optimized
    } else if (memPerVcpu < 2.5) {
      family = 'c5'; // compute-optimized
    } else {
      family = 'm5'; // general purpose
    }

    // Choose size by vCPU requirement, then bump if memory is tight
    const sizeByVcpu = vcpu <= 2 ? 'large'
      : vcpu <= 4 ? 'xlarge'
      : vcpu <= 8 ? '2xlarge'
      : vcpu <= 16 ? '4xlarge'
      : vcpu <= 32 ? '8xlarge'
      : '12xlarge';

    // Approx memory per vCPU model (GB)
    const memPerVcpuByFamily = { c5: 2, m5: 4, r5: 8, i3: 8 };
    const approxPerVcpu = memPerVcpuByFamily[family] || 4;
    const approxMemoryForSize = (label) => {
      const vcpuForLabel = { large: 2, xlarge: 4, '2xlarge': 8, '4xlarge': 16, '8xlarge': 32, '12xlarge': 48 }[label] || 2;
      return vcpuForLabel * approxPerVcpu;
    };

    let chosen = sizeByVcpu;
    while (approxMemoryForSize(chosen) < memoryGb) {
      chosen = bumpSize(chosen);
      if (chosen === '32xlarge') break; // cap
    }

    const type = `${family}.${chosen}`;

    const rationaleParts = [];
    rationaleParts.push(`Requested vCPU: ${vcpu}, Memory: ${memoryGb} GB, Storage: ${storageGb} GB.`);
    if (family === 'i3') rationaleParts.push('High storage requirement detected → storage-optimized family (i3).');
    if (family === 'r5') rationaleParts.push('High memory per vCPU → memory-optimized family (r5).');
    if (family === 'c5') rationaleParts.push('Low memory per vCPU → compute-optimized family (c5).');
    if (family === 'm5') rationaleParts.push('Balanced requirements → general purpose family (m5).');
    rationaleParts.push(`Size selected to satisfy CPU and memory needs → ${chosen}.`);

    return { type, rationale: rationaleParts.join(' ') };
  }

  function bumpSize(label) {
    const order = ['large', 'xlarge', '2xlarge', '4xlarge', '8xlarge', '12xlarge', '16xlarge', '24xlarge', '32xlarge'];
    const idx = order.indexOf(label);
    return idx === -1 || idx === order.length - 1 ? label : order[idx + 1];
  }

  function triggerRecommendation() {
    const vcpu = parseInt(vcpuEl.value, 10);
    const mem = parseInt(memoryEl.value, 10);
    const stg = parseInt(storageEl.value, 10);
    const { type, rationale } = recommendInstance(vcpu, mem, stg);
    recommendationEl.value = type || '';
    rationaleEl.textContent = rationale;
  }

  // Auto-recommend when values change
  [vcpuEl, memoryEl, storageEl].forEach((el) => el.addEventListener('input', triggerRecommendation));
  if (recommendBtn) recommendBtn.addEventListener('click', triggerRecommendation);

  function computeAz(regionId) {
    return regionId ? `${regionId}a` : 'ap-southeast-2a';
  }

  async function deployProject(payload) {
    const url = `${BASE_URL}/elb/deploy`;
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const detail = await res.json().catch(() => ({}));
      throw new Error((detail && detail.detail) || `HTTP ${res.status}`);
    }
    return res.json();
  }

  function renderDeployResult(data) {
    const outputs = data.outputs || {};
    const nlb = outputs.nlb_dns_name || outputs.alb_dns_name || '';
    deployResultBody.innerHTML = `
      <div style="display:grid; gap:8px;">
        <div><strong>stack_id:</strong> ${data.stack_id || '(n/a)'}</div>
        <div><strong>phase:</strong> ${data.phase || '(n/a)'} </div>
        ${nlb ? `<div><strong>Load Balancer DNS:</strong> ${nlb}</div>` : ''}
        ${Array.isArray(outputs.instance_public_ip) ? `<div><strong>Instances IP:</strong> ${outputs.instance_public_ip.join(', ')}</div>` : ''}
      </div>
    `;
    deployResult.style.display = 'block';
  }

  function setSubmitting(isSubmitting) {
    const btn = formEl.querySelector('button[type="submit"]');
    if (btn) btn.disabled = isSubmitting;
  }

  formEl.addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
      setSubmitting(true);
      deployResult.style.display = 'none';
      deployResultBody.textContent = '';

      const projectName = document.getElementById('projectName').value.trim();
      const region = regionEl.value;
      const instanceType = recommendationEl.value || 't3.micro';
      const az = computeAz(region);

      const payload = {
        region,
        vpc_cidr: '10.25.0.0/16',
        subnet_cidr: '10.25.1.0/24',
        az,
        name_prefix: projectName || 'proj',
        instance_count: 2,
        ami: 'ami-0a25a306450a2cba3',
        instance_type: instanceType,
        user_data_inline: null,
        user_data_path: null,
        auto_install_monitoring: true,
      };

      const data = await deployProject(payload);
      renderDeployResult(data);
      await refreshProjectsList();
    } catch (err) {
      deployResultBody.innerHTML = `<div style=\"color:#b91c1c;\">Deploy failed: ${err && err.message ? err.message : err}</div>`;
      deployResult.style.display = 'block';
    } finally {
      setSubmitting(false);
    }
  });

  async function fetchProjects() {
    const url = `${BASE_URL}/elb/projects`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  }

  async function refreshProjectsList() {
    try {
      projectsList.innerHTML = '<li>Loading...</li>';
      const data = await fetchProjects();
      const items = (data.projects || []).map((p) => {
        const id = p.stack_id || p.stackId || '';
        const nlb = p.nlb_dns || p.nlb_dns_name || '';
        return `<li style=\"margin: 6px 0;\">` +
               `<strong>${id}</strong>${nlb ? ` — <span style=\\\"color:#334155\\\">${nlb}</span>` : ''}` +
               `</li>`;
      });
      projectsList.innerHTML = items.length ? items.join('') : '<li>No active projects</li>';
    } catch (err) {
      projectsList.innerHTML = `<li style=\"color:#b91c1c;\">Failed to load projects: ${err && err.message ? err.message : err}</li>`;
    }
  }

  if (refreshBtn) refreshBtn.addEventListener('click', refreshProjectsList);
  refreshProjectsList();
})();



# API Documentation for Frontend - VPBank Hybrid Cloud Platform

## Base URL
```
http://localhost:8008
```

## Authentication
Currently no authentication required (add later if needed)

---

## 📦 1. ELB Deployment APIs

### 1.1 Deploy Infrastructure with Monitoring

**Endpoint:** `POST /elb/deploy`

**Description:** Deploy VPC, EC2 instances, and NLB with optional auto-monitoring stack installation

**Request Body:**
```json
{
  "region": "ap-southeast-2",
  "vpc_cidr": "10.100.0.0/16",
  "subnet_cidr": "10.100.1.0/24",
  "az": "ap-southeast-2a",
  "name_prefix": "my-app",
  "key_name": "my-key",
  "instance_count": 2,
  "ami": "ami-0eeab253db7e765a9",
  "instance_type": "t3.medium",
  "auto_install_monitoring": true,
  "user_data_inline": null
}
```

**Request Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| region | string | Yes | AWS region (e.g., "ap-southeast-2") |
| vpc_cidr | string | Yes | VPC CIDR block (e.g., "10.100.0.0/16") |
| subnet_cidr | string | Yes | Subnet CIDR (e.g., "10.100.1.0/24") |
| az | string | Yes | Availability zone (e.g., "ap-southeast-2a") |
| name_prefix | string | Yes | Prefix for resource names |
| key_name | string | Yes | SSH key pair name |
| instance_count | integer | Yes | Number of EC2 instances (≥1) |
| ami | string | Yes | AMI ID for Ubuntu 20.04/22.04 |
| instance_type | string | Yes | EC2 instance type (e.g., "t3.medium") |
| auto_install_monitoring | boolean | No | Auto-install Grafana+Mimir+Loki (default: true) |
| user_data_inline | string | No | Custom user data script (overrides auto_install) |
| user_data_path | string | No | Path to user data file |

**Success Response (200 OK):**
```json
{
  "phase": "APPLIED",
  "stack_id": "20251104213408-c3c57ad5",
  "logs": {
    "init": "Terraform init output...",
    "apply": "Terraform apply output...",
    "output": "Terraform output..."
  },
  "outputs": {
    "nlb_dns_name": {
      "value": "my-app-nlb-xxx.elb.ap-southeast-2.amazonaws.com"
    },
    "instance_public_ip": {
      "value": ["3.123.45.67", "3.123.45.68"]
    },
    "instance_dns": {
      "value": ["ec2-3-123-45-67.compute.amazonaws.com"]
    }
  }
}
```

**Error Response (500):**
```json
{
  "phase": "FAILED_CREDENTIALS",
  "error": "Missing AWS creds in .env",
  "stack_id": "20251104213408-c3c57ad5"
}
```

**Frontend Usage:**
```javascript
async function deployInfrastructure(config) {
  const response = await fetch('http://localhost:8008/elb/deploy', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config)
  });
  const data = await response.json();
  
  if (data.phase === 'APPLIED') {
    return {
      stackId: data.stack_id,
      nlbDns: data.outputs.nlb_dns_name.value,
      instanceIps: data.outputs.instance_public_ip.value
    };
  } else {
    throw new Error(data.error || 'Deployment failed');
  }
}
```

---

## 🔄 2. Scaling Management APIs

### 2.1 List All Stacks

**Endpoint:** `GET /scaling/stacks`

**Description:** Get list of all deployed stacks with current instance counts

**Success Response (200 OK):**
```json
{
  "success": true,
  "count": 2,
  "stacks": [
    {
      "stack_id": "20251104213408-c3c57ad5",
      "current_instance_count": 2,
      "instances": ["3.123.45.67", "3.123.45.68"],
      "nlb_dns": "my-app-nlb-xxx.elb.ap-southeast-2.amazonaws.com",
      "deployed_at": "2025-11-04 21:34:08",
      "region": "ap-southeast-2",
      "metadata": {...}
    }
  ]
}
```

**Frontend Usage:**
```javascript
async function getAllStacks() {
  const response = await fetch('http://localhost:8008/scaling/stacks');
  const data = await response.json();
  return data.stacks;
}
```

**Display Example:**
- Show table with columns: Stack ID, Instance Count, Region, Deployed At
- Add action buttons: View Details, Scale, Get Metrics

---

### 2.2 Get Stack Details

**Endpoint:** `GET /scaling/stack/{stack_id}/info`

**Description:** Get detailed information about a specific stack

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| stack_id | string | Stack identifier (e.g., "20251104213408-c3c57ad5") |

**Success Response (200 OK):**
```json
{
  "success": true,
  "stack": {
    "stack_id": "20251104213408-c3c57ad5",
    "current_instance_count": 2,
    "instances": ["3.123.45.67", "3.123.45.68"],
    "nlb_dns": "my-app-nlb-xxx.elb.ap-southeast-2.amazonaws.com",
    "deployed_at": "2025-11-04 21:34:08",
    "region": "ap-southeast-2",
    "metadata": {
      "stack_id": "20251104213408-c3c57ad5",
      "deployed_at": "2025-11-04 21:34:08",
      "last_scaled_at": "2025-11-04 22:15:30",
      "last_scale_reason": "AI Auto-scale: High CPU usage",
      "context": {
        "instance_count": 2,
        "instance_type": "t3.medium",
        "name_prefix": "my-app"
      }
    }
  }
}
```

**Error Response (404):**
```json
{
  "detail": "Stack 20251104213408-c3c57ad5 not found"
}
```

**Frontend Usage:**
```javascript
async function getStackDetails(stackId) {
  const response = await fetch(`http://localhost:8008/scaling/stack/${stackId}/info`);
  if (!response.ok) throw new Error('Stack not found');
  const data = await response.json();
  return data.stack;
}
```

---

### 2.3 Get Stack Metrics

**Endpoint:** `GET /scaling/stack/{stack_id}/metrics`

**Description:** Get current CPU, memory usage from monitoring stack

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| stack_id | string | Stack identifier |

**Success Response (200 OK):**
```json
{
  "success": true,
  "stack_id": "20251104213408-c3c57ad5",
  "metrics": {
    "avg_cpu_percent": 45.23,
    "avg_memory_percent": 62.15,
    "instance_count": 2
  },
  "mimir_url": "http://my-app-nlb-xxx.elb.ap-southeast-2.amazonaws.com/mimir",
  "query_time": "2025-11-04T12:34:56.789Z"
}
```

**Error Response (if metrics unavailable):**
```json
{
  "success": false,
  "error": "NLB DNS not found for stack",
  "stack_id": "20251104213408-c3c57ad5",
  "metrics": {}
}
```

**Frontend Usage:**
```javascript
async function getMetrics(stackId) {
  const response = await fetch(`http://localhost:8008/scaling/stack/${stackId}/metrics`);
  const data = await response.json();
  
  if (data.success) {
    return {
      cpu: data.metrics.avg_cpu_percent,
      memory: data.metrics.avg_memory_percent,
      instances: data.metrics.instance_count
    };
  }
  return null;
}

// Poll metrics every 30 seconds
setInterval(() => {
  getMetrics(stackId).then(metrics => {
    updateDashboard(metrics);
  });
}, 30000);
```

**UI Display:**
- CPU usage: Progress bar (green < 50%, yellow 50-70%, red > 70%)
- Memory usage: Progress bar (green < 60%, yellow 60-80%, red > 80%)
- Instance count: Badge/chip showing number

---

### 2.4 Manual Scale Stack

**Endpoint:** `POST /scaling/stack/scale`

**Description:** Manually scale stack to target instance count

**Request Body:**
```json
{
  "stack_id": "20251104213408-c3c57ad5",
  "target_count": 3,
  "reason": "Manual scale-up due to increased traffic"
}
```

**Request Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| stack_id | string | Yes | Stack identifier |
| target_count | integer | Yes | Desired number of instances (1-20) |
| reason | string | No | Reason for scaling |

**Success Response (200 OK):**
```json
{
  "success": true,
  "stack_id": "20251104213408-c3c57ad5",
  "old_count": 2,
  "new_count": 3,
  "action": "scale_up",
  "reason": "Manual scale-up due to increased traffic",
  "message": "Successfully scaled from 2 to 3 instances",
  "logs": {
    "apply": "Terraform apply output..."
  }
}
```

**Error Response (400):**
```json
{
  "detail": "target_count must be >= 1"
}
```

**Frontend Usage:**
```javascript
async function scaleStack(stackId, targetCount, reason) {
  const response = await fetch('http://localhost:8008/scaling/stack/scale', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      stack_id: stackId,
      target_count: targetCount,
      reason: reason
    })
  });
  
  const data = await response.json();
  
  if (data.success) {
    showNotification(`Scaled from ${data.old_count} to ${data.new_count} instances`);
  } else {
    showError(data.error);
  }
  
  return data;
}
```

**UI Components:**
```html
<!-- Scale Modal -->
<div class="scale-modal">
  <h3>Scale Stack: {stackId}</h3>
  <p>Current instances: {currentCount}</p>
  
  <input 
    type="number" 
    min="1" 
    max="20" 
    v-model="targetCount"
    placeholder="Target instance count"
  />
  
  <textarea 
    v-model="reason"
    placeholder="Reason for scaling (optional)"
  ></textarea>
  
  <button @click="scaleStack(stackId, targetCount, reason)">
    Scale
  </button>
</div>
```

---

### 2.5 Get AI Recommendation

**Endpoint:** `POST /scaling/stack/{stack_id}/recommend`

**Description:** Get AI-powered scaling recommendation without executing

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| stack_id | string | Stack identifier |

**Success Response (200 OK):**
```json
{
  "success": true,
  "stack_id": "20251104213408-c3c57ad5",
  "current_count": 2,
  "metrics": {
    "avg_cpu_percent": 78.5,
    "avg_memory_percent": 65.2,
    "instance_count": 2
  },
  "recommendation": {
    "action": "scale_up",
    "target_count": 3,
    "reason": "High CPU usage detected (78.5%), recommend adding instances to reduce load",
    "confidence": 0.92
  }
}
```

**Possible Actions:**
- `"scale_up"` - Add more instances
- `"scale_down"` - Remove instances
- `"no_change"` - No scaling needed

**Frontend Usage:**
```javascript
async function getAIRecommendation(stackId) {
  const response = await fetch(
    `http://localhost:8008/scaling/stack/${stackId}/recommend`,
    { method: 'POST' }
  );
  const data = await response.json();
  return data.recommendation;
}
```

**UI Display:**
```html
<!-- AI Recommendation Card -->
<div class="ai-recommendation" :class="recommendation.action">
  <div class="header">
    <span class="icon">🤖</span>
    <h4>AI Recommendation</h4>
    <span class="confidence">
      Confidence: {{ (recommendation.confidence * 100).toFixed(0) }}%
    </span>
  </div>
  
  <div class="action-badge" :class="recommendation.action">
    {{ recommendation.action.replace('_', ' ').toUpperCase() }}
  </div>
  
  <p class="reason">{{ recommendation.reason }}</p>
  
  <div class="metrics-summary">
    <div>CPU: {{ metrics.avg_cpu_percent.toFixed(1) }}%</div>
    <div>Memory: {{ metrics.avg_memory_percent.toFixed(1) }}%</div>
  </div>
  
  <div class="actions">
    <button 
      v-if="recommendation.action !== 'no_change'"
      @click="executeRecommendation(stackId, recommendation.target_count)"
      class="primary"
    >
      Execute: Scale to {{ recommendation.target_count }} instances
    </button>
    <button @click="refreshRecommendation">Refresh</button>
  </div>
</div>
```

**CSS Classes:**
```css
.ai-recommendation.scale_up { border-left: 4px solid #f59e0b; }
.ai-recommendation.scale_down { border-left: 4px solid #3b82f6; }
.ai-recommendation.no_change { border-left: 4px solid #10b981; }

.confidence {
  background: #e5e7eb;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.875rem;
}
```

---

### 2.6 Auto-Scale with AI

**Endpoint:** `POST /scaling/stack/{stack_id}/auto-scale`

**Description:** Get AI recommendation and auto-execute if confidence is high

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| stack_id | string | Stack identifier |

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| confidence_threshold | float | 0.7 | Minimum confidence to execute (0.0-1.0) |

**Success Response (Executed):**
```json
{
  "success": true,
  "executed": true,
  "stack_id": "20251104213408-c3c57ad5",
  "current_count": 2,
  "metrics": {
    "avg_cpu_percent": 85.3,
    "avg_memory_percent": 72.1,
    "instance_count": 2
  },
  "recommendation": {
    "action": "scale_up",
    "target_count": 3,
    "reason": "High CPU usage detected (85.3%)",
    "confidence": 0.95
  },
  "scaling_result": {
    "success": true,
    "old_count": 2,
    "new_count": 3,
    "action": "scale_up",
    "message": "Successfully scaled from 2 to 3 instances"
  }
}
```

**Success Response (Not Executed - Low Confidence):**
```json
{
  "success": true,
  "executed": false,
  "reason": "Confidence 0.65 below threshold 0.7",
  "recommendation": {
    "action": "scale_up",
    "target_count": 3,
    "confidence": 0.65
  }
}
```

**Frontend Usage:**
```javascript
async function autoScale(stackId, confidenceThreshold = 0.7) {
  const response = await fetch(
    `http://localhost:8008/scaling/stack/${stackId}/auto-scale?confidence_threshold=${confidenceThreshold}`,
    { method: 'POST' }
  );
  const data = await response.json();
  
  if (data.executed) {
    showNotification(
      `Auto-scaled: ${data.scaling_result.message}`,
      'success'
    );
  } else {
    showNotification(
      `Not executed: ${data.reason}`,
      'info'
    );
  }
  
  return data;
}
```

---

### 2.7 Query Custom Metrics

**Endpoint:** `POST /scaling/stack/metrics/query`

**Description:** Execute custom PromQL query against stack's Mimir

**Request Body:**
```json
{
  "stack_id": "20251104213408-c3c57ad5",
  "promql_query": "rate(http_requests_total[5m])"
}
```

**Success Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "resultType": "vector",
    "result": [
      {
        "metric": {
          "instance": "10.100.1.10:9100",
          "job": "node"
        },
        "value": [1699104896, "42.5"]
      }
    ]
  }
}
```

**Frontend Usage:**
```javascript
async function queryCustomMetric(stackId, promqlQuery) {
  const response = await fetch('http://localhost:8008/scaling/stack/metrics/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      stack_id: stackId,
      promql_query: promqlQuery
    })
  });
  return await response.json();
}

// Example: Query request rate
const result = await queryCustomMetric(
  stackId,
  'sum(rate(http_requests_total[5m]))'
);
```

---

## 🌐 3. SD-WAN Hybrid Cloud APIs

### 3.1 Deploy SD-WAN Architecture

**Endpoint:** `POST /sdwan/deploy`

**Description:** Deploy hybrid cloud with Transit Gateway and Site-to-Site VPN

**Request Body:**
```json
{
  "name_prefix": "vpbank-sdwan",
  "region": "ap-southeast-2",
  "azs": ["ap-southeast-2a", "ap-southeast-2b"],
  "openstack_cidr": "172.10.0.0/16",
  "openstack_public_ip": "203.0.113.50",
  "vpn_preshared_key": "your-secure-psk-here",
  "app_vpc_cidr": "10.1.0.0/16",
  "shared_vpc_cidr": "10.2.0.0/16",
  "app_ami": "ami-0eeab253db7e765a9",
  "app_instance_type": "t3.medium",
  "app_min_size": 2,
  "app_max_size": 10,
  "app_desired_size": 3
}
```

**Success Response (200 OK):**
```json
{
  "phase": "APPLIED",
  "stack_id": "20251104220000-xyz12345",
  "vpn_config_path": "/path/to/vpn-configuration.json",
  "outputs": {
    "vpn_gateway_id": {...},
    "transit_gateway_id": {...}
  }
}
```

---

## 📊 4. Frontend Dashboard Components

### 4.1 Stack List View

**Component:** `StackList.vue`

```javascript
<template>
  <div class="stack-list">
    <h2>Infrastructure Stacks</h2>
    
    <div class="filters">
      <input 
        v-model="searchQuery" 
        placeholder="Search stacks..."
      />
      <select v-model="filterRegion">
        <option value="">All Regions</option>
        <option value="ap-southeast-2">AP Southeast 2</option>
        <option value="us-east-1">US East 1</option>
      </select>
    </div>
    
    <table class="stacks-table">
      <thead>
        <tr>
          <th>Stack ID</th>
          <th>Region</th>
          <th>Instances</th>
          <th>Status</th>
          <th>Deployed</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="stack in filteredStacks" :key="stack.stack_id">
          <td>{{ stack.stack_id }}</td>
          <td>{{ stack.region }}</td>
          <td>
            <span class="badge">{{ stack.current_instance_count }}</span>
          </td>
          <td>
            <span class="status-badge running">Running</span>
          </td>
          <td>{{ formatDate(stack.deployed_at) }}</td>
          <td>
            <button @click="viewDetails(stack.stack_id)">Details</button>
            <button @click="getMetrics(stack.stack_id)">Metrics</button>
            <button @click="scale(stack.stack_id)">Scale</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
export default {
  data() {
    return {
      stacks: [],
      searchQuery: '',
      filterRegion: ''
    };
  },
  computed: {
    filteredStacks() {
      return this.stacks.filter(stack => {
        const matchesSearch = stack.stack_id.includes(this.searchQuery);
        const matchesRegion = !this.filterRegion || stack.region === this.filterRegion;
        return matchesSearch && matchesRegion;
      });
    }
  },
  async mounted() {
    await this.loadStacks();
    // Refresh every 30 seconds
    setInterval(() => this.loadStacks(), 30000);
  },
  methods: {
    async loadStacks() {
      const response = await fetch('http://localhost:8008/scaling/stacks');
      const data = await response.json();
      this.stacks = data.stacks;
    }
  }
};
</script>
```

---

### 4.2 Stack Details View

**Component:** `StackDetails.vue`

```javascript
<template>
  <div class="stack-details">
    <div class="header">
      <h2>Stack: {{ stackId }}</h2>
      <button @click="refresh">Refresh</button>
    </div>
    
    <div class="metrics-cards">
      <div class="metric-card">
        <h4>CPU Usage</h4>
        <div class="progress-bar">
          <div 
            class="progress" 
            :style="{ width: metrics.cpu + '%' }"
            :class="getCpuClass(metrics.cpu)"
          ></div>
        </div>
        <p>{{ metrics.cpu.toFixed(1) }}%</p>
      </div>
      
      <div class="metric-card">
        <h4>Memory Usage</h4>
        <div class="progress-bar">
          <div 
            class="progress" 
            :style="{ width: metrics.memory + '%' }"
            :class="getMemoryClass(metrics.memory)"
          ></div>
        </div>
        <p>{{ metrics.memory.toFixed(1) }}%</p>
      </div>
      
      <div class="metric-card">
        <h4>Instance Count</h4>
        <p class="large-number">{{ stack.current_instance_count }}</p>
      </div>
    </div>
    
    <div class="ai-recommendation-section">
      <button @click="getRecommendation">Get AI Recommendation</button>
      
      <div v-if="recommendation" class="recommendation-card">
        <!-- See section 2.5 for recommendation UI -->
      </div>
    </div>
    
    <div class="instances-list">
      <h3>Instances</h3>
      <ul>
        <li v-for="ip in stack.instances" :key="ip">
          {{ ip }}
        </li>
      </ul>
    </div>
  </div>
</template>
```

---

## 🔔 5. Real-time Updates

### WebSocket (Future Enhancement)

Currently use polling. For real-time updates, consider:

```javascript
// Poll metrics every 30 seconds
const pollMetrics = setInterval(async () => {
  const metrics = await getMetrics(stackId);
  updateUI(metrics);
}, 30000);

// Stop polling when component unmounts
onUnmounted(() => clearInterval(pollMetrics));
```

---

## 🎨 6. UI/UX Recommendations

### Color Scheme for Metrics
- **CPU < 50%**: Green (#10b981)
- **CPU 50-70%**: Yellow (#f59e0b)
- **CPU > 70%**: Red (#ef4444)

### Action Colors
- **Scale Up**: Orange (#f97316)
- **Scale Down**: Blue (#3b82f6)
- **No Change**: Green (#10b981)

### Loading States
```javascript
<div v-if="loading" class="loading">
  <spinner />
  <p>Loading metrics...</p>
</div>
```

### Error Handling
```javascript
try {
  await scaleStack(stackId, targetCount);
} catch (error) {
  showNotification(error.message, 'error');
}
```

---

## 📱 7. Mobile Responsive

All API responses are mobile-friendly. Recommended breakpoints:
- Desktop: > 1024px
- Tablet: 768px - 1024px
- Mobile: < 768px

---

## 🔒 8. Security Notes

- Add authentication headers when implemented
- Validate all user inputs before sending to API
- Use HTTPS in production
- Store API base URL in environment variable

```javascript
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8008';
```

---

## 📚 9. Complete Example: Full Dashboard

See `SCALING-SETUP-GUIDE.md` for backend setup, then build frontend with these APIs.

**Recommended Stack:**
- Vue 3 / React
- TailwindCSS for styling
- Chart.js / Recharts for graphs
- Axios for HTTP requests

---

## 🆘 10. Support

- Backend API Docs: http://localhost:8008/docs
- Issues: Contact backend team
- Slack: #infrastructure-platform


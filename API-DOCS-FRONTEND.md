# API Documentation - VPBank Hybrid Cloud Platform

## Base URL
```
http://localhost:8000
```

---

## 🚀 1. Infrastructure Deployment

### Deploy AWS Infrastructure
**POST** `/elb/deploy`

Triển khai VPC, EC2 instances, NLB với monitoring stack tự động.

**Request:**
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
  "auto_install_monitoring": true
}
```

**Response:**
```json
{
  "success": true,
  "stack": {
    "stack_id": "20251104213408-c3c57ad5",
    "nlb_dns": "my-app-nlb-xxx.elb.ap-southeast-2.amazonaws.com",
    "instance_ips": ["54.123.45.67", "54.123.45.68"],
    "monitoring_urls": {
      "grafana": "http://my-app-nlb-xxx.elb.ap-southeast-2.amazonaws.com",
      "mimir": "http://my-app-nlb-xxx.elb.ap-southeast-2.amazonaws.com:9009",
      "loki": "http://my-app-nlb-xxx.elb.ap-southeast-2.amazonaws.com:3100"
    }
  }
}
```

---

## 📊 2. Scaling Management

### List Active Stacks
**GET** `/scaling/stacks`

Lấy danh sách tất cả infrastructure stacks đang hoạt động.

**Response:**
```json
{
  "success": true,
  "total_stacks": 2,
  "stacks": [
    {
      "stack_id": "20251104213408-c3c57ad5",
      "current_instance_count": 3,
      "instances": ["54.123.45.67", "54.123.45.68", "54.123.45.69"],
      "nlb_dns": "my-app-nlb-xxx.elb.ap-southeast-2.amazonaws.com",
      "deployed_at": "2025-11-04 21:34:08",
      "region": "ap-southeast-2"
    }
  ]
}
```

### Get Stack Information
**GET** `/scaling/stack/{stack_id}/info`

Lấy thông tin chi tiết của một stack.

### Scale Stack
**POST** `/scaling/stack/scale`

Thay đổi số lượng EC2 instances trong stack.

**Request:**
```json
{
  "stack_id": "20251104213408-c3c57ad5",
  "target_count": 5,
  "reason": "Tăng traffic trong giờ cao điểm"
}
```

**Response:**
```json
{
  "success": true,
  "stack_id": "20251104213408-c3c57ad5",
  "old_count": 3,
  "new_count": 5,
  "action": "scale_up",
  "message": "Successfully scaled from 3 to 5 instances"
}
```

### Get Stack Metrics
**GET** `/scaling/stack/{stack_id}/metrics`

Lấy metrics CPU, Memory từ Grafana/Mimir.

**Response:**
```json
{
  "success": true,
  "stack_id": "20251104213408-c3c57ad5",
  "metrics": {
    "avg_cpu_usage": 65.2,
    "avg_memory_usage": 78.5,
    "timestamp": "2025-11-07 10:30:00"
  }
}
```

### AI Auto-Scale Recommendation
**POST** `/scaling/stack/{stack_id}/recommend`

Nhận gợi ý scaling từ AI dựa trên metrics hiện tại.

**Response:**
```json
{
  "success": true,
  "stack_id": "20251104213408-c3c57ad5",
  "current_count": 3,
  "recommended_count": 5,
  "confidence": 0.85,
  "reasoning": "CPU usage cao (65%) và memory usage (78%) cho thấy cần scale up",
  "action": "scale_up"
}
```

---

## 💻 3. EC2 Instance Control

### List Stack Instances
**GET** `/ec2/stack/{stack_id}/instances`

Lấy danh sách chi tiết tất cả EC2 instances trong stack.

**Response:**
```json
{
  "success": true,
  "stack_id": "20251104213408-c3c57ad5",
  "total_instances": 3,
  "instances": [
    {
      "instance_id": "i-0123456789abcdef0",
      "public_ip": "54.123.45.67",
      "public_dns": "ec2-54-123-45-67.ap-southeast-2.compute.amazonaws.com",
      "status": "running",
      "index": 0,
      "name": "my-app-1"
    }
  ]
}
```

### Start/Stop/Reboot Individual Instance
**POST** `/ec2/instance/start`
**POST** `/ec2/instance/stop`  
**POST** `/ec2/instance/reboot`

**Request:**
```json
{
  "instance_id": "i-0123456789abcdef0",
  "region": "ap-southeast-2"
}
```

### Batch Operations on Stack
**POST** `/ec2/stack/{stack_id}/start`
**POST** `/ec2/stack/{stack_id}/stop`
**POST** `/ec2/stack/{stack_id}/reboot`

Thực hiện action trên tất cả instances trong stack.

**Response:**
```json
{
  "success": true,
  "stack_id": "20251104213408-c3c57ad5",
  "action": "start",
  "total_instances": 3,
  "successful_operations": 3,
  "failed_operations": 0,
  "message": "Batch start: 3/3 instances processed successfully"
}
```

---

## 📈 4. Monitoring Integration

### Grafana Dashboard URLs
Sau khi deploy thành công, truy cập monitoring qua NLB:

- **Grafana UI**: `http://{nlb_dns}/` (admin/admin)
- **Mimir API**: `http://{nlb_dns}:9009/prometheus/api/v1/query`
- **Loki API**: `http://{nlb_dns}:3100/loki/api/v1/query`

### Custom Metrics Query
**POST** `/scaling/stack/metrics/query`

Thực hiện PromQL query tùy chỉnh.

**Request:**
```json
{
  "stack_id": "20251104213408-c3c57ad5",
  "promql_query": "rate(cpu_usage_total[5m])"
}
```

---

## 🔧 Frontend Integration Examples

### React Component Example
```jsx
// Lấy danh sách stacks
const fetchStacks = async () => {
  const response = await fetch('http://localhost:8000/scaling/stacks');
  const data = await response.json();
  return data.stacks;
};

// Scale stack
const scaleStack = async (stackId, targetCount) => {
  const response = await fetch('http://localhost:8000/scaling/stack/scale', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      stack_id: stackId,
      target_count: targetCount,
      reason: 'Manual scaling from dashboard'
    })
  });
  return response.json();
};

// Lấy metrics
const getMetrics = async (stackId) => {
  const response = await fetch(`http://localhost:8000/scaling/stack/${stackId}/metrics`);
  return response.json();
};
```

### Vue.js Example
```javascript
// methods
async getStackInfo(stackId) {
  try {
    const response = await this.$http.get(`/scaling/stack/${stackId}/info`);
    this.stackInfo = response.data;
  } catch (error) {
    console.error('Error fetching stack info:', error);
  }
},

async controlInstance(instanceId, action) {
  try {
    const response = await this.$http.post(`/ec2/instance/${action}`, {
      instance_id: instanceId,
      region: 'ap-southeast-2'
    });
    this.$message.success(`Instance ${action} successful`);
    return response.data;
  } catch (error) {
    this.$message.error(`Failed to ${action} instance`);
  }
}
```

---

## ⚠️ Error Handling

Tất cả API endpoints trả về format lỗi chuẩn:

```json
{
  "success": false,
  "error": "Stack not found",
  "detail": "Stack 20251104213408-invalid not found in workspace"
}
```

**Common HTTP Status Codes:**
- `200`: Success
- `400`: Bad Request (invalid parameters)
- `404`: Resource Not Found
- `500`: Internal Server Error

---

## 🔄 Real-time Updates

Để theo dõi trạng thái real-time, frontend có thể:

1. **Polling**: Gọi API `/scaling/stack/{stack_id}/info` mỗi 30s
2. **Metrics Refresh**: Gọi `/scaling/stack/{stack_id}/metrics` mỗi 60s  
3. **Status Check**: Gọi `/ec2/stack/{stack_id}/instances` khi cần cập nhật trạng thái instances

---

*Cập nhật lần cuối: November 2025*

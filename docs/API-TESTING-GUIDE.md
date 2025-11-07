# API Testing Guide - VPBank Hybrid Cloud Platform

## 📋 Mục Lục
1. [Project Management](#project-management)
2. [Scaling Operations](#scaling-operations)
3. [Metrics & Monitoring](#metrics--monitoring)
4. [AI Auto-Scaling](#ai-auto-scaling)
5. [EC2 Instance Control](#ec2-instance-control)
6. [Terminal/SSH Access](#terminalssh-access)
7. [Quick Test Flow](#quick-test-flow)

---

## 🔧 Chuẩn Bị

### Stack ID
```
20251107161813-bb01cd55
```

### Base URL
```
http://localhost:8000
```

### Tools Required
```bash
# Install jq for pretty JSON output
sudo apt-get install -y jq

# Or use python for JSON parsing
python -m json.tool
```

---

## 📁 Project Management

### **1. Get Project Info**
Lấy thông tin chi tiết của project

```bash
curl http://localhost:8000/elb/projects/20251107161813-bb01cd55 | jq .
```

**Response Example:**
```json
{
  "success": true,
  "project": {
    "stack_id": "20251107161813-bb01cd55",
    "current_instance_count": 2,
    "instances": ["54.123.45.67", "54.123.45.68"],
    "nlb_dns": "test-final-nlb-xxx.elb.ap-southeast-2.amazonaws.com",
    "deployed_at": "2025-11-07 16:18:13",
    "region": "ap-southeast-2"
  }
}
```

### **2. List All Projects**
Lấy danh sách tất cả projects đang active

```bash
curl http://localhost:8000/elb/projects | jq .
```

**Response Example:**
```json
{
  "success": true,
  "total_projects": 1,
  "projects": [
    {
      "stack_id": "20251107161813-bb01cd55",
      "current_instance_count": 2,
      "instances": ["54.123.45.67", "54.123.45.68"],
      "nlb_dns": "test-final-nlb-xxx.elb.ap-southeast-2.amazonaws.com",
      "deployed_at": "2025-11-07 16:18:13",
      "region": "ap-southeast-2"
    }
  ]
}
```

---

## 📈 Scaling Operations

### **3. Get Stack Info**
Lấy thông tin chi tiết của stack (instances, metadata, etc)

```bash
curl http://localhost:8000/scaling/stack/20251107161813-bb01cd55/info | jq .
```

**Response Example:**
```json
{
  "success": true,
  "stack_id": "20251107161813-bb01cd55",
  "current_instance_count": 2,
  "instances": ["54.123.45.67", "54.123.45.68"],
  "nlb_dns": "test-final-nlb-xxx.elb.ap-southeast-2.amazonaws.com",
  "deployed_at": "2025-11-07 16:18:13",
  "region": "ap-southeast-2"
}
```

### **4. List All Active Stacks**
Lấy danh sách tất cả stacks đang hoạt động

```bash
curl http://localhost:8000/scaling/stacks | jq .
```

### **5. Scale Stack Up**
Tăng số lượng instances từ 2 lên 5

```bash
curl -X POST http://localhost:8000/scaling/stack/scale \
  -H "Content-Type: application/json" \
  -d '{
    "stack_id": "20251107161813-bb01cd55",
    "target_count": 5,
    "reason": "Testing scale up - high traffic expected"
  }' | jq .
```

**Response Example:**
```json
{
  "success": true,
  "stack_id": "20251107161813-bb01cd55",
  "old_count": 2,
  "new_count": 5,
  "action": "scale_up",
  "keypairs_added": ["test-final-vm-3", "test-final-vm-4", "test-final-vm-5"],
  "keypairs_deleted": [],
  "message": "Successfully scaled from 2 to 5 instances"
}
```

### **6. Scale Stack Down**
Giảm số lượng instances từ 5 xuống 2

```bash
curl -X POST http://localhost:8000/scaling/stack/scale \
  -H "Content-Type: application/json" \
  -d '{
    "stack_id": "20251107161813-bb01cd55",
    "target_count": 2,
    "reason": "Testing scale down - cost optimization"
  }' | jq .
```

**Response Example:**
```json
{
  "success": true,
  "stack_id": "20251107161813-bb01cd55",
  "old_count": 5,
  "new_count": 2,
  "action": "scale_down",
  "keypairs_added": [],
  "keypairs_deleted": ["test-final-vm-3", "test-final-vm-4", "test-final-vm-5"],
  "message": "Successfully scaled from 5 to 2 instances"
}
```

---

## 📊 Metrics & Monitoring

### **7. Get Stack Metrics**
Lấy metrics CPU và Memory hiện tại từ Mimir

```bash
curl http://localhost:8000/scaling/stack/20251107161813-bb01cd55/metrics | jq .
```

**Response Example:**
```json
{
  "success": true,
  "stack_id": "20251107161813-bb01cd55",
  "metrics": {
    "avg_cpu_usage": 35.2,
    "avg_memory_usage": 62.8,
    "timestamp": "2025-11-07 16:30:00"
  }
}
```

### **8. Custom PromQL Query**
Thực hiện custom query trên Mimir (Prometheus API)

```bash
curl -X POST http://localhost:8000/scaling/stack/metrics/query \
  -H "Content-Type: application/json" \
  -d '{
    "stack_id": "20251107161813-bb01cd55",
    "promql_query": "rate(cpu_usage_total[5m])"
  }' | jq .
```

**Response Example:**
```json
{
  "success": true,
  "stack_id": "20251107161813-bb01cd55",
  "query": "rate(cpu_usage_total[5m])",
  "result": {
    "status": "success",
    "data": {
      "resultType": "vector",
      "result": [...]
    }
  }
}
```

---

## 🤖 AI Auto-Scaling

### **9. Get AI Recommendation**
Nhận khuyến nghị scaling từ Gemini AI dựa trên metrics hiện tại

```bash
curl -X POST http://localhost:8000/scaling/stack/20251107161813-bb01cd55/recommend \
  -H "Content-Type: application/json" | jq .
```

**Response Example:**
```json
{
  "success": true,
  "stack_id": "20251107161813-bb01cd55",
  "current_count": 2,
  "recommended_count": 4,
  "confidence": 0.82,
  "reasoning": "CPU usage is 72% and memory usage is 81%. Recommend scaling up to 4 instances to handle the load.",
  "action": "scale_up"
}
```

### **10. Execute AI Recommendation**
Thực hiện scaling dựa trên AI recommendation

```bash
curl -X POST http://localhost:8000/scaling/stack/20251107161813-bb01cd55/auto-scale \
  -H "Content-Type: application/json" | jq .
```

**Response Example:**
```json
{
  "success": true,
  "stack_id": "20251107161813-bb01cd55",
  "old_count": 2,
  "new_count": 4,
  "action": "scale_up",
  "recommendation_confidence": 0.82,
  "message": "Auto-scaled from 2 to 4 instances based on AI recommendation"
}
```

---

## 💻 EC2 Instance Control

### **11. List Instances**
Lấy danh sách tất cả instances trong stack

```bash
curl http://localhost:8000/ec2/stack/20251107161813-bb01cd55/instances | jq .
```

**Response Example:**
```json
{
  "success": true,
  "stack_id": "20251107161813-bb01cd55",
  "total_instances": 2,
  "instances": [
    {
      "instance_id": "i-0123456789abcdef0",
      "public_ip": "54.123.45.67",
      "public_dns": "ec2-54-123-45-67.ap-southeast-2.compute.amazonaws.com",
      "status": "running",
      "index": 1,
      "name": "test-final-vm-1"
    },
    {
      "instance_id": "i-0123456789abcdef1",
      "public_ip": "54.123.45.68",
      "public_dns": "ec2-54-123-45-68.ap-southeast-2.compute.amazonaws.com",
      "status": "running",
      "index": 2,
      "name": "test-final-vm-2"
    }
  ]
}
```

### **12. Get Instance Status**
Lấy trạng thái của instance cụ thể

```bash
curl http://localhost:8000/ec2/instance/status \
  -H "Content-Type: application/json" \
  -d '{
    "stack_id": "20251107161813-bb01cd55",
    "instance_index": 1
  }' | jq .
```

**Response Example:**
```json
{
  "success": true,
  "instance_id": "i-0123456789abcdef0",
  "status": "running",
  "instance_name": "test-final-vm-1",
  "public_ip": "54.123.45.67"
}
```

### **13. Start Instance**
Khởi động instance

```bash
curl -X POST http://localhost:8000/ec2/instance/start \
  -H "Content-Type: application/json" \
  -d '{
    "stack_id": "20251107161813-bb01cd55",
    "instance_index": 1
  }' | jq .
```

**Response Example:**
```json
{
  "success": true,
  "instance_id": "i-0123456789abcdef0",
  "action": "start",
  "message": "Instance started successfully"
}
```

### **14. Stop Instance**
Dừng instance

```bash
curl -X POST http://localhost:8000/ec2/instance/stop \
  -H "Content-Type: application/json" \
  -d '{
    "stack_id": "20251107161813-bb01cd55",
    "instance_index": 1
  }' | jq .
```

**Response Example:**
```json
{
  "success": true,
  "instance_id": "i-0123456789abcdef0",
  "action": "stop",
  "message": "Instance stopped successfully"
}
```

### **15. Reboot Instance**
Khởi động lại instance

```bash
curl -X POST http://localhost:8000/ec2/instance/reboot \
  -H "Content-Type: application/json" \
  -d '{
    "stack_id": "20251107161813-bb01cd55",
    "instance_index": 1
  }' | jq .
```

**Response Example:**
```json
{
  "success": true,
  "instance_id": "i-0123456789abcdef0",
  "action": "reboot",
  "message": "Instance rebooted successfully"
}
```

### **16. Batch Operations - Start All Instances**
Khởi động tất cả instances trong stack

```bash
curl -X POST http://localhost:8000/ec2/stack/20251107161813-bb01cd55/start \
  -H "Content-Type: application/json" | jq .
```

### **17. Batch Operations - Stop All Instances**
Dừng tất cả instances trong stack

```bash
curl -X POST http://localhost:8000/ec2/stack/20251107161813-bb01cd55/stop \
  -H "Content-Type: application/json" | jq .
```

### **18. Batch Operations - Reboot All Instances**
Khởi động lại tất cả instances trong stack

```bash
curl -X POST http://localhost:8000/ec2/stack/20251107161813-bb01cd55/reboot \
  -H "Content-Type: application/json" | jq .
```

---

## 🖥️ Terminal/SSH Access

### **19. Connect Terminal Session**
Kết nối đến instance qua SSH terminal

```bash
curl -X POST http://localhost:8000/terminal/connect \
  -H "Content-Type: application/json" \
  -d '{
    "stack_id": "20251107161813-bb01cd55",
    "instance_index": 1,
    "username": "ubuntu"
  }' | jq .
```

**Response Example:**
```json
{
  "success": true,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "instance_ip": "54.123.45.67",
  "instance_name": "test-final-vm-1",
  "username": "ubuntu",
  "ssh_command": "ssh -i /path/to/test-final-vm-1.pem ubuntu@54.123.45.67"
}
```

### **20. List Active Terminal Sessions**
Lấy danh sách các terminal sessions đang hoạt động

```bash
curl http://localhost:8000/terminal/sessions | jq .
```

**Response Example:**
```json
{
  "success": true,
  "total_sessions": 1,
  "sessions": [
    {
      "session_id": "550e8400-e29b-41d4-a716-446655440000",
      "hostname": "54.123.45.67",
      "username": "ubuntu",
      "is_active": true
    }
  ]
}
```

### **21. Disconnect Terminal Session**
Đóng terminal session

```bash
curl -X POST http://localhost:8000/terminal/disconnect \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
  }' | jq .
```

**Response Example:**
```json
{
  "success": true,
  "message": "Session 550e8400-e29b-41d4-a716-446655440000 closed"
}
```

### **22. Cleanup Inactive Sessions**
Xóa tất cả inactive terminal sessions

```bash
curl -X POST http://localhost:8000/terminal/cleanup | jq .
```

**Response Example:**
```json
{
  "success": true,
  "cleaned_sessions": 3
}
```

### **23. WebSocket Terminal - Interactive Shell**
Kết nối WebSocket để interactive terminal (dùng xterm.js trên frontend)

```javascript
// JavaScript code for browser
const sessionId = "550e8400-e29b-41d4-a716-446655440000";
const ws = new WebSocket(`ws://localhost:8000/terminal/ws/${sessionId}`);

// Handle incoming messages
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  
  if (msg.type === "output") {
    // Write to terminal
    terminal.write(msg.data);
  } else if (msg.type === "error") {
    console.error("Error:", msg.message);
  } else if (msg.type === "closed") {
    console.log("Session closed:", msg.message);
  }
};

// Send command
function sendCommand(command) {
  ws.send(JSON.stringify({
    type: "command",
    data: command + "\n"
  }));
}

// Resize terminal
function resizeTerminal(width, height) {
  ws.send(JSON.stringify({
    type: "resize",
    width: width,
    height: height
  }));
}

// Disconnect
function disconnect() {
  ws.send(JSON.stringify({
    type: "disconnect"
  }));
}

// Example usage
sendCommand("ls -la");
sendCommand("cat /etc/grafana/provisioning/datasources/datasources.yml");
sendCommand("docker ps");
resizeTerminal(120, 30);
```

---

## 🧪 Quick Test Flow

### **Scenario: Complete Stack Testing**

```bash
#!/bin/bash

STACK_ID="20251107161813-bb01cd55"
BASE_URL="http://localhost:8000"

echo "=========================================="
echo "🧪 Complete Stack Testing Flow"
echo "=========================================="
echo ""

# 1. Check stack info
echo "1️⃣  Get stack info..."
curl $BASE_URL/elb/projects/$STACK_ID | jq .
echo ""
sleep 2

# 2. List instances
echo "2️⃣  List instances..."
curl $BASE_URL/ec2/stack/$STACK_ID/instances | jq .
echo ""
sleep 2

# 3. Get metrics
echo "3️⃣  Get metrics..."
curl $BASE_URL/scaling/stack/$STACK_ID/metrics | jq .
echo ""
sleep 2

# 4. Scale up
echo "4️⃣  Scale up (2 → 3)..."
curl -X POST $BASE_URL/scaling/stack/scale \
  -H "Content-Type: application/json" \
  -d "{\"stack_id\":\"$STACK_ID\",\"target_count\":3}" | jq .
echo ""
sleep 5

# 5. Check updated count
echo "5️⃣  Verify new instance count..."
curl $BASE_URL/scaling/stack/$STACK_ID/info | jq .
echo ""
sleep 2

# 6. Get AI recommendation
echo "6️⃣  Get AI recommendation..."
curl -X POST $BASE_URL/scaling/stack/$STACK_ID/recommend \
  -H "Content-Type: application/json" | jq .
echo ""
sleep 2

# 7. Connect terminal
echo "7️⃣  Connect terminal to instance 1..."
SESSION=$(curl -X POST $BASE_URL/terminal/connect \
  -H "Content-Type: application/json" \
  -d "{\"stack_id\":\"$STACK_ID\",\"instance_index\":1}" | jq -r '.session_id')
echo "Session ID: $SESSION"
echo ""
sleep 2

# 8. Scale down
echo "8️⃣  Scale down (3 → 2)..."
curl -X POST $BASE_URL/scaling/stack/scale \
  -H "Content-Type: application/json" \
  -d "{\"stack_id\":\"$STACK_ID\",\"target_count\":2}" | jq .
echo ""

echo "=========================================="
echo "✅ Testing completed!"
echo "=========================================="
```

### **Save and Run:**
```bash
cat > test_apis.sh << 'EOF'
# (paste script content above)
EOF

chmod +x test_apis.sh
./test_apis.sh
```

---

## 📱 Performance Testing

### **Load Test - Multiple Concurrent Requests**
```bash
# Test with 10 concurrent requests
for i in {1..10}; do
  curl http://localhost:8000/scaling/stack/20251107161813-bb01cd55/metrics &
done
wait

echo "All requests completed"
```

### **Monitor API Response Time**
```bash
# Using curl with time output
curl -w "\nTime taken: %{time_total}s\n" \
  http://localhost:8000/scaling/stack/20251107161813-bb01cd55/info
```

---

## 🔍 Troubleshooting

### **Connection Refused**
```bash
# Check if backend is running
curl http://localhost:8000/docs
```

### **Invalid Stack ID**
```bash
# List available stacks
curl http://localhost:8000/elb/projects | jq .
```

### **Permission Denied (EC2)**
```bash
# Check AWS credentials
aws sts get-caller-identity
```

### **Terminal Session Not Found**
```bash
# List active sessions
curl http://localhost:8000/terminal/sessions | jq .
```

---

## 📚 Related Documentation

- **API Reference**: See `API-DOCS-FRONTEND.md`
- **Setup Guide**: See `SETUP-GUIDE.md`
- **Project Overview**: See `README.md`
- **Keypair Implementation**: See `KEYPAIR_IMPLEMENTATION.md`

---

*Last Updated: November 7, 2025*
*API Testing Guide v1.0*

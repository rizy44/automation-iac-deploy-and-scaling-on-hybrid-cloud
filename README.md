# 🚀 VPBank Hybrid Cloud Platform

> Nền tảng Infrastructure as Code (IaC) tự động hóa triển khai, quản lý và tối ưu hóa hạ tầng hybrid cloud với AI-powered scaling

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Terraform](https://img.shields.io/badge/terraform-1.6+-purple.svg)](https://www.terraform.io/)
[![AWS](https://img.shields.io/badge/AWS-Ready-orange.svg)](https://aws.amazon.com/)

---

## 📖 Mục Lục

- [Giới Thiệu](#-giới-thiệu)
- [Tính Năng](#-tính-năng)
- [Kiến Trúc](#-kiến-trúc)
- [Bắt Đầu Nhanh](#-bắt-đầu-nhanh)
- [Deployment Options](#-deployment-options)
- [API Documentation](#-api-documentation)
- [Monitoring & Analytics](#-monitoring--analytics)
- [Use Cases](#-use-cases)
- [Configuration](#-configuration)
- [Security](#-security)
- [Chi Phí](#-chi-phí)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🌟 Giới Thiệu

**VPBank Hybrid Cloud Platform** là giải pháp Infrastructure as Code (IaC) toàn diện, cho phép doanh nghiệp triển khai và quản lý hạ tầng hybrid cloud một cách tự động, hiệu quả và thông minh. Platform được xây dựng với triết lý "Simplify Complexity" - đơn giản hóa những phức tạp trong quản lý hạ tầng đám mây.

### 🎯 Tại Sao Chọn VPBank Cloud Platform?

<table>
<tr>
<td width="50%" valign="top">

**🚀 Triển khai cực nhanh**

- Infrastructure hoàn chỉnh chỉ trong 5-10 phút
- One-click deployment với Terraform
- Tự động cài đặt monitoring stack

**🤖 AI-Powered Intelligence**

- Google Gemini AI phân tích metrics
- Auto-scaling dựa trên ML predictions
- Intelligent cost optimization

**📊 Observability Toàn Diện**

- Grafana dashboards tích hợp sẵn
- Real-time metrics với Mimir (Prometheus)
- Centralized logging với Loki

</td>
<td width="50%" valign="top">

**💰 Tối Ưu Chi Phí**

- Auto scale down khi traffic thấp
- Right-sizing recommendations
- Cost tracking và reporting

**🔒 Security by Design**

- Network segmentation tự động
- Encrypted VPN tunnels (AES-256)
- Per-instance SSH keypairs
- Security groups theo best practices

**🔧 Developer Friendly**

- RESTful API với OpenAPI/Swagger
- WebSocket SSH terminals
- Python SDK ready

</td>
</tr>
</table>

---

## ✨ Tính Năng

### 🏗️ Infrastructure Deployment

#### **Option 1: SD-WAN Hybrid Cloud** (Enterprise-grade)

Kiến trúc hybrid cloud hoàn chỉnh kết nối OpenStack datacenter với AWS cloud:

```
┌─────────────────────┐         ┌─────────────────────┐
│  OpenStack DC       │◄───────►│    AWS Cloud        │
│  172.10.0.0/16      │  IPsec  │    Transit Gateway  │
│                     │  VPN    │    + Multi-VPC      │
│  • SD-WAN Edge      │  (2x)   │    + Auto Scaling   │
│  • StrongSwan       │         │    + Load Balancer  │
│  • BGP Routing      │         │    + Monitoring     │
└─────────────────────┘         └─────────────────────┘
```

**Components:**

- ✅ AWS Transit Gateway (central hub routing)
- ✅ Site-to-Site VPN với 2 tunnels (high availability)
- ✅ App VPC với Application Load Balancer
- ✅ Auto Scaling Group (2-20 instances)
- ✅ Shared Services VPC (monitoring, logging, DNS)
- ✅ OpenStack SD-WAN Edge với StrongSwan IPsec

**Cost:** ~$175/month | **Deploy time:** 10-15 minutes

#### **Option 2: Simple ELB Deployment** (Quick & Easy)

Single VPC deployment với Network Load Balancer:

```
┌───────────────────────────────────┐
│              AWS VPC              │
│                                   │
│    ┌────────────────────────┐     │
│    │  Network Load Balancer │     │
│    └────────────┬───────────┘     │
│                 │                 │
│         ┌───────┴───────┐         │
│         ▼               ▼         │
│    ┌────────┐      ┌────────┐     │
│    │ EC2 #1 │      │ EC2 #2 │     │
│    │ + Graf │      │ + Graf │     │
│    └────────┘      └────────┘     │
│                                   │
└───────────────────────────────────┘
```

**Components:**

- ✅ Single VPC với public/private subnets
- ✅ EC2 instances (1-50) với auto-monitoring
- ✅ Network Load Balancer
- ✅ Per-instance SSH keypairs tự động
- ✅ Grafana + Mimir + Loki pre-installed

**Cost:** ~$30/month | **Deploy time:** 5-8 minutes

### 📈 AI-Powered Auto-Scaling

<table>
<tr>
<td width="60%">

**Intelligent Scaling Engine**

1. **Real-time Metrics Collection**

   - CPU, Memory, Network usage từ Mimir
   - Application-level metrics
   - Custom PromQL queries

2. **AI Analysis với Google Gemini**

   - Pattern recognition trong metrics
   - Predictive scaling recommendations
   - Confidence scoring (0-1)

3. **Automatic Execution**

   - Auto-scale khi confidence > threshold (default 0.7)
   - Scale up: Tăng instances khi high load
   - Scale down: Giảm instances để tiết kiệm chi phí
   - Scheduled checks mỗi 5 phút (configurable)

4. **Manual Override**
   - Scale thủ công bất cứ lúc nào
   - Set custom instance count
   - API-driven scaling

</td>
<td width="40%">

**Example Response:**

```json
{
  "current_count": 2,
  "recommended_count": 4,
  "confidence": 0.85,
  "action": "scale_up",
  "reasoning": "CPU 78%,
    Memory 82%.
    Recommend scaling
    to handle load."
}
```

**Scaling Limits:**

- Min: 1 instance
- Max: 20 instances
- Configurable via `.env`

</td>
</tr>
</table>

### 🖥️ EC2 Instance Management

**Full Lifecycle Control:**

| Operation  | Single Instance                | Batch (All Instances)              |
| ---------- | ------------------------------ | ---------------------------------- |
| **Start**  | ✅ `POST /ec2/instance/start`  | ✅ `POST /ec2/stack/{id}/start`    |
| **Stop**   | ✅ `POST /ec2/instance/stop`   | ✅ `POST /ec2/stack/{id}/stop`     |
| **Reboot** | ✅ `POST /ec2/instance/reboot` | ✅ `POST /ec2/stack/{id}/reboot`   |
| **Status** | ✅ `GET /ec2/instance/status`  | ✅ `GET /ec2/stack/{id}/instances` |

**Features:**

- Real-time status monitoring (running, stopped, stopping, etc.)
- Instance-level và stack-level operations
- Detailed response với instance ID, IP, DNS
- Error handling và retry logic

### 🖥️ SSH Terminal Access

**WebSocket-based Interactive Terminal:**

```javascript
// Connect via WebSocket
const ws = new WebSocket(`ws://api/terminal/ws/${sessionId}`);

// Send commands
ws.send(
  JSON.stringify({
    type: "command",
    data: "ls -la\n",
  })
);

// Receive output
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  if (msg.type === "output") {
    terminal.write(msg.data);
  }
};
```

**Features:**

- Browser-based SSH access (xterm.js compatible)
- No SSH client installation needed
- Session management (list, connect, disconnect)
- Resize terminal support
- Secure connection với auto-generated keypairs

### 📊 Monitoring & Analytics

**Full Observability Stack:**

<table>
<tr>
<td width="33%" valign="top">

**📈 Grafana**

- Pre-configured dashboards
- System overview
- Per-instance metrics
- Auto-scaling events
- Custom visualizations

Access: `http://<NLB_DNS>:3000`
Credentials: `admin/admin`

</td>
<td width="33%" valign="top">

**📊 Mimir (Prometheus)**

- Time-series metrics storage
- 5-minute retention (configurable)
- PromQL query support
- Multi-tenant ready
- High-availability mode

Endpoint: `http://<NLB_DNS>/mimir`

</td>
<td width="33%" valign="top">

**📝 Loki**

- Centralized log aggregation
- Log streaming
- Label-based indexing
- Integration với Grafana
- Efficient storage

Endpoint: `http://<NLB_DNS>/loki`

</td>
</tr>
</table>

**Pre-configured Metrics:**

- CPU usage (per core, average)
- Memory usage (used, available, percent)
- Network I/O (bytes in/out, packets)
- Disk I/O (read/write ops, latency)
- Instance count và scaling events

**Custom PromQL Queries:**

```promql
# Average CPU across all instances
avg(rate(node_cpu_seconds_total{mode!="idle"}[5m])) * 100

# Memory usage percentage
(1 - avg(node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100

# Network traffic rate
rate(node_network_transmit_bytes_total[5m])
```

---

## 🏛️ Kiến Trúc

### SD-WAN Hybrid Cloud Architecture

```
┌───────────────────────────────────┐
│       OpenStack Datacenter        │
│          172.10.0.0/16            │
│                                   │
│  ┌─────────────────────────────┐  │
│  │  SD-WAN Edge (StrongSwan)   │  │
│  │  Public IP: 203.0.113.50    │  │
│  └─────────────┬───────────────┘  │
└────────────────┼──────────────────┘
                 │
       IPsec VPN Tunnels (2x)
                 │
┌────────────────┼──────────────────┐
│                ▼                  │
│  ┌─────────────────────────────┐  │
│  │   AWS Transit Gateway       │  │
│  │   ASN: 64512                │  │
│  └─────┬──────────────┬────────┘  │
│        │              │           │
│  ┌─────▼─────┐   ┌────▼───────┐   │
│  │  App VPC  │   │Shared VPC  │   │
│  │10.101.../16   │10.103.../16│   │
│  │           │   │            │   │
│  │ ┌───────┐ │   │ Monitoring │   │
│  │ │  ALB  │ │   │  Logging   │   │
│  │ └───┬───┘ │   │            │   │
│  │     │     │   └────────────┘   │
│  │ ┌───▼───┐ │                    │
│  │ │  ASG  │ │                    │
│  │ │ 2-4   │ │                    │
│  │ │ EC2   │ │                    │
│  │ └───────┘ │                    │
│  └───────────┘                    │
│            AWS Cloud              │
└───────────────────────────────────┘
```

### Simple ELB Architecture

```
┌──────────────────────────────┐
│           AWS VPC            │
│                              │
│  ┌──────────────────────┐    │
│  │  Network Load        │    │
│  │  Balancer            │    │
│  └──────────┬───────────┘    │
│             │                │
│  ┌──────────▼─────────────┐  │
│  │   EC2 Instances        │  │
│  │   (2-50 instances)     │  │
│  │   + Grafana/Mimir/Loki │  │
│  └────────────────────────┘  │
│                              │
└──────────────────────────────┘
```

---

## 🚀 Bắt Đầu Nhanh

### Yêu Cầu Hệ Thống

- **OS**: Ubuntu 20.04+, CentOS 8+, Amazon Linux 2
- **Python**: 3.8+
- **Terraform**: 1.6.0+
- **AWS CLI**: v2
- **RAM**: 4GB+
- **Disk**: 20GB+

### Cài Đặt Chi Tiết

**Xem hướng dẫn đầy đủ**: [📚 SETUP-GUIDE.md](docs/SETUP-GUIDE.md)

### Quick Install

```bash
# 1. Clone repository
git clone https://github.com/rizy44/automation-iac-deploy-and-scaling-on-hybrid-cloud.git
cd automation-iac-deploy-and-scaling-on-hybrid-cloud

# 2. Cài đặt dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

# 3. Cấu hình AWS
aws configure
# Nhập: Access Key, Secret Key, Region (ap-southeast-2)

# 4. Cấu hình môi trường
cp .env.example .env
nano .env  # Điền GEMINI_API_KEY

# 5. Khởi chạy server
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
```

Server chạy tại: **http://localhost:8000**

### Deploy Infrastructure Đầu Tiên

#### Option 1: SD-WAN Hybrid Cloud

```bash
curl -X POST http://localhost:8000/sdwan/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "name_prefix": "prod-sdwan",
    "region": "ap-southeast-2",
    "azs": ["ap-southeast-2a", "ap-southeast-2b"],
    "openstack_cidr": "172.10.0.0/16",
    "openstack_public_ip": "203.0.113.50",
    "app_ami": "ami-0a25a306450a2cba3"
  }'
```

**Next steps**: [📘 QUICKSTART-SDWAN.md](docs/QUICKSTART-SDWAN.md)

#### Option 2: Simple ELB Deployment

```bash
curl -X POST http://localhost:8000/elb/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "name_prefix": "test-app",
    "instance_count": 2,
    "instance_type": "t3.micro",
    "auto_install_monitoring": true
  }'
```

Monitoring tự động được cài đặt tại: `http://<NLB_DNS>:3000`

---

## 📚 API Documentation

### Interactive Docs

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Quick API Reference

#### 🏗️ Deployment APIs

| Endpoint                    | Method | Description                      |
| --------------------------- | ------ | -------------------------------- |
| `/sdwan/deploy`             | POST   | Deploy SD-WAN hybrid cloud       |
| `/elb/deploy`               | POST   | Deploy simple ELB infrastructure |
| `/sdwan/destroy/{stack_id}` | DELETE | Destroy SD-WAN infrastructure    |

#### 📈 Scaling APIs

| Endpoint                               | Method | Description               |
| -------------------------------------- | ------ | ------------------------- |
| `/scaling/stack/{stack_id}/info`       | GET    | Lấy thông tin stack       |
| `/scaling/stack/scale`                 | POST   | Scale stack manually      |
| `/scaling/stack/{stack_id}/recommend`  | POST   | Lấy AI recommendation     |
| `/scaling/stack/{stack_id}/auto-scale` | POST   | Thực hiện AI auto-scaling |

#### 🖥️ EC2 Management APIs

| Endpoint                          | Method | Description           |
| --------------------------------- | ------ | --------------------- |
| `/ec2/stack/{stack_id}/instances` | GET    | List tất cả instances |
| `/ec2/instance/start`             | POST   | Start instance        |
| `/ec2/instance/stop`              | POST   | Stop instance         |
| `/ec2/instance/reboot`            | POST   | Reboot instance       |
| `/ec2/stack/{stack_id}/start`     | POST   | Start all instances   |

#### 🖥️ Terminal/SSH APIs

| Endpoint                    | Method    | Description          |
| --------------------------- | --------- | -------------------- |
| `/terminal/connect`         | POST      | Tạo SSH session      |
| `/terminal/ws/{session_id}` | WebSocket | Interactive terminal |
| `/terminal/sessions`        | GET       | List active sessions |

**Chi tiết đầy đủ**: [🔌 API-REFERENCE.md](docs/API-REFERENCE.md)

**Testing guide**: [🧪 API-TESTING-GUIDE.md](docs/API-TESTING-GUIDE.md)

---

## 🎯 Use Cases

### E-commerce Platform

**Kịch bản**: Flash sale với traffic tăng đột biến

```bash
# 1. Deploy infrastructure
curl -X POST http://localhost:8000/elb/deploy \
  -d '{"name_prefix":"ecommerce","instance_count":2,"instance_type":"t3.medium"}'

# 2. Enable AI auto-scaling (tự động scale khi traffic cao)
# AI sẽ monitor và scale từ 2 lên 10 instances khi cần

# 3. Sau flash sale, AI tự động scale down về 2 instances
```

**Tiết kiệm**: ~70% chi phí so với giữ 10 instances 24/7

### Fintech Application

**Kịch bản**: Đảm bảo uptime 99.9% với hybrid cloud

```bash
# Deploy SD-WAN hybrid cloud
curl -X POST http://localhost:8000/sdwan/deploy \
  -d '{"name_prefix":"fintech","app_min_size":4,"app_max_size":10}'

# Kết quả:
# - Core banking trên OpenStack (on-premise)
# - API Gateway trên AWS (scalable)
# - Kết nối secure qua VPN
```

### Media Streaming

**Kịch bản**: Xử lý traffic không đều trong ngày

```bash
# Morning: 2 instances
# Peak (8PM): AI auto-scale lên 8 instances
# Night: Scale down về 2 instances
```

---

## ⚙️ Cấu Hình

### Environment Variables (.env)

```bash
# AWS Configuration
AWS_DEFAULT_REGION=ap-southeast-2
TF_WORK_ROOT=/tmp/terraform-workspaces

# AI Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Auto-scaling Configuration
AUTO_SCALING_ENABLED=true
AUTO_SCALING_INTERVAL_MINUTES=5
AUTO_SCALING_CONFIDENCE_THRESHOLD=0.7
SCALE_UP_MAX_INSTANCES=20
SCALE_DOWN_MIN_INSTANCES=1

# Monitoring
MIMIR_URL=http://mimir:9009
GRAFANA_URL=http://grafana:3000

# Logging
LOG_LEVEL=INFO
```

### Lấy Gemini API Key

1. Truy cập: https://makersuite.google.com/app/apikey
2. Tạo API key mới
3. Copy và paste vào `.env`

---

## 📊 Monitoring

### Access Grafana

```bash
# Lấy NLB DNS từ deployment response
curl http://<NLB_DNS>:3000

# Default credentials:
# Username: admin
# Password: admin
```

### Pre-configured Dashboards

1. **System Overview**: CPU, Memory, Network overview
2. **EC2 Instances**: Per-instance metrics
3. **Auto-Scaling**: Scaling events và AI recommendations
4. **Application**: Custom application metrics

### PromQL Examples

```promql
# Average CPU usage across all instances
avg(cpu_usage_percent{stack_id="your-stack-id"})

# Memory usage per instance
memory_usage_bytes{instance=~".*"}

# Network traffic
rate(network_bytes_total[5m])
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Deployment Failed

```bash
# Check logs
tail -f .infra/work/{stack_id}/terraform.log

# Common causes:
# - AWS credentials không đúng
# - Region không support instance type
# - AMI không tồn tại trong region
```

#### 2. AI Auto-scaling Không Hoạt Động

```bash
# Check scheduler logs
python -m uvicorn backend.app:app --log-level debug

# Verify Gemini API key
curl -H "Authorization: Bearer $GEMINI_API_KEY" https://generativelanguage.googleapis.com/v1/models
```

#### 3. Monitoring Không Hiển Thị Metrics

```bash
# SSH vào instance và check Grafana Agent
sudo systemctl status grafana-agent

# Check Mimir endpoint
curl http://<MIMIR_URL>:9009/api/v1/query?query=up
```

#### 4. VPN Tunnels Không Kết Nối (SD-WAN)

```bash
# SSH vào OpenStack Edge
ssh ubuntu@203.0.113.50

# Check StrongSwan status
sudo ipsec statusall

# View logs
sudo journalctl -u strongswan -f
```

**Chi tiết**: [🔧 OpenStack Edge Setup](docs/openstack-edge-setup.md)

---

## 💰 Chi Phí Ước Tính

### SD-WAN Hybrid Cloud (~$175/tháng)

| Service              | Monthly Cost |
| -------------------- | ------------ |
| Transit Gateway      | $36          |
| TGW Attachments (2x) | $72          |
| Site-to-Site VPN     | $36          |
| EC2 (t3.micro x2)    | $15          |
| NAT Gateway          | $33          |
| ALB                  | $16          |
| Data Transfer        | ~$10         |

### Simple ELB (~$30/tháng)

| Service           | Monthly Cost |
| ----------------- | ------------ |
| EC2 (t3.micro x2) | $15          |
| NLB               | $16          |
| Data Transfer     | ~$5          |

**Mẹo tiết kiệm**:

- Stop instances khi không dùng
- Dùng Spot Instances cho non-critical workloads
- Enable AI auto-scaling để tối ưu resources

---

## 🤝 Đóng Góp

Chúng tôi luôn chào đón đóng góp từ cộng đồng!

### Cách Thức Đóng Góp

1. Fork repository
2. Tạo feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Mở Pull Request

### Báo Lỗi

- Mở Issue với mô tả chi tiết
- Cung cấp logs và steps to reproduce
- Tag với label phù hợp

---

## 📦 Tech Stack

| Category       | Technology                                |
| -------------- | ----------------------------------------- |
| **Backend**    | Python 3.8+, FastAPI                      |
| **IaC**        | Terraform 1.6+                            |
| **Cloud**      | AWS (EC2, VPC, NLB, ALB, Transit Gateway) |
| **AI**         | Google Gemini API                         |
| **Monitoring** | Grafana, Mimir (Prometheus), Loki         |
| **Deployment** | Docker-ready                              |
| **VPN**        | StrongSwan (OpenStack Edge)               |

---

## 🔒 Security Best Practices

✅ **Implemented**:

- AWS credentials trong `.env` (không commit)
- Terraform state được quản lý cẩn thận
- Security groups tự động cấu hình
- SSH keys tự động tạo và quản lý
- IPsec encryption cho VPN (AES-256)

⚠️ **Production Recommendations**:

- Sử dụng AWS IAM roles thay vì access keys
- Remote backend cho Terraform state (S3 + DynamoDB)
- SSL/TLS cho API endpoints
- Network segmentation và VPN
- Rotate SSH keys định kỳ
- Enable CloudTrail và Config

---

## 📖 Tài Liệu Đầy Đủ

| Document                                                   | Description                       |
| ---------------------------------------------------------- | --------------------------------- |
| [📚 SETUP-GUIDE.md](docs/SETUP-GUIDE.md)                   | Hướng dẫn cài đặt chi tiết từ A-Z |
| [🔌 API-REFERENCE.md](docs/API-REFERENCE.md)               | Tài liệu API đầy đủ               |
| [🧪 API-TESTING-GUIDE.md](docs/API-TESTING-GUIDE.md)       | Hướng dẫn test APIs               |
| [📘 QUICKSTART-SDWAN.md](docs/QUICKSTART-SDWAN.md)         | Quick start cho SD-WAN            |
| [🔧 openstack-edge-setup.md](docs/openstack-edge-setup.md) | Setup OpenStack Edge              |
| [🏛️ sdwan-architecture.md](docs/sdwan-architecture.md)     | Kiến trúc SD-WAN chi tiết         |

---

## 🙏 Acknowledgments

- **VPBank Technology Team** - Core development
- **AWS Solutions Architects** - Architecture guidance
- **Open Source Community** - Tools và libraries
- **Beta Testers** - Feedback và bug reports

---

## 📞 Support & Contact

- **Issues**: [GitHub Issues](https://github.com/rizy44/automation-iac-deploy-and-scaling-on-hybrid-cloud/issues)
- **Documentation**: [Wiki](https://github.com/rizy44/automation-iac-deploy-and-scaling-on-hybrid-cloud/wiki)
- **API Docs**: http://localhost:8000/docs

---

<div align="center">

**Made with ❤️ by VPBank Technology Team U1T-H1GH-3GO**

[Report Bug](https://github.com/rizy44/automation-iac-deploy-and-scaling-on-hybrid-cloud/issues) · [Request Feature](https://github.com/rizy44/automation-iac-deploy-and-scaling-on-hybrid-cloud/issues) · [Documentation](docs/)

</div>

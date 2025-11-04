# SD-WAN Hybrid Cloud - Quick Start Guide

Hướng dẫn nhanh để deploy SD-WAN architecture kết nối OpenStack với AWS.

## 🎯 Mục Tiêu

Deploy hybrid cloud infrastructure với:
- ✅ AWS Transit Gateway (central hub)
- ✅ Site-to-Site VPN (2 tunnels) 
- ✅ App VPC với ALB + Auto Scaling
- ✅ Shared Services VPC
- ✅ Kết nối OpenStack datacenter (172.10.0.0/16)

**Chi phí dự kiến**: ~$175/tháng

---

## 📋 Yêu Cầu

### OpenStack
- VM Ubuntu 22.04 (2 vCPU, 2GB RAM)
- Public IP (floating IP)
- Security group: Allow UDP 500, 4500, ESP

### AWS
- Account với $200 credit
- Region: ap-southeast-2
- Credentials trong `.env`

### Backend
- Server đang chạy trên port 8008
- Đã cấu hình `.env` với AWS credentials

---

## 🚀 Deploy Trong 5 Bước

### Bước 1: Tạo OpenStack VM

```bash
# Trên OpenStack
openstack server create \
  --flavor m1.medium \
  --image ubuntu-22.04 \
  --network openstack-internal \
  --key-name your-key \
  --security-group sdwan-edge \
  sdwan-edge-a

# Gán floating IP
openstack floating ip create external-network
openstack server add floating ip sdwan-edge-a 203.0.113.50
```

**Lưu lại Public IP**: `203.0.113.50` (thay bằng IP thực của bạn)

### Bước 2: Setup StrongSwan trên OpenStack

```bash
# SSH vào VM
ssh ubuntu@203.0.113.50

# Download và chạy script
curl -O http://YOUR_BACKEND_IP:8008/scripts/strongswan-edge.sh
sudo bash strongswan-edge.sh
```

Script sẽ cài đặt và cấu hình StrongSwan tự động.

### Bước 3: Deploy AWS Infrastructure

```bash
curl -X POST http://localhost:8008/sdwan/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "name_prefix": "my-sdwan",
    "region": "ap-southeast-2",
    "azs": ["ap-southeast-2a", "ap-southeast-2b"],
    "openstack_cidr": "172.10.0.0/16",
    "openstack_public_ip": "203.0.113.50",
    "app_vpc_cidr": "10.101.0.0/16",
    "shared_vpc_cidr": "10.103.0.0/16",
    "app_ami": "ami-0a25a306450a2cba3",
    "app_instance_type": "t3.micro",
    "app_min_size": 2,
    "app_max_size": 4,
    "app_desired_size": 2
  }'
```

**Lưu `stack_id`** từ response!

Thời gian deploy: ~10-15 phút ☕

### Bước 4: Lấy VPN Configuration

```bash
curl http://localhost:8008/sdwan/vpn-config/{stack_id} | jq > vpn-config.json
```

Example response:
```json
{
  "tunnel1": {
    "address": "52.63.123.45",
    "preshared_key": "SecureKey123..."
  },
  "tunnel2": {
    "address": "13.239.45.67",
    "preshared_key": "SecureKey123..."
  }
}
```

### Bước 5: Configure OpenStack Edge

Trên OpenStack VM:

```bash
# Edit IPsec config
sudo nano /etc/ipsec.conf
```

Replace placeholders:
- `OPENSTACK_PUBLIC_IP` → `203.0.113.50`
- `AWS_TUNNEL1_ADDRESS` → `52.63.123.45` (from vpn-config.json)
- `AWS_TUNNEL2_ADDRESS` → `13.239.45.67` (from vpn-config.json)

```bash
# Edit secrets
sudo nano /etc/ipsec.secrets
```

Replace:
- `VPN_PRESHARED_KEY` → `SecureKey123...` (from vpn-config.json)
- `AWS_TUNNEL1_ADDRESS` → `52.63.123.45`
- `AWS_TUNNEL2_ADDRESS` → `13.239.45.67`

```bash
# Start VPN
sudo systemctl restart strongswan

# Check status
sudo ipsec statusall
```

Bạn sẽ thấy:
```
Security Associations (2 up, 0 connecting):
  aws-tunnel1[1]: ESTABLISHED
  aws-tunnel2[2]: ESTABLISHED
```

---

## ✅ Test Connectivity

### 1. Test từ OpenStack VM

```bash
# Ping vào AWS App VPC (lấy IP từ AWS console)
ping 10.101.16.10

# Truy cập ALB (từ deployment response)
curl http://ALB_DNS_NAME
```

### 2. Test từ browser

Mở browser, truy cập:
```
http://ALB_DNS_NAME
```

Bạn sẽ thấy trang web: **"SD-WAN Hybrid Cloud Architecture"**

### 3. Check VPN status

```bash
sudo ipsec statusall
sudo journalctl -u strongswan -n 50
```

---

## 📊 Monitoring

### API Endpoints

```bash
# List all stacks
curl http://localhost:8008/sdwan/stacks

# Get VPN config
curl http://localhost:8008/sdwan/vpn-config/{stack_id}

# Health check
curl http://localhost:8008/sdwan/health
```

### AWS Console

- Transit Gateway: VPC → Transit Gateways
- VPN Connections: VPC → Site-to-Site VPN Connections
- Auto Scaling: EC2 → Auto Scaling Groups
- Load Balancer: EC2 → Load Balancers

---

## 🗑️ Cleanup

Để xóa toàn bộ infrastructure:

```bash
curl -X DELETE http://localhost:8008/sdwan/destroy/{stack_id}
```

Hoặc manual:
```bash
cd .infra/work/{stack_id}
terraform destroy -auto-approve
```

**Lưu ý**: Xóa hết để tránh tốn chi phí!

---

## 🐛 Troubleshooting

### VPN không kết nối

```bash
# Check logs
sudo journalctl -u strongswan -f

# Restart VPN
sudo systemctl restart strongswan

# Manual bring up
sudo ipsec up aws-tunnel1
sudo ipsec up aws-tunnel2
```

### Không ping được AWS

```bash
# Check routing
ip route show

# Should see:
# 10.101.0.0/16 via 169.254.10.1 dev vti1
```

### Application không load

```bash
# Check ASG instances
curl http://localhost:8008/sdwan/vpn-config/{stack_id}

# Verify ALB target health in AWS Console
```

---

## 📚 Tài Liệu Chi Tiết

- [OpenStack Edge Setup](openstack-edge-setup.md) - Hướng dẫn setup chi tiết
- [Architecture Documentation](sdwan-architecture.md) - Kiến trúc và design
- [Main README](../README.md) - Thông tin chung về project

---

## 💰 Chi Phí Ước Tính

| Service | Monthly Cost |
|---------|-------------|
| Transit Gateway | $36 |
| TGW Attachments (2x) | $72 |
| Site-to-Site VPN | $36 |
| EC2 (t3.micro x2) | $15 |
| NAT Gateway | $33 |
| ALB | $16 |
| Data Transfer | $10 |
| **Total** | **~$175** |

**Tips tiết kiệm**:
- Stop instances khi không dùng (giảm ~$15)
- Dùng single NAT Gateway (giảm ~$33)
- Deploy ngắn hạn cho demo/test

---

## 🎓 Demo/Competition Tips

Cho thi đấu với budget $200:

1. **Deploy trước 1 ngày** để test kỹ
2. **Prepare backup plan** nếu VPN fail
3. **Document everything** với screenshots
4. **Mention production enhancements**:
   - Direct Connect cho low latency
   - Multi-AZ NAT Gateway cho HA
   - CloudWatch dashboards
5. **Cleanup ngay sau khi demo** để tránh vượt budget

---

## 🆘 Support

Nếu gặp vấn đề:

1. Check logs: `.infra/work/{stack_id}/`
2. Review documentation ở `docs/`
3. Test từng component riêng biệt
4. Verify AWS credentials và permissions

**Good luck with your hybrid cloud deployment!** 🚀


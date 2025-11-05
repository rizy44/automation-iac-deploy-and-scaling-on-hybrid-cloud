# 🚀 Quick Start Guide

5 phút để chạy được project!

---

## Bước 1: Clone & Setup (1 phút)

```bash
# Clone repository
git clone <repository-url>
cd code

# Run automated setup
chmod +x setup.sh
./setup.sh
```

Script sẽ tự động:
- ✅ Kiểm tra Python, Terraform, AWS CLI
- ✅ Cài đặt dependencies nếu thiếu
- ✅ Tạo virtual environment
- ✅ Cài packages Python
- ✅ Tạo file `.env` template

---

## Bước 2: Configure Credentials (2 phút)

```bash
# Edit .env file
nano .env
```

**Thêm 2 keys bắt buộc:**

### 2.1. AWS Credentials
```bash
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
```

Lấy từ: AWS Console → IAM → Users → Security Credentials

### 2.2. Gemini API Key (cho AI features)
```bash
GEMINI_API_KEY=...
```

Lấy miễn phí tại: https://makersuite.google.com/app/apikey

**Save và thoát** (Ctrl+X, Y, Enter)

---

## Bước 3: Start Backend (30 giây)

```bash
# Activate venv
source .venv/bin/activate

# Start server
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8008 --reload
```

**Thấy log này = thành công:**
```
INFO: Uvicorn running on http://0.0.0.0:8008
INFO: Application startup complete.
```

---

## Bước 4: Test API (1 phút)

### Open browser: http://localhost:8008/docs

Bạn sẽ thấy **Swagger UI** với tất cả API endpoints.

### Test deploy (terminal mới):

```bash
curl -X POST http://localhost:8008/elb/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "region": "ap-southeast-2",
    "vpc_cidr": "10.100.0.0/16",
    "subnet_cidr": "10.100.1.0/24",
    "az": "ap-southeast-2a",
    "name_prefix": "demo",
    "key_name": "vpbank-key",
    "instance_count": 1,
    "ami": "ami-0eeab253db7e765a9",
    "instance_type": "t3.medium",
    "auto_install_monitoring": true
  }' | jq
```

**Lưu ý:** Cần tạo SSH key `vpbank-key` trong AWS trước!

```bash
aws ec2 create-key-pair \
  --key-name vpbank-key \
  --query 'KeyMaterial' \
  --output text \
  --region ap-southeast-2 > ~/.ssh/vpbank-key.pem

chmod 400 ~/.ssh/vpbank-key.pem
```

---

## 🎉 Done!

Bây giờ bạn có thể:
- ✅ Deploy infrastructure qua API
- ✅ Scale EC2 instances
- ✅ Get AI recommendations
- ✅ Monitor với Grafana/Mimir/Loki

---

## 📚 Đọc tiếp

- **Full setup:** `SETUP-GUIDE.md`
- **API docs:** `API-DOCUMENTATION-FRONTEND.md`
- **Scaling guide:** `SCALING-SETUP-GUIDE.md`

---

## 🐛 Lỗi thường gặp

### "IndentationError"
```bash
# Fix file syntax
nano backend/api/elb.py
# Line 19 must NOT have extra spaces at start
```

### "Missing AWS creds"
```bash
# Check .env
cat .env | grep AWS_ACCESS_KEY_ID
# Must not be "your_access_key_here"
```

### "Module not found"
```bash
source .venv/bin/activate
pip install -r backend/requirements.txt
```

---

## AMI IDs cho các regions

| Region | AMI (Ubuntu 22.04) |
|--------|-------------------|
| ap-southeast-2 (Sydney) | ami-0eeab253db7e765a9 |
| ap-southeast-1 (Singapore) | ami-0c802847a7dd848c0 |
| us-east-1 (N. Virginia) | ami-0c55b159cbfafe1f0 |

Tìm AMI cho region khác:
```bash
aws ec2 describe-images \
  --owners 099720109477 \
  --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" \
  --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' \
  --output text \
  --region <your-region>
```

---

**Happy Coding! 🚀**


# Hướng Dẫn Cài Đặt Hệ Thống
## VPBank Hybrid Cloud Platform

---

## 📋 Yêu Cầu Hệ Thống

### Hệ điều hành được hỗ trợ:
- **Ubuntu**: 20.04 LTS, 22.04 LTS (khuyến nghị)
- **CentOS/RHEL**: 8.x, 9.x
- **Amazon Linux**: 2

### Phần cứng tối thiểu:
- **CPU**: 2 cores
- **RAM**: 4GB
- **Disk**: 20GB trống
- **Network**: Kết nối internet ổn định

---

## 🔧 Bước 1: Cài Đặt Python 3 và Các Công Cụ Cơ Bản

### Ubuntu/Debian:
```bash
# Cập nhật package list
sudo apt update && sudo apt upgrade -y

# Cài đặt Python 3 và các tools cần thiết
sudo apt install python3 python3-pip python3-venv python3-dev \
                 git curl wget unzip build-essential -y

# Kiểm tra version Python
python3 --version
pip3 --version
```

### CentOS/RHEL/Amazon Linux:
```bash
# Cập nhật hệ thống
sudo yum update -y

# Cài đặt Python 3 và tools
sudo yum install python3 python3-pip python3-devel \
                 git curl wget unzip gcc gcc-c++ make -y

# Kiểm tra version
python3 --version
pip3 --version
```

---

## ☁️ Bước 2: Cài Đặt AWS CLI v2

```bash
# Download AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"

# Giải nén và cài đặt
unzip awscliv2.zip
sudo ./aws/install

# Dọn dẹp file tạm
rm -rf awscliv2.zip aws/

# Kiểm tra cài đặt
aws --version
```

### Cấu hình AWS credentials:
```bash
# Cấu hình AWS access keys
aws configure

# Nhập thông tin:
# AWS Access Key ID: [Your Access Key]
# AWS Secret Access Key: [Your Secret Key] 
# Default region name: ap-southeast-2
# Default output format: json

# Kiểm tra cấu hình
aws sts get-caller-identity
```

---

## 🏗️ Bước 3: Cài Đặt Terraform

```bash
# Download Terraform 1.6.0
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip

# Giải nén và di chuyển vào PATH
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/

# Dọn dẹp
rm terraform_1.6.0_linux_amd64.zip

# Kiểm tra cài đặt
terraform --version
```

---

## 📁 Bước 4: Clone Repository và Chuẩn Bị Project

```bash
# Clone repository (thay thế URL thực tế)
git clone https://github.com/vpbank/hybrid-cloud-platform.git
cd hybrid-cloud-platform

# Hoặc nếu đã có source code
cd /path/to/your/project
```

---

## 🐍 Bước 5: Tạo Python Virtual Environment

```bash
# Tạo virtual environment
python3 -m venv .venv

# Kích hoạt virtual environment
source .venv/bin/activate

# Kiểm tra Python trong venv
which python
python --version
```

**Lưu ý**: Luôn kích hoạt venv trước khi làm việc:
```bash
source .venv/bin/activate
```

---

## 📦 Bước 6: Cài Đặt Python Dependencies

```bash
# Đảm bảo đang trong virtual environment
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Cài đặt dependencies từ requirements.txt
pip install -r backend/requirements.txt

# Kiểm tra các package đã cài
pip list
```

---

## ⚙️ Bước 7: Cấu Hình Environment Variables

```bash
# Tạo file .env từ template (nếu có)
cp .env.example .env

# Hoặc tạo file .env mới
cat > .env << 'EOF'
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

# Logging
LOG_LEVEL=INFO
EOF
```

### Lấy Gemini API Key:
1. Truy cập: https://makersuite.google.com/app/apikey
2. Tạo API key mới
3. Copy và paste vào file `.env`

---

## 🚀 Bước 8: Chạy Backend Server

```bash
# Đảm bảo đang trong virtual environment và thư mục gốc
source .venv/bin/activate
cd /path/to/project

# Chạy server development
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload

# Hoặc chạy production
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000
```

Server sẽ chạy tại: http://localhost:8000

---

## ✅ Bước 9: Kiểm Tra Cài Đặt

### Kiểm tra API Documentation:
```bash
# Mở browser hoặc dùng curl
curl http://localhost:8000/docs

# Kiểm tra health check
curl http://localhost:8000/scaling/stacks
```

### Kiểm tra các service:
```bash
# Test AWS connection
aws ec2 describe-regions --region ap-southeast-2

# Test Terraform
terraform version

# Test Python environment
python -c "import fastapi, requests, pydantic; print('All packages OK')"
```

---

## 🔧 Troubleshooting

### Lỗi Python/Pip:
```bash
# Nếu pip3 không tìm thấy
sudo apt install python3-pip  # Ubuntu
sudo yum install python3-pip  # CentOS

# Nếu venv không hoạt động
python3 -m pip install --user virtualenv
python3 -m virtualenv .venv
```

### Lỗi AWS CLI:
```bash
# Nếu aws command không tìm thấy
echo 'export PATH=$PATH:/usr/local/bin' >> ~/.bashrc
source ~/.bashrc

# Kiểm tra AWS credentials
aws configure list
```

### Lỗi Terraform:
```bash
# Nếu terraform không tìm thấy
sudo chmod +x /usr/local/bin/terraform
echo 'export PATH=$PATH:/usr/local/bin' >> ~/.bashrc
source ~/.bashrc
```

### Lỗi Port đã sử dụng:
```bash
# Tìm process đang dùng port 8000
sudo lsof -i :8000

# Kill process nếu cần
sudo kill -9 <PID>

# Hoặc chạy trên port khác
python -m uvicorn backend.app:app --port 8001
```

---

## 🔄 Chạy Hệ Thống Hàng Ngày

### Script khởi động nhanh:
```bash
#!/bin/bash
# save as start.sh

cd /path/to/project
source .venv/bin/activate
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
```

```bash
chmod +x start.sh
./start.sh
```

### Tự động khởi động với systemd (Production):
```bash
# Tạo service file
sudo tee /etc/systemd/system/vpbank-cloud.service > /dev/null <<EOF
[Unit]
Description=VPBank Hybrid Cloud Platform
After=network.target

[Service]
Type=simple
User=deployer
WorkingDirectory=/path/to/project
Environment=PATH=/path/to/project/.venv/bin
ExecStart=/path/to/project/.venv/bin/python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Enable và start service
sudo systemctl daemon-reload
sudo systemctl enable vpbank-cloud
sudo systemctl start vpbank-cloud

# Kiểm tra status
sudo systemctl status vpbank-cloud
```

---

## 📚 Tài Liệu Tham Khảo

- **API Documentation**: `API-DOCS-FRONTEND.md`
- **Project Overview**: `README.md`
- **FastAPI Docs**: http://localhost:8000/docs
- **AWS CLI Guide**: https://docs.aws.amazon.com/cli/
- **Terraform Docs**: https://terraform.io/docs

---

## 🆘 Hỗ Trợ

Nếu gặp vấn đề trong quá trình cài đặt:

1. Kiểm tra logs: `tail -f /var/log/syslog`
2. Kiểm tra Python errors trong terminal
3. Verify AWS credentials: `aws sts get-caller-identity`
4. Check network connectivity: `curl -I https://api.github.com`

---

*Cập nhật lần cuối: November 2025*

# Automation IaC Deploy & Scaling on Hybrid Cloud — Local Setup & Run Guide

> Hướng dẫn chạy **backend** sau khi `git pull`, dùng `.venv`, `.env`, và Terraform để render template **Jinja → Terraform** và deploy lên AWS.

---

## 1) Yêu cầu hệ thống

* **Python** 3.10+ (khuyến nghị 3.11)
* **Terraform** ≥ **1.6** (để khớp `required_version = ">= 1.6"` trong template)
* **AWS account** với **Access Key** & **Secret Key** (chỉ 2 biến, *không dùng session token*)
* Internet outbound để tải provider plugins

Kiểm tra nhanh:

```bash
python --version
terraform -version
```

---

## 2) Cấu trúc thư mục (tham chiếu)

```
<repo-root>/
├─ backend/
│  ├─ app.py
│  ├─ core/
│  │  ├─ config.py
│  │  └─ logging.py
│  ├─ api/
│  │  └─ elb.py
│  ├─ services/
│  │  └─ terraform.py
│  ├─ templates/
│  │  └─ terraform/
│  │     └─ aws/
│  │        └─ main.tf.j2       # Template Jinja giữ NGUYÊN như bạn đã cung cấp
│  ├─ requirements.txt
│  └─ __init__.py
├─ .env.example                  # Mẫu biến môi trường
├─ .gitignore
└─ scripts/
   ├─ run-dev.sh                 # (tuỳ chọn) Chạy uvicorn dev
   └─ setup-env.sh               # (tuỳ chọn) Tạo .venv & cài deps
```

> **Lưu ý:** Template `backend/templates/terraform/aws/main.tf.j2` đã giữ nguyên. Backend chỉ render biến & gọi Terraform.

---

## 3) Tạo `.venv`, cài dependencies, cấu hình `.env`

### Linux/macOS

```bash
# 1) Vào root của repo
cd <repo-root>

# 2) Tạo & kích hoạt venv
python -m venv .venv
source .venv/bin/activate

# 3) Cài dependencies
pip install -r backend/requirements.txt

# 4) Tạo file .env từ mẫu và CHỈNH SỬA 2 biến AWS
cp .env.example .env
chmod 600 .env

# 5) Mở .env và điền đúng 2 biến dưới đây:
# AWS_ACCESS_KEY_ID=...
# AWS_SECRET_ACCESS_KEY=...

# 6) (khuyến nghị) Kiểm tra đường dẫn Terraform trong .env
# TF_BIN=/usr/bin/terraform   # hoặc `which terraform`
```

### Windows (PowerShell)

```powershell
cd <repo-root>
py -m venv .venv
. .\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
Copy-Item .env.example .env
# Mở .env và điền AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY
```

---

## 4) Chạy server (dev)

```bash
# Cách 1: trực tiếp
export PYTHONPATH=.
uvicorn backend.app:app --reload --host 0.0.0.0 --port 8008

# Cách 2: dùng script (nếu có scripts/run-dev.sh)
bash scripts/run-dev.sh
```

Server mặc định đọc `.env` ở **root repo**, và lưu workdir Terraform tại `.infra/work/<stack_id>/`.

---

## 5) Cấu hình `.env` (tham chiếu)

```ini
# App
APP_HOST=0.0.0.0
APP_PORT=8008
LOG_LEVEL=INFO
ENV=dev

# Templates & Terraform
TEMPLATE_DIR=backend/templates
TF_BIN=/usr/bin/terraform
TF_WORK_ROOT=.infra/work
TF_TIMEOUT_SEC=900

# Mặc định tiện dụng (có thể override bằng payload API)
DEFAULT_REGION=ap-southeast-2
DEFAULT_AZ=ap-southeast-2a
DEFAULT_INSTANCE_TYPE=t3.micro

# ===== AWS credentials (CHỈ 2 biến này) =====
AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY=YOUR_SECRET_ACCESS_KEY
```

> `.env` đã có trong `.gitignore`. **Không commit** file này.

---

## 6) API — Deploy AWS NLB + EC2 từ template

**Endpoint:** `POST /elb/deploy`

**Body (JSON):**

```json
{
  "region": "ap-southeast-2",
  "vpc_cidr": "10.20.0.0/16",
  "subnet_cidr": "10.20.10.0/24",
  "az": "ap-southeast-2a",
  "name_prefix": "bpp",
  "key_name": "bpp-key",
  "instance_count": 2,
  "ami": "ami-0a25a306450a2cba3",
  "instance_type": "t3.micro",
  "user_data_inline": "#!/usr/bin/env bash\necho hello > /var/tmp/ok\n"
}
```

**Chú ý:** Backend **không nhận** AWS creds qua API. Creds được nạp từ `.env`.

**Test nhanh:**

```bash
curl -X POST http://localhost:8008/elb/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "region":"ap-southeast-2a",
    "vpc_cidr":"10.20.0.0/16",
    "subnet_cidr":"10.20.10.0/24",
    "az":"ap-southeast-2a",
    "name_prefix":"bpp",
    "key_name":"bpp-key",
    "instance_count":2,
    "ami":"ami-0a25a306450a2cba3",
    "instance_type":"t3.micro",
    "user_data_inline":"#!/usr/bin/env bash\\necho hello > /var/tmp/ok\\n"
  }'
```

**Kết quả trả về** gồm:

* `stack_id`: thư mục workdir tương ứng trong `.infra/work/<stack_id>/`
* `phase`: `APPLIED` hoặc `FAILED_INIT/FAILED_APPLY/FAILED_CREDENTIALS`
* `outputs`: `instance_dns`, `instance_public_ip`, `nlb_dns_name`
* `logs.init`, `logs.apply`, `logs.output` để debug

---

## 7) Artifacts & bảo mật

* Terraform render ra: `.infra/work/<stack_id>/main.tf`
* PEM do template tạo: `.infra/work/<stack_id>/<key_name>.pem` (**nhạy cảm**)
* Một số private material có thể tồn tại trong **Terraform state**. Ở môi trường production, cân nhắc:

  * Tạo sẵn keypair và chỉ import **public key** (không dùng `tls_private_key` + `local_file`)
  * Dùng **remote backend** & secret manager

---

## 8) Lỗi thường gặp & cách xử lý

* **`FAILED_CREDENTIALS`**: Thiếu hoặc sai `AWS_ACCESS_KEY_ID/SECRET` trong `.env` → mở `.env` và điền đúng; đảm bảo không có khoảng trắng thừa.
* **`terraform: command not found`**: Sửa `TF_BIN` trong `.env` trỏ đúng binary (`which terraform`).
* **Provider version conflicts**: Xoá `.terraform/` trong workdir của stack, chạy lại; hoặc nâng Terraform ≥ 1.6.
* **Tên NLB quá dài**: `name_prefix` nên ngắn (≤ 10 ký tự) để tránh vượt giới hạn 32 ký tự.

---

## 9) Nâng cao (tuỳ chọn)

* **systemd service**: chạy uvicorn như service, dùng `EnvironmentFile=/path/to/.env` để nạp creds.
* **Docker hoá**: build image chứa Python + Terraform, mount `.env` & `.infra/work/` làm volume.

---

## 10) Bản quyền & trách nhiệm

* Mã và template phục vụ mục đích học tập/nghiên cứu. Kiểm tra quota/cost AWS trước khi

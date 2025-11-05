# Setup Guide - VPBank Hybrid Cloud Platform

Hướng dẫn cài đặt và chạy project từ đầu cho collaborators.

---

## 📋 Prerequisites

### 1. System Requirements
- **OS**: Ubuntu 20.04+ / macOS / WSL2
- **Python**: 3.10+
- **Terraform**: 1.6+
- **Git**: 2.x+

### 2. AWS Account
- AWS Access Key ID
- AWS Secret Access Key
- Permissions: EC2, VPC, ELB, IAM

### 3. Gemini API Key (for AI features)
- Get free key from: https://makersuite.google.com/app/apikey

---

## 🚀 Quick Start (5 phút)

```bash
# 1. Clone repository
git clone <repository-url>
cd code

# 2. Run setup script
./setup.sh

# 3. Configure .env
cp .env.example .env
nano .env  # Add your AWS keys and Gemini API key

# 4. Start backend
source .venv/bin/activate
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8008 --reload
```

---

## 📝 Detailed Setup Instructions

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd code

# Check structure
ls -la
# Should see: backend/, docs/, .gitignore, README.md, etc.
```

### Step 2: Install System Dependencies

#### Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    terraform \
    awscli \
    git
```

#### macOS:
```bash
brew install python terraform awscli
```

#### Verify installations:
```bash
python3 --version   # Should be 3.10+
terraform --version # Should be 1.6+
aws --version       # AWS CLI 2.x
```

### Step 3: Create Python Virtual Environment

```bash
# Create venv
python3 -m venv .venv

# Activate venv
source .venv/bin/activate

# Verify activation (should see (.venv) in prompt)
which python
# Output: /home/user/code/.venv/bin/python
```

**Important Notes:**
- Virtual environment đảm bảo dependencies isolated
- File `.venv/` không được push lên Git (đã có trong `.gitignore`)
- Mỗi collaborator tự tạo venv trên máy mình

### Step 4: Install Python Dependencies

```bash
# Make sure venv is activated
source .venv/bin/activate

# Install all requirements
pip install --upgrade pip
pip install -r backend/requirements.txt

# Verify installations
pip list | grep -E "fastapi|uvicorn|terraform|requests|apscheduler"
```

**Expected packages:**
- fastapi
- uvicorn
- python-dotenv
- jinja2
- pydantic>=2
- requests>=2.31.0
- apscheduler>=3.10.4

### Step 5: Configure AWS Credentials

#### Option 1: Using .env file (Recommended)

```bash
# Create .env from example
cat > .env <<EOF
# AWS Credentials
AWS_ACCESS_KEY_ID=AKIA...your_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here

# AWS Configuration
DEFAULT_REGION=ap-southeast-2
DEFAULT_AZ=ap-southeast-2a
DEFAULT_INSTANCE_TYPE=t3.medium

# Terraform
TF_BIN=/usr/bin/terraform
TF_WORK_ROOT=.infra/work
TF_TIMEOUT_SEC=900

# Backend
APP_HOST=0.0.0.0
APP_PORT=8008
LOG_LEVEL=INFO
ENV=dev

# AI Advisor (Get from https://makersuite.google.com/app/apikey)
GEMINI_API_KEY=your_gemini_api_key_here

# Auto-scaling
AUTO_SCALING_ENABLED=false
AUTO_SCALING_INTERVAL_MINUTES=5
AUTO_SCALING_CONFIDENCE_THRESHOLD=0.7
SCALE_UP_MAX_INSTANCES=20
SCALE_DOWN_MIN_INSTANCES=1
EOF

# Edit with your keys
nano .env
```

#### Option 2: Using AWS CLI (Alternative)

```bash
aws configure
# AWS Access Key ID: AKIA...
# AWS Secret Access Key: ...
# Default region: ap-southeast-2
# Default output format: json
```

### Step 6: Verify Configuration

```bash
# Test AWS credentials
aws sts get-caller-identity

# Should return your AWS account info:
# {
#   "UserId": "AIDA...",
#   "Account": "123456789012",
#   "Arn": "arn:aws:iam::123456789012:user/yourname"
# }
```

### Step 7: Get Ubuntu AMI for Your Region

```bash
# Get latest Ubuntu 22.04 AMI for ap-southeast-2
aws ec2 describe-images \
  --owners 099720109477 \
  --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" \
            "Name=state,Values=available" \
  --query 'Images | sort_by(@, &CreationDate) | [-1].[ImageId,Name,CreationDate]' \
  --output table \
  --region ap-southeast-2

# Example output:
# ami-0eeab253db7e765a9  ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-20241101
```

**AMI IDs by Region (Ubuntu 22.04):**
| Region | AMI ID | Notes |
|--------|--------|-------|
| ap-southeast-2 | ami-0eeab253db7e765a9 | Sydney (Currently using) |
| ap-southeast-1 | ami-0c802847a7dd848c0 | Singapore |
| us-east-1 | ami-0c55b159cbfafe1f0 | N. Virginia |
| us-west-2 | ami-0735c191cf914754d | Oregon |

**To find AMI for other regions:**
```bash
aws ec2 describe-images \
  --owners 099720109477 \
  --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" \
  --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' \
  --output text \
  --region <your-region>
```

---

## 🔧 Running the Backend

### Start Development Server

```bash
# Activate venv (if not already)
source .venv/bin/activate

# Start backend with hot-reload
cd /path/to/code
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8008 --reload
```

**Expected output:**
```
INFO:     Will watch for changes in these directories: ['/path/to/code']
INFO:     Uvicorn running on http://0.0.0.0:8008 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Starting auto-scaling scheduler (interval: 5 minutes, confidence threshold: 0.7)
INFO:     Auto-scaling scheduler started successfully
INFO:     Application startup complete.
```

### Access API Documentation

Open browser: **http://localhost:8008/docs**

You'll see interactive Swagger UI with all API endpoints.

---

## 🧪 Testing the APIs

### Test 1: Health Check

```bash
# Check if backend is running
curl http://localhost:8008/docs

# Should return HTML (Swagger UI page)
```

### Test 2: Deploy Infrastructure

**Important:** Make sure you have SSH key pair in AWS first!

```bash
# Create SSH key pair if not exists
aws ec2 create-key-pair \
  --key-name vpbank-test-key \
  --query 'KeyMaterial' \
  --output text \
  --region ap-southeast-2 > ~/.ssh/vpbank-test-key.pem

chmod 400 ~/.ssh/vpbank-test-key.pem
```

**Deploy stack with monitoring:**

```bash
curl -X POST http://localhost:8008/elb/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "region": "ap-southeast-2",
    "vpc_cidr": "10.100.0.0/16",
    "subnet_cidr": "10.100.1.0/24",
    "az": "ap-southeast-2a",
    "name_prefix": "test-stack",
    "key_name": "vpbank-test-key",
    "instance_count": 1,
    "ami": "ami-0eeab253db7e765a9",
    "instance_type": "t3.medium",
    "auto_install_monitoring": true
  }' | jq

# Expected response:
# {
#   "phase": "APPLIED",
#   "stack_id": "20251105123456-abc12345",
#   "outputs": {
#     "nlb_dns_name": {...},
#     "instance_public_ip": {...}
#   }
# }
```

**Save stack_id for next tests!**

### Test 3: List Stacks

```bash
curl http://localhost:8008/scaling/stacks | jq

# Expected:
# {
#   "success": true,
#   "count": 1,
#   "stacks": [...]
# }
```

### Test 4: Get Stack Info

```bash
STACK_ID="20251105123456-abc12345"  # Use your stack_id

curl http://localhost:8008/scaling/stack/$STACK_ID/info | jq

# Expected:
# {
#   "success": true,
#   "stack": {
#     "stack_id": "...",
#     "current_instance_count": 1,
#     "instances": ["3.xxx.xxx.xxx"],
#     "nlb_dns": "test-stack-nlb-xxx.elb.ap-southeast-2.amazonaws.com"
#   }
# }
```

### Test 5: Get Metrics

**Note:** Metrics require Grafana Agent running on instances (wait 5-10 minutes after deploy)

```bash
curl http://localhost:8008/scaling/stack/$STACK_ID/metrics | jq

# Expected (if metrics available):
# {
#   "success": true,
#   "metrics": {
#     "avg_cpu_percent": 5.2,
#     "avg_memory_percent": 35.8,
#     "instance_count": 1
#   }
# }
```

### Test 6: AI Recommendation

```bash
curl -X POST http://localhost:8008/scaling/stack/$STACK_ID/recommend | jq

# Expected:
# {
#   "success": true,
#   "recommendation": {
#     "action": "no_change",
#     "target_count": 1,
#     "reason": "Resource usage within normal range",
#     "confidence": 0.85
#   }
# }
```

### Test 7: Manual Scale Up

```bash
curl -X POST http://localhost:8008/scaling/stack/scale \
  -H "Content-Type: application/json" \
  -d '{
    "stack_id": "'$STACK_ID'",
    "target_count": 2,
    "reason": "Testing manual scale-up"
  }' | jq

# Expected:
# {
#   "success": true,
#   "old_count": 1,
#   "new_count": 2,
#   "action": "scale_up",
#   "message": "Successfully scaled from 1 to 2 instances"
# }
```

**Verify in AWS Console:**
- Go to EC2 → Instances
- Should see 2 instances with tag `Name=test-stack-1` and `test-stack-2`

### Test 8: Scale Down

```bash
curl -X POST http://localhost:8008/scaling/stack/scale \
  -H "Content-Type: application/json" \
  -d '{
    "stack_id": "'$STACK_ID'",
    "target_count": 1,
    "reason": "Testing scale-down (LIFO)"
  }' | jq

# Expected:
# {
#   "success": true,
#   "old_count": 2,
#   "new_count": 1,
#   "action": "scale_down"
# }
```

**Verify:** Instance `test-stack-2` (highest index) should be terminated (LIFO)

---

## 🤖 Testing AI Auto-Scaling

### Enable Auto-Scaling

```bash
# Stop backend (Ctrl+C)

# Update .env
nano .env
# Change: AUTO_SCALING_ENABLED=true

# Restart backend
source .venv/bin/activate
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8008 --reload
```

**Logs should show:**
```
INFO: Starting auto-scaling scheduler (interval: 5 minutes, confidence threshold: 0.7)
INFO: Auto-scaling scheduler started successfully
```

### Simulate High Load

```bash
# SSH into instance
ssh -i ~/.ssh/vpbank-test-key.pem ubuntu@<instance_public_ip>

# Install stress tool
sudo apt-get update
sudo apt-get install -y stress

# Run CPU stress test (10 minutes)
stress --cpu 2 --timeout 600s &

# Exit SSH
exit
```

### Monitor Auto-Scaling

Watch backend logs - after 5-10 minutes, should see:

```
INFO: Starting auto-scaling check for all stacks
INFO: Found 1 active stack(s)
INFO: Stack xxx: Action=scale_up, Current=1, Target=2, Confidence=0.92, Reason=High CPU usage
INFO: Stack xxx: Executing scale_up (confidence 0.92 >= threshold 0.7)
INFO: Stack xxx: Successfully scaled from 1 to 2 instances
```

---

## 📚 Project Structure

```
code/
├── backend/
│   ├── api/
│   │   ├── elb.py          # ELB deployment endpoints
│   │   ├── sdwan.py        # SD-WAN deployment endpoints
│   │   └── scaling.py      # Scaling management endpoints
│   ├── core/
│   │   ├── config.py       # Configuration settings
│   │   └── logging.py      # Logging setup
│   ├── services/
│   │   ├── terraform.py    # Terraform execution
│   │   ├── scaling_service.py   # Scaling logic
│   │   ├── metrics_service.py   # Metrics queries
│   │   ├── ai_advisor.py        # Gemini AI integration
│   │   └── scheduler.py         # Auto-scaling scheduler
│   ├── templates/
│   │   ├── main.tf.j2      # Main Terraform template
│   │   └── sdwan-hybrid.tf.j2
│   ├── app.py              # FastAPI application
│   └── requirements.txt    # Python dependencies
├── docs/
│   ├── API-REFERENCE.md
│   └── QUICKSTART-SDWAN.md
├── .env.example            # Environment variables template
├── .gitignore
├── README.md
├── SETUP-GUIDE.md          # This file
├── API-DOCUMENTATION-FRONTEND.md
├── SCALING-SETUP-GUIDE.md
└── IMPLEMENTATION-SUMMARY.md
```

---

## 🐛 Troubleshooting

### Issue 1: "IndentationError" when starting backend

**Solution:**
```bash
# Check Python syntax
python3 -m py_compile backend/api/elb.py
python3 -m py_compile backend/app.py

# If errors found, fix indentation in the file
```

### Issue 2: "Module not found" errors

**Solution:**
```bash
# Activate venv
source .venv/bin/activate

# Reinstall dependencies
pip install -r backend/requirements.txt
```

### Issue 3: "Missing AWS creds in .env"

**Solution:**
```bash
# Check .env file exists
ls -la .env

# Verify AWS keys are set
cat .env | grep AWS_ACCESS_KEY_ID

# If missing, add them
nano .env
```

### Issue 4: Terraform apply fails

**Solution:**
```bash
# Check Terraform version
terraform --version

# Check AWS credentials
aws sts get-caller-identity

# Check AWS limits (EC2, VPC, EIP quotas)
aws service-quotas get-service-quota \
  --service-code ec2 \
  --quota-code L-1216C47A \
  --region ap-southeast-2
```

### Issue 5: Metrics showing 0.0

**Reason:** Grafana Agent not installed or not sending data yet

**Solution:**
```bash
# Wait 5-10 minutes after deployment for:
# - Docker containers to start
# - Grafana Agent to initialize
# - Metrics to be collected

# Check if monitoring is running (SSH into instance)
ssh -i ~/.ssh/vpbank-test-key.pem ubuntu@<instance_ip>
docker ps
# Should see: grafana, loki, mimir containers

# Check Grafana Agent
sudo systemctl status grafana-agent
```

### Issue 6: "Gemini API key not configured"

**Solution:**
```bash
# Get API key from: https://makersuite.google.com/app/apikey

# Add to .env
echo "GEMINI_API_KEY=your_key_here" >> .env

# Restart backend
```

---

## 🧹 Cleanup

### Destroy a Stack

```bash
STACK_ID="your_stack_id"

# Option 1: Via API (recommended)
curl -X POST http://localhost:8008/aws/destroy \
  -H "Content-Type: application/json" \
  -d '{"workspace_id": "'$STACK_ID'"}'

# Option 2: Manual Terraform
cd .infra/work/$STACK_ID
terraform destroy -auto-approve
```

### Clean All Stacks

```bash
# WARNING: This destroys ALL infrastructure!

for stack_dir in .infra/work/*/; do
  cd "$stack_dir"
  terraform destroy -auto-approve
  cd -
done
```

### Remove Virtual Environment

```bash
# Deactivate venv
deactivate

# Remove directory
rm -rf .venv
```

---

## 📖 Additional Documentation

- **API Reference:** `API-DOCUMENTATION-FRONTEND.md`
- **Scaling Guide:** `SCALING-SETUP-GUIDE.md`
- **Implementation Details:** `IMPLEMENTATION-SUMMARY.md`
- **Interactive API Docs:** http://localhost:8008/docs

---

## 🔐 Security Best Practices

### 1. Never Commit Secrets
```bash
# .gitignore already includes:
# - .env
# - *.pem
# - *.tfvars
# - deploy_metadata.json

# Verify before committing:
git status
git diff
```

### 2. Use IAM Roles in Production
Instead of AWS keys in `.env`, use IAM instance roles or ECS task roles.

### 3. Rotate Keys Regularly
```bash
# Generate new AWS access key
aws iam create-access-key --user-name your-username

# Update .env with new key
# Deactivate old key after testing
```

---

## 👥 Team Collaboration

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/your-feature

# Make changes
# ...

# Commit
git add .
git commit -m "Add: your feature description"

# Push
git push origin feature/your-feature

# Create Pull Request on GitHub/GitLab
```

### Before Pushing

```bash
# Check no secrets committed
git diff

# Run linter (if available)
# flake8 backend/
# pylint backend/

# Test locally
python -m uvicorn backend.app:app --reload
```

---

## 🚀 Production Deployment

### Recommended Setup:
1. **Use Docker** for backend
2. **Use systemd** service for auto-start
3. **Use Nginx** reverse proxy
4. **Use HTTPS** with Let's Encrypt
5. **Use RDS** for database (future)
6. **Use Parameter Store** for secrets

### Example systemd service:
```ini
[Unit]
Description=VPBank Infrastructure Backend
After=network.target

[Service]
Type=simple
User=deployer
WorkingDirectory=/opt/vpbank-code
Environment="PATH=/opt/vpbank-code/.venv/bin"
ExecStart=/opt/vpbank-code/.venv/bin/uvicorn backend.app:app --host 0.0.0.0 --port 8008
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## 📞 Support

- **Documentation:** See `docs/` folder
- **Issues:** Create GitHub issue
- **Slack:** #infrastructure-team
- **Email:** infrastructure@vpbank.com

---

## ✅ Checklist for New Team Members

- [ ] Clone repository
- [ ] Install system dependencies (Python, Terraform, AWS CLI)
- [ ] Create virtual environment
- [ ] Install Python dependencies
- [ ] Configure `.env` with AWS keys
- [ ] Get Gemini API key
- [ ] Start backend successfully
- [ ] Access Swagger UI at http://localhost:8008/docs
- [ ] Deploy test stack
- [ ] Test scaling endpoints
- [ ] Read `API-DOCUMENTATION-FRONTEND.md`
- [ ] Join team Slack channel

---

**Ready to start!** 🎉

For any questions, refer to documentation or contact the team.


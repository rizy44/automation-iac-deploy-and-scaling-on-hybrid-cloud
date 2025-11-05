#!/bin/bash

# VPBank Hybrid Cloud Platform - Setup Script
# This script automates the initial setup for new collaborators

set -e  # Exit on error

echo "========================================"
echo "VPBank Infrastructure Platform Setup"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on supported OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
else
    echo -e "${RED}Unsupported OS: $OSTYPE${NC}"
    echo "This script supports Linux and macOS only"
    exit 1
fi

echo -e "${GREEN}Detected OS: $OS${NC}"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Python 3
echo "Checking Python 3..."
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"
else
    echo -e "${RED}✗ Python 3 not found${NC}"
    echo "Please install Python 3.10+ first:"
    if [ "$OS" == "linux" ]; then
        echo "  sudo apt-get install python3 python3-pip python3-venv"
    else
        echo "  brew install python"
    fi
    exit 1
fi

# Check Terraform
echo "Checking Terraform..."
if command_exists terraform; then
    TF_VERSION=$(terraform --version | head -n1 | cut -d'v' -f2)
    echo -e "${GREEN}✓ Terraform $TF_VERSION found${NC}"
else
    echo -e "${YELLOW}⚠ Terraform not found${NC}"
    echo "Installing Terraform..."
    if [ "$OS" == "linux" ]; then
        wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
        echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
        sudo apt-get update && sudo apt-get install terraform
    else
        brew tap hashicorp/tap
        brew install hashicorp/tap/terraform
    fi
    echo -e "${GREEN}✓ Terraform installed${NC}"
fi

# Check AWS CLI
echo "Checking AWS CLI..."
if command_exists aws; then
    AWS_VERSION=$(aws --version | cut -d' ' -f1 | cut -d'/' -f2)
    echo -e "${GREEN}✓ AWS CLI $AWS_VERSION found${NC}"
else
    echo -e "${YELLOW}⚠ AWS CLI not found${NC}"
    echo "Installing AWS CLI..."
    if [ "$OS" == "linux" ]; then
        curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
        unzip -q awscliv2.zip
        sudo ./aws/install
        rm -rf aws awscliv2.zip
    else
        brew install awscli
    fi
    echo -e "${GREEN}✓ AWS CLI installed${NC}"
fi

echo ""
echo "========================================"
echo "Setting up Python Virtual Environment"
echo "========================================"
echo ""

# Check if .venv already exists
if [ -d ".venv" ]; then
    echo -e "${YELLOW}⚠ Virtual environment already exists${NC}"
    read -p "Do you want to recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing old virtual environment..."
        rm -rf .venv
    else
        echo "Using existing virtual environment"
        VENV_EXISTS=1
    fi
fi

# Create virtual environment
if [ -z "$VENV_EXISTS" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip --quiet

# Install dependencies
echo "Installing Python dependencies..."
pip install -r backend/requirements.txt --quiet
echo -e "${GREEN}✓ Dependencies installed${NC}"

echo ""
echo "========================================"
echo "Configuring Environment"
echo "========================================"
echo ""

# Check if .env exists
if [ -f ".env" ]; then
    echo -e "${GREEN}✓ .env file already exists${NC}"
else
    echo "Creating .env file..."
    cat > .env <<EOF
# AWS Credentials (REQUIRED - Add your keys here!)
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here

# AWS Configuration
DEFAULT_REGION=ap-southeast-2
DEFAULT_AZ=ap-southeast-2a
DEFAULT_INSTANCE_TYPE=t3.medium

# Terraform
TF_BIN=$(which terraform)
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
    echo -e "${GREEN}✓ .env file created${NC}"
    echo -e "${YELLOW}⚠ IMPORTANT: Edit .env and add your AWS credentials!${NC}"
fi

# Create .infra/work directory
mkdir -p .infra/work
echo -e "${GREEN}✓ Workspace directory created${NC}"

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo -e "${GREEN}Next steps:${NC}"
echo ""
echo "1. Configure credentials:"
echo "   ${YELLOW}nano .env${NC}"
echo "   - Add your AWS_ACCESS_KEY_ID"
echo "   - Add your AWS_SECRET_ACCESS_KEY"
echo "   - Add your GEMINI_API_KEY (from https://makersuite.google.com/app/apikey)"
echo ""
echo "2. Activate virtual environment:"
echo "   ${YELLOW}source .venv/bin/activate${NC}"
echo ""
echo "3. Start backend:"
echo "   ${YELLOW}python -m uvicorn backend.app:app --host 0.0.0.0 --port 8008 --reload${NC}"
echo ""
echo "4. Open API docs in browser:"
echo "   ${YELLOW}http://localhost:8008/docs${NC}"
echo ""
echo "5. Read documentation:"
echo "   - ${YELLOW}SETUP-GUIDE.md${NC} - Full setup instructions"
echo "   - ${YELLOW}API-DOCUMENTATION-FRONTEND.md${NC} - API reference"
echo "   - ${YELLOW}SCALING-SETUP-GUIDE.md${NC} - Scaling features"
echo ""
echo "For troubleshooting, see SETUP-GUIDE.md"
echo ""
echo -e "${GREEN}Happy coding! 🚀${NC}"


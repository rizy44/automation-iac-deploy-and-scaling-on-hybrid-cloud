#!/bin/bash
################################################################################
# StrongSwan SD-WAN Edge Setup Script for OpenStack
# This script installs and configures StrongSwan IPsec for AWS VPN connection
################################################################################

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   log_error "This script must be run as root (use sudo)"
   exit 1
fi

log_info "Starting StrongSwan SD-WAN Edge setup..."

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    OS_VERSION=$VERSION_ID
else
    log_error "Cannot detect OS"
    exit 1
fi

log_info "Detected OS: $OS $OS_VERSION"

################################################################################
# Install StrongSwan
################################################################################
log_info "Installing StrongSwan and dependencies..."

if [[ "$OS" == "ubuntu" ]] || [[ "$OS" == "debian" ]]; then
    apt-get update -y
    apt-get install -y strongswan strongswan-pki libstrongswan-extra-plugins \
        strongswan-swanctl charon-systemd curl jq net-tools
elif [[ "$OS" == "centos" ]] || [[ "$OS" == "rhel" ]] || [[ "$OS" == "rocky" ]]; then
    yum install -y epel-release
    yum install -y strongswan curl jq net-tools
else
    log_error "Unsupported OS: $OS"
    exit 1
fi

log_info "StrongSwan installed successfully"

################################################################################
# Enable IP Forwarding
################################################################################
log_info "Enabling IP forwarding..."

cat > /etc/sysctl.d/99-ip-forward.conf <<EOF
net.ipv4.ip_forward = 1
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0
EOF

sysctl -p /etc/sysctl.d/99-ip-forward.conf

log_info "IP forwarding enabled"

################################################################################
# Configure iptables for NAT
################################################################################
log_info "Configuring iptables for NAT..."

# Get the primary network interface
PRIMARY_IF=$(ip route | grep default | awk '{print $5}' | head -1)
log_info "Primary network interface: $PRIMARY_IF"

# Enable NAT for OpenStack network
iptables -t nat -A POSTROUTING -s 172.10.0.0/16 -o $PRIMARY_IF -j MASQUERADE
iptables -A FORWARD -i $PRIMARY_IF -o $PRIMARY_IF -j ACCEPT

# Save iptables rules
if command -v iptables-save &> /dev/null; then
    if [[ "$OS" == "ubuntu" ]] || [[ "$OS" == "debian" ]]; then
        apt-get install -y iptables-persistent
        iptables-save > /etc/iptables/rules.v4
    else
        service iptables save || true
    fi
fi

log_info "iptables configured for NAT"

################################################################################
# Create VPN Configuration Template
################################################################################
log_info "Creating VPN configuration template..."

cat > /etc/ipsec.conf.template <<'EOF'
# StrongSwan configuration for AWS VPN
config setup
    charondebug="ike 2, knl 2, cfg 2, net 2, esp 2, dmn 2, mgr 2"
    uniqueids=no

# Tunnel 1
conn aws-tunnel1
    auto=start
    left=%defaultroute
    leftid=OPENSTACK_PUBLIC_IP
    leftsubnet=172.10.0.0/16
    right=AWS_TUNNEL1_ADDRESS
    rightsubnet=0.0.0.0/0
    ike=aes256-sha2_256-modp2048!
    esp=aes256-sha2_256-modp2048!
    keyexchange=ikev2
    ikelifetime=28800s
    lifetime=3600s
    rekeymargin=540s
    type=tunnel
    dpddelay=10s
    dpdtimeout=30s
    dpdaction=restart
    authby=secret
    mark=%unique

# Tunnel 2
conn aws-tunnel2
    auto=start
    left=%defaultroute
    leftid=OPENSTACK_PUBLIC_IP
    leftsubnet=172.10.0.0/16
    right=AWS_TUNNEL2_ADDRESS
    rightsubnet=0.0.0.0/0
    ike=aes256-sha2_256-modp2048!
    esp=aes256-sha2_256-modp2048!
    keyexchange=ikev2
    ikelifetime=28800s
    lifetime=3600s
    rekeymargin=540s
    type=tunnel
    dpddelay=10s
    dpdtimeout=30s
    dpdaction=restart
    authby=secret
    mark=%unique
EOF

cat > /etc/ipsec.secrets.template <<'EOF'
# VPN Pre-shared Keys
AWS_TUNNEL1_ADDRESS : PSK "VPN_PRESHARED_KEY"
AWS_TUNNEL2_ADDRESS : PSK "VPN_PRESHARED_KEY"
EOF

log_info "Configuration templates created"

################################################################################
# Instructions
################################################################################
cat <<'INSTRUCTIONS'

================================================================================
StrongSwan SD-WAN Edge Installation Complete!
================================================================================

NEXT STEPS:

1. Get VPN configuration from AWS:
   After deploying SD-WAN infrastructure via API, retrieve the VPN config:
   
   curl http://YOUR_BACKEND_IP:8008/sdwan/vpn-config/{stack_id}

2. Edit /etc/ipsec.conf:
   
   sudo nano /etc/ipsec.conf
   
   Replace the following placeholders:
   - OPENSTACK_PUBLIC_IP: Your OpenStack public IP
   - AWS_TUNNEL1_ADDRESS: From VPN config (tunnel1.address)
   - AWS_TUNNEL2_ADDRESS: From VPN config (tunnel2.address)

3. Edit /etc/ipsec.secrets:
   
   sudo nano /etc/ipsec.secrets
   
   Replace:
   - VPN_PRESHARED_KEY: From VPN config (tunnel1.preshared_key)
   - AWS_TUNNEL1_ADDRESS: Same as above
   - AWS_TUNNEL2_ADDRESS: Same as above

4. Start StrongSwan:
   
   sudo systemctl enable strongswan
   sudo systemctl restart strongswan

5. Check VPN status:
   
   sudo ipsec statusall
   
   You should see both tunnels established.

6. Test connectivity:
   
   # Ping an instance in AWS App VPC (e.g., 10.101.1.10)
   ping 10.101.1.10

7. Configure BGP (Optional for dynamic routing):
   
   Install FRRouting for BGP:
   sudo apt-get install -y frr
   
   Configure BGP peering with AWS (ASN 64512 ↔ 65000)

================================================================================
TROUBLESHOOTING:

View logs:
  sudo journalctl -u strongswan -f

Check tunnel status:
  sudo ipsec statusall

Restart VPN:
  sudo systemctl restart strongswan

Test IPsec:
  sudo ipsec up aws-tunnel1
  sudo ipsec up aws-tunnel2

================================================================================
INSTRUCTIONS

log_info "Setup complete! Follow the instructions above to complete configuration."


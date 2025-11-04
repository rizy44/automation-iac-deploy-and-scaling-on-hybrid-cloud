# OpenStack SD-WAN Edge Setup Guide

This guide explains how to setup StrongSwan IPsec gateway on OpenStack to connect with AWS via Site-to-Site VPN.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Architecture Overview](#architecture-overview)
3. [Step-by-Step Setup](#step-by-step-setup)
4. [Configuration](#configuration)
5. [Testing and Verification](#testing-and-verification)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### OpenStack Requirements

- Ubuntu 20.04/22.04 or CentOS 7/8 VM
- Minimum: 2 vCPU, 2GB RAM, 20GB disk
- **Public IP address** assigned to VM (floating IP)
- Security group allowing:
  - UDP 500 (IKE)
  - UDP 4500 (NAT-T)
  - ESP protocol (IP Protocol 50)
  - All traffic from/to AWS VPC CIDRs (10.101.0.0/16, 10.103.0.0/16)

### Network Configuration

- OpenStack internal network: `172.10.0.0/16`
- VM should be able to route traffic for the entire OpenStack network
- IP forwarding enabled
- No conflicting firewall rules

### Information Needed

From AWS deployment (via `/sdwan/vpn-config/{stack_id}` API):
- VPN Tunnel 1 public IP
- VPN Tunnel 2 public IP
- Pre-shared key
- BGP ASN (AWS: 64512, Customer: 65000)

---

## Architecture Overview

```
┌─────────────────────────────────────────────┐
│          OpenStack Datacenter               │
│          172.10.0.0/16                      │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │   SD-WAN Edge-A (StrongSwan)         │  │
│  │   - Public IP: 203.0.113.50          │  │
│  │   - Private IP: 172.10.1.10          │  │
│  │   - IPsec tunnels to AWS             │  │
│  │   - BGP peering                      │  │
│  └──────────────────────────────────────┘  │
│            │                                │
│  ┌─────────┴─────────┐                     │
│  │ OpenStack VMs     │                     │
│  │ 172.10.x.x        │                     │
│  └───────────────────┘                     │
└─────────────────────────────────────────────┘
            │
            │ IPsec Tunnels (2x)
            │ Internet or MPLS
            ↓
┌─────────────────────────────────────────────┐
│              AWS Cloud                      │
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │   Transit Gateway                    │  │
│  │   ASN: 64512                         │  │
│  └──────────────────────────────────────┘  │
│       │                  │                  │
│       ↓                  ↓                  │
│  ┌─────────┐      ┌──────────────┐         │
│  │App VPC  │      │Shared VPC    │         │
│  │10.101.../16    │10.103.../16  │         │
│  └─────────┘      └──────────────┘         │
└─────────────────────────────────────────────┘
```

---

## Step-by-Step Setup

### Step 1: Create OpenStack VM

Create a VM on OpenStack with the specifications mentioned in prerequisites.

```bash
# Example using OpenStack CLI
openstack server create \
  --flavor m1.medium \
  --image ubuntu-22.04 \
  --network openstack-internal \
  --key-name your-keypair \
  --security-group sdwan-edge \
  sdwan-edge-a
```

### Step 2: Assign Floating IP

```bash
# Allocate floating IP
openstack floating ip create external-network

# Assign to VM
openstack server add floating ip sdwan-edge-a 203.0.113.50
```

### Step 3: SSH to VM and Run Setup Script

```bash
# SSH to the VM
ssh ubuntu@203.0.113.50

# Download the setup script from your backend server
curl -O http://YOUR_BACKEND_IP:8008/scripts/strongswan-edge.sh

# Or if you have the repo
# scp backend/scripts/strongswan-edge.sh ubuntu@203.0.113.50:~/

# Make it executable and run
chmod +x strongswan-edge.sh
sudo ./strongswan-edge.sh
```

The script will:
- Install StrongSwan and dependencies
- Enable IP forwarding
- Configure iptables for NAT
- Create configuration templates

### Step 4: Deploy AWS Infrastructure

From your local machine or backend server:

```bash
curl -X POST http://YOUR_BACKEND_IP:8008/sdwan/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "name_prefix": "prod-sdwan",
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

Save the `stack_id` from response.

### Step 5: Get VPN Configuration

```bash
curl http://YOUR_BACKEND_IP:8008/sdwan/vpn-config/{stack_id} | jq
```

Example response:
```json
{
  "stack_id": "20251103120000-abc123",
  "tunnel1": {
    "address": "52.63.123.45",
    "inside_cidr": "169.254.10.0/30",
    "customer_inside_ip": "169.254.10.2",
    "aws_inside_ip": "169.254.10.1",
    "preshared_key": "SecureKey123..."
  },
  "tunnel2": {
    "address": "13.239.45.67",
    "inside_cidr": "169.254.10.4/30",
    "customer_inside_ip": "169.254.10.6",
    "aws_inside_ip": "169.254.10.5",
    "preshared_key": "SecureKey123..."
  },
  "bgp": {
    "aws_asn": 64512,
    "customer_asn": 65000
  },
  "routing": {
    "openstack_cidr": "172.10.0.0/16",
    "app_vpc_cidr": "10.101.0.0/16",
    "shared_vpc_cidr": "10.103.0.0/16"
  }
}
```

---

## Configuration

### Configure IPsec

Edit `/etc/ipsec.conf`:

```bash
sudo nano /etc/ipsec.conf
```

Replace placeholders with values from VPN config:

```conf
config setup
    charondebug="ike 2, knl 2, cfg 2"
    uniqueids=no

conn aws-tunnel1
    auto=start
    left=%defaultroute
    leftid=203.0.113.50
    leftsubnet=172.10.0.0/16
    right=52.63.123.45                    # tunnel1.address
    rightsubnet=0.0.0.0/0
    ike=aes256-sha2_256-modp2048!
    esp=aes256-sha2_256-modp2048!
    keyexchange=ikev2
    ikelifetime=28800s
    lifetime=3600s
    type=tunnel
    dpddelay=10s
    dpdtimeout=30s
    dpdaction=restart
    authby=secret

conn aws-tunnel2
    auto=start
    left=%defaultroute
    leftid=203.0.113.50
    leftsubnet=172.10.0.0/16
    right=13.239.45.67                    # tunnel2.address
    rightsubnet=0.0.0.0/0
    ike=aes256-sha2_256-modp2048!
    esp=aes256-sha2_256-modp2048!
    keyexchange=ikev2
    ikelifetime=28800s
    lifetime=3600s
    type=tunnel
    dpddelay=10s
    dpdtimeout=30s
    dpdaction=restart
    authby=secret
```

### Configure Pre-shared Keys

Edit `/etc/ipsec.secrets`:

```bash
sudo nano /etc/ipsec.secrets
```

```
52.63.123.45 : PSK "SecureKey123..."
13.239.45.67 : PSK "SecureKey123..."
```

**Important**: Use the same key for both tunnels if AWS generated the same key.

### Start StrongSwan

```bash
sudo systemctl enable strongswan
sudo systemctl restart strongswan
```

### Configure Static Routes (if not using BGP)

```bash
# Add routes to AWS VPCs
sudo ip route add 10.101.0.0/16 dev eth0 scope link
sudo ip route add 10.103.0.0/16 dev eth0 scope link

# Make persistent
echo "10.101.0.0/16 via 169.254.10.1 dev eth0" | sudo tee -a /etc/network/interfaces
echo "10.103.0.0/16 via 169.254.10.1 dev eth0" | sudo tee -a /etc/network/interfaces
```

---

## Testing and Verification

### Check Tunnel Status

```bash
sudo ipsec statusall
```

Expected output:
```
Security Associations (2 up, 0 connecting):
  aws-tunnel1[1]: ESTABLISHED 5 seconds ago
  aws-tunnel2[2]: ESTABLISHED 3 seconds ago
```

### Test Connectivity to AWS

```bash
# Ping an instance in App VPC (get IP from AWS console or API)
ping 10.101.1.10

# Test HTTP to ALB
curl http://ALB_DNS_NAME
```

### Monitor Logs

```bash
# Real-time logs
sudo journalctl -u strongswan -f

# Check for errors
sudo grep -i error /var/log/syslog
```

### Test from OpenStack VM

From another VM in OpenStack network:

```bash
# This VM should route through SD-WAN Edge
ping 10.101.1.10

# Access application via ALB
curl http://ALB_DNS_NAME
```

---

## Troubleshooting

### Tunnels Not Establishing

**Check 1: Security Groups**
```bash
# Verify UDP 500 and 4500 are allowed
sudo netstat -tulpn | grep -E ':(500|4500)'
```

**Check 2: Public IP**
```bash
# Confirm public IP matches what you configured
curl ifconfig.me
```

**Check 3: Logs**
```bash
sudo journalctl -u strongswan -n 100 --no-pager
```

### Tunnels Up But No Connectivity

**Check 1: IP Forwarding**
```bash
sysctl net.ipv4.ip_forward
# Should return: net.ipv4.ip_forward = 1
```

**Check 2: Routes**
```bash
ip route show
# Should see routes to 10.101.0.0/16 and 10.103.0.0/16
```

**Check 3: NAT**
```bash
sudo iptables -t nat -L -n -v
# Should see MASQUERADE rule for 172.10.0.0/16
```

### Packet Loss or High Latency

**Check MTU**
```bash
# IPsec adds overhead, may need to reduce MTU
sudo ip link set dev eth0 mtu 1400

# Test with ping
ping -M do -s 1400 10.101.1.10
```

### Restart VPN

```bash
sudo systemctl restart strongswan
sudo ipsec restart
```

### Manually Bring Up Tunnels

```bash
sudo ipsec up aws-tunnel1
sudo ipsec up aws-tunnel2
```

### Debug Mode

Edit `/etc/ipsec.conf` and increase debug level:
```conf
config setup
    charondebug="ike 4, knl 4, cfg 4, net 4, esp 4"
```

Then restart:
```bash
sudo systemctl restart strongswan
```

---

## Advanced: BGP Configuration (Optional)

For dynamic routing, configure BGP with FRRouting:

### Install FRRouting

```bash
sudo apt-get install -y frr
```

### Configure BGP

Edit `/etc/frr/bgpd.conf`:

```conf
router bgp 65000
  bgp router-id 172.10.1.10
  neighbor 169.254.10.1 remote-as 64512
  neighbor 169.254.10.5 remote-as 64512
  
  address-family ipv4 unicast
    network 172.10.0.0/16
    neighbor 169.254.10.1 activate
    neighbor 169.254.10.5 activate
  exit-address-family
```

Enable and start:

```bash
sudo systemctl enable frr
sudo systemctl restart frr
```

Check BGP status:

```bash
sudo vtysh -c "show bgp summary"
sudo vtysh -c "show ip route"
```

---

## Security Best Practices

1. **Firewall**: Only allow necessary ports (UDP 500, 4500, ESP)
2. **Key Management**: Store pre-shared keys securely, rotate periodically
3. **Monitoring**: Set up alerts for tunnel down events
4. **Updates**: Keep StrongSwan updated for security patches
5. **Backup**: Document configuration, have backup Edge-B for HA

---

## Next Steps

After successful setup:

1. Deploy applications on AWS App VPC
2. Test end-to-end connectivity from OpenStack to AWS
3. Configure monitoring and alerting
4. Document IP addressing and routing
5. Plan for high availability (second tunnel, backup edge)

For architecture details, see [SD-WAN Architecture Documentation](sdwan-architecture.md).


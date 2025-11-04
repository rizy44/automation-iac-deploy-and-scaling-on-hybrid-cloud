# SD-WAN Hybrid Cloud Architecture

## Executive Summary

This document describes the hybrid cloud architecture connecting OpenStack datacenter with AWS cloud using Site-to-Site VPN and AWS Transit Gateway. The solution provides secure, scalable connectivity for hybrid workloads.

---

## Architecture Diagram

```
┌───────────────────────────────────────────────────────────────────────────┐
│                         OPENSTACK DATACENTER                              │
│                         Network: 172.10.0.0/16                            │
│                                                                           │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    SD-WAN Edge-A (StrongSwan)                    │   │
│  │  ┌────────────────────────────────────────────────────────────┐ │   │
│  │  │  • Public IP: 203.0.113.50 (Floating IP)                   │ │   │
│  │  │  • Private IP: 172.10.1.10                                  │ │   │
│  │  │  • IPsec VPN Client                                         │ │   │
│  │  │  • BGP Speaker (ASN 65000)                                  │ │   │
│  │  │  • NAT Gateway for internal network                         │ │   │
│  │  └────────────────────────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                              │                                            │
│         ┌────────────────────┴────────────────────┐                      │
│         │                                          │                      │
│  ┌──────▼──────┐                           ┌──────▼──────┐              │
│  │ Compute VMs │                           │  Storage    │              │
│  │ 172.10.2.x  │                           │  172.10.3.x │              │
│  └─────────────┘                           └─────────────┘              │
└───────────────────────────────────────────────────────────────────────────┘
                              │
                              │  IPsec Tunnel 1: 52.63.123.45
                              │  IPsec Tunnel 2: 13.239.45.67
                              │  (Internet or MPLS)
                              │
                              ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                            AWS CLOUD                                      │
│                         Region: ap-southeast-2                            │
│                                                                           │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                     AWS TRANSIT GATEWAY                          │   │
│  │  ┌────────────────────────────────────────────────────────────┐ │   │
│  │  │  • Central routing hub                                      │ │   │
│  │  │  • ASN: 64512                                               │ │   │
│  │  │  • VPN attachments: 1 (to OpenStack)                        │ │   │
│  │  │  • VPC attachments: 2 (App VPC, Shared VPC)                │ │   │
│  │  │  • Route propagation: Enabled                               │ │   │
│  │  └────────────────────────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│            │                                    │                         │
│            │                                    │                         │
│  ┌─────────▼────────────┐          ┌───────────▼──────────────┐         │
│  │    APP VPC           │          │  SHARED SERVICES VPC     │         │
│  │  10.101.0.0/16       │          │  10.103.0.0/16           │         │
│  │                      │          │                          │         │
│  │  ┌────────────────┐  │          │  ┌────────────────────┐ │         │
│  │  │ Public Subnets │  │          │  │ Private Subnets    │ │         │
│  │  │ (Multi-AZ)     │  │          │  │ (Multi-AZ)         │ │         │
│  │  │                │  │          │  │                    │ │         │
│  │  │ ┌────────────┐ │  │          │  │ • Monitoring      │ │         │
│  │  │ │    ALB     │ │  │          │  │ • DNS Services    │ │         │
│  │  │ └──────┬─────┘ │  │          │  │ • Logging         │ │         │
│  │  └────────┼────────┘  │          │  └────────────────────┘ │         │
│  │           │            │          │                          │         │
│  │  ┌────────▼─────────┐ │          └──────────────────────────┘         │
│  │  │ Private Subnets  │ │                                                │
│  │  │ (Multi-AZ)       │ │                                                │
│  │  │                  │ │                                                │
│  │  │ ┌──────────────┐ │ │                                                │
│  │  │ │     ASG      │ │ │                                                │
│  │  │ │  (2-4 EC2)   │ │ │                                                │
│  │  │ │  t3.micro    │ │ │                                                │
│  │  │ └──────────────┘ │ │                                                │
│  │  │                  │ │                                                │
│  │  │ ┌──────────────┐ │ │                                                │
│  │  │ │ NAT Gateway  │ │ │                                                │
│  │  │ └──────────────┘ │ │                                                │
│  │  └──────────────────┘ │                                                │
│  └───────────────────────┘                                                │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
                              │
                              │  Internet Gateway
                              │
                              ▼
                         [ INTERNET ]
```

---

## Network Design

### IP Address Allocation

| Network Segment | CIDR Block | Purpose |
|----------------|------------|---------|
| OpenStack Datacenter | 172.10.0.0/16 | Private on-premise network |
| OpenStack Management | 172.10.1.0/24 | SD-WAN Edge, management |
| OpenStack Compute | 172.10.2.0/24 | Virtual machines |
| OpenStack Storage | 172.10.3.0/24 | Storage nodes |
| AWS App VPC | 10.101.0.0/16 | Application workloads |
| App Public Subnets | 10.101.0.0/20 | ALB, NAT Gateway |
| App Private Subnets | 10.101.16.0/20 | EC2 instances |
| AWS Shared VPC | 10.103.0.0/16 | Shared services |
| Shared Private Subnets | 10.103.0.0/20 | Monitoring, DNS, logging |
| VPN Tunnel 1 | 169.254.10.0/30 | BGP peering |
| VPN Tunnel 2 | 169.254.10.4/30 | BGP peering backup |

### Availability Zones

- **OpenStack**: Single datacenter with local HA
- **AWS**: Multi-AZ deployment (2-3 AZs)
  - `ap-southeast-2a`
  - `ap-southeast-2b`
  - `ap-southeast-2c` (optional)

---

## Component Details

### OpenStack Components

#### SD-WAN Edge-A
- **Role**: VPN gateway and router
- **Software**: Ubuntu 22.04 + StrongSwan
- **vCPU**: 2
- **RAM**: 2GB
- **Functions**:
  - IPsec VPN termination
  - BGP routing (ASN 65000)
  - NAT for internal network
  - Traffic inspection (optional)

#### Compute Resources
- OpenStack VMs running various workloads
- Access AWS services via SD-WAN Edge

### AWS Components

#### Transit Gateway
- **Purpose**: Central connectivity hub
- **ASN**: 64512 (AWS default)
- **Attachments**:
  - 1x VPN connection (to OpenStack)
  - 2x VPC attachments (App, Shared)
- **Cost**: ~$36/month + $36/month per attachment
- **Throughput**: Up to 50 Gbps per VPC attachment

#### Site-to-Site VPN
- **Type**: IPsec VPN with BGP
- **Tunnels**: 2 (active-active for HA)
- **Encryption**: AES-256-GCM
- **Authentication**: Pre-shared key
- **Cost**: ~$36/month
- **Throughput**: Up to 1.25 Gbps per tunnel

#### App VPC

**Public Subnets** (Multi-AZ):
- Application Load Balancer (ALB)
- NAT Gateways
- Bastion hosts (optional)

**Private Subnets** (Multi-AZ):
- Auto Scaling Group (2-4 instances)
- EC2 instance type: t3.micro
- Security groups restrict access
- User data: nginx installation

**Application Load Balancer**:
- Public-facing
- HTTP/HTTPS listeners
- Health checks to target group
- Cross-zone load balancing

**Auto Scaling Group**:
- Min: 2, Max: 4, Desired: 2
- Target tracking scaling
- Health checks: ELB + EC2
- Spread across AZs

#### Shared Services VPC

**Private Subnets** (Multi-AZ):
- Monitoring services (CloudWatch, Prometheus)
- DNS services (Route53 Resolver)
- Centralized logging
- Configuration management

**No Internet Gateway**:
- Fully private VPC
- Access via Transit Gateway only
- Egress through NAT in App VPC or dedicated Egress VPC

---

## Traffic Flows

### Scenario 1: OpenStack VM → AWS App (via ALB)

```
OpenStack VM (172.10.2.10)
    ↓ (gateway: 172.10.1.10)
SD-WAN Edge-A (172.10.1.10)
    ↓ (IPsec encrypted)
AWS VPN Endpoint (52.63.123.45)
    ↓
Transit Gateway
    ↓
App VPC
    ↓
ALB (10.101.1.5)
    ↓
EC2 Instance (10.101.16.10)
```

**Latency**: ~20-50ms (Internet VPN)  
**Bandwidth**: Up to 1.25 Gbps per tunnel

### Scenario 2: AWS App → OpenStack Storage

```
EC2 Instance (10.101.16.10)
    ↓
Transit Gateway
    ↓ (route to 172.10.0.0/16)
AWS VPN Endpoint
    ↓ (IPsec encrypted)
SD-WAN Edge-A
    ↓ (routing + NAT)
OpenStack Storage (172.10.3.20)
```

### Scenario 3: AWS App → Shared Services

```
EC2 Instance (10.101.16.10)
    ↓ (local routing via TGW attachment)
Transit Gateway
    ↓ (route to 10.103.0.0/16)
Shared Services VPC (10.103.x.x)
```

**Latency**: <1ms (within AWS)  
**Bandwidth**: Up to 50 Gbps

### Scenario 4: Internet User → AWS App

```
Internet User
    ↓ (HTTPS)
Internet Gateway
    ↓
ALB (10.101.1.5)
    ↓
EC2 Instance (10.101.16.10)
```

**Public access via ALB DNS name**

---

## Routing Configuration

### OpenStack SD-WAN Edge Routes

```bash
# Default route to Internet
default via 172.10.1.1 dev eth0

# Local OpenStack network
172.10.0.0/16 dev eth0 scope link

# AWS networks via VPN
10.101.0.0/16 via 169.254.10.1 dev vti1
10.103.0.0/16 via 169.254.10.1 dev vti1
```

### AWS Transit Gateway Route Tables

**Default Route Table**:
```
Destination         Target
172.10.0.0/16      VPN attachment
10.101.0.0/16      App VPC attachment
10.103.0.0/16      Shared VPC attachment
```

**Propagated from BGP**:
- OpenStack advertises 172.10.0.0/16 via BGP (ASN 65000)
- AWS propagates 10.101.0.0/16, 10.103.0.0/16 via BGP (ASN 64512)

### App VPC Route Tables

**Public Subnet Route Table**:
```
Destination         Target
10.101.0.0/16      local
172.10.0.0/16      Transit Gateway
0.0.0.0/0          Internet Gateway
```

**Private Subnet Route Table**:
```
Destination         Target
10.101.0.0/16      local
172.10.0.0/16      Transit Gateway
10.103.0.0/16      Transit Gateway
0.0.0.0/0          NAT Gateway
```

---

## Security Architecture

### Network Security

**OpenStack**:
- Security Groups: Allow UDP 500, 4500, ESP protocol
- Firewall: Only necessary ports open
- IPsec encryption: AES-256

**AWS**:
- Security Groups:
  - ALB: HTTP (80), HTTPS (443) from 0.0.0.0/0
  - EC2: HTTP (80) from ALB, SSH (22) from OpenStack
  - Shared: All traffic from App VPC
- Network ACLs: Default allow (stateless)
- VPC Flow Logs: Enabled for monitoring

### Encryption

- **In Transit**:
  - VPN: IPsec with AES-256-GCM
  - ALB: TLS 1.2+ (optional)
- **At Rest**:
  - EBS volumes: Encrypted (optional)
  - S3 buckets: SSE-S3 or SSE-KMS

### Access Control

- **AWS IAM**: Least privilege for API access
- **SSH Keys**: Managed via AWS Systems Manager
- **VPN Pre-shared Key**: Stored securely, rotated quarterly

---

## High Availability & Disaster Recovery

### Current HA Features

1. **Dual VPN Tunnels**: Active-active configuration
2. **Multi-AZ Deployment**: ALB and ASG across 2+ AZs
3. **Auto Scaling**: Automatic instance replacement
4. **Health Checks**: ALB and ASG health monitoring

### Single Points of Failure

1. **SD-WAN Edge-A**: Single gateway in OpenStack
2. **Internet Connection**: Single ISP

### Recommended Improvements

**Phase 2 Enhancements**:
1. Deploy SD-WAN Edge-B for redundancy
2. Add second internet connection (diverse ISP)
3. Implement Direct Connect for production traffic
4. Add Egress VPC for centralized internet breakout
5. Configure CloudWatch alarms and SNS notifications

### Disaster Recovery

**RTO/RPO Targets**:
- VPN failure: RTO <5 minutes (automatic failover)
- AZ failure: RTO <2 minutes (ALB + ASG)
- Region failure: RTO <1 hour (manual failover)

**Backup Strategy**:
- Regular Terraform state backups
- EC2 AMI snapshots
- OpenStack VM snapshots
- Configuration documentation

---

## Monitoring & Operations

### Key Metrics

**VPN Health**:
- Tunnel status (up/down)
- Bytes in/out
- Tunnel data in/out
- Tunnel state change count

**Application Performance**:
- ALB request count
- ALB target response time
- EC2 CPU/memory utilization
- ASG scaling activities

**Network Performance**:
- VPC flow logs
- Transit Gateway bytes in/out
- NAT Gateway bytes in/out

### Alerting

**Critical Alerts**:
- VPN tunnel down >5 minutes
- All EC2 instances unhealthy
- Transit Gateway attachment down

**Warning Alerts**:
- High VPN latency (>100ms)
- ASG scaling issues
- High NAT Gateway costs

### Cost Monitoring

**Monthly Cost Estimate** (~$175/month):
```
Transit Gateway:            $36
  - Hourly charge:          $36
  - Attachments (2):        $72
Site-to-Site VPN:           $36
EC2 (t3.micro x2):          $15
NAT Gateway:                $33
ALB:                        $16
Data Transfer:              $10-20
──────────────────────────────
Total:                      ~$175-185/month
```

---

## Performance Considerations

### Latency

| Path | Expected Latency |
|------|-----------------|
| OpenStack ↔ AWS (VPN) | 20-50ms |
| AWS App ↔ Shared VPC | <1ms |
| Internet ↔ AWS ALB | Variable |

### Bandwidth

| Component | Max Throughput |
|-----------|---------------|
| VPN per tunnel | 1.25 Gbps |
| VPN total (2 tunnels) | 2.5 Gbps |
| Transit Gateway per VPC | 50 Gbps |
| NAT Gateway | 45 Gbps |

### Scalability Limits

- **VPN Connections**: Up to 10 per Transit Gateway
- **Transit Gateway Attachments**: 5,000
- **Routes per Route Table**: 10,000 (with propagation)
- **EC2 Instances per ASG**: 1,000

---

## Deployment Process

### Prerequisites
1. AWS account with appropriate credits
2. OpenStack environment operational
3. Public IP for OpenStack Edge
4. Backend API server running

### Deployment Steps

1. **Prepare OpenStack**:
   - Create VM for SD-WAN Edge
   - Assign floating IP
   - Configure security groups

2. **Deploy AWS Infrastructure**:
   ```bash
   curl -X POST http://backend:8008/sdwan/deploy -d '{...}'
   ```

3. **Configure OpenStack Edge**:
   - Run strongswan-edge.sh script
   - Update /etc/ipsec.conf
   - Update /etc/ipsec.secrets
   - Start StrongSwan

4. **Verify Connectivity**:
   - Check VPN tunnel status
   - Test ping from OpenStack to AWS
   - Access ALB from OpenStack

5. **Deploy Applications**:
   - Update ASG user data
   - Deploy to App VPC
   - Configure monitoring

### Rollback Plan

If deployment fails:
1. Run `terraform destroy` or call `/sdwan/destroy/{stack_id}`
2. Remove OpenStack Edge configuration
3. Review logs and fix issues
4. Retry deployment

---

## Future Enhancements

### Phase 2 (Production Readiness)
- [ ] AWS Direct Connect for low latency
- [ ] Second SD-WAN Edge for HA
- [ ] Egress VPC for centralized internet
- [ ] CloudWatch dashboards and alarms
- [ ] Automated DR failover

### Phase 3 (Advanced Features)
- [ ] SD-WAN controller for policy-based routing
- [ ] Application-aware routing
- [ ] WAN optimization
- [ ] Integration with Service Mesh (Istio, Consul)
- [ ] Multi-region AWS deployment

---

## References

- [AWS Transit Gateway Documentation](https://docs.aws.amazon.com/vpc/latest/tgw/)
- [AWS Site-to-Site VPN Documentation](https://docs.aws.amazon.com/vpn/)
- [StrongSwan Documentation](https://docs.strongswan.org/)
- [OpenStack Networking Guide](https://docs.openstack.org/neutron/)

---

## Appendix

### Terraform Modules Used
- AWS VPC
- AWS Transit Gateway
- AWS VPN Connection
- AWS ALB and Target Groups
- AWS Auto Scaling Group

### Security Compliance
- Encryption in transit (IPsec)
- Network segmentation (VPCs)
- Least privilege access (Security Groups)
- Audit logging (VPC Flow Logs)

### Support Contacts
- AWS Support: Premium support recommended
- OpenStack Admin: Internal team
- Network Team: For ISP and connectivity issues


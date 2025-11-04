# API Reference - Hybrid Cloud Infrastructure

Base URL: `http://localhost:8008`

## Table of Contents

1. [SD-WAN Hybrid Cloud Endpoints](#sdwan-hybrid-cloud-endpoints)
2. [ELB/NLB Deployment Endpoints](#elb-nlb-deployment-endpoints)
3. [Legacy AWS Deployment Endpoints](#legacy-aws-deployment-endpoints)

---

## SD-WAN Hybrid Cloud Endpoints

### POST /sdwan/deploy

Deploy complete SD-WAN hybrid cloud architecture.

**Request Body:**
```json
{
  "name_prefix": "prod-sdwan",
  "region": "ap-southeast-2",
  "azs": ["ap-southeast-2a", "ap-southeast-2b"],
  "openstack_cidr": "172.10.0.0/16",
  "openstack_public_ip": "203.0.113.50",
  "vpn_preshared_key": "optional-will-be-generated",
  "app_vpc_cidr": "10.101.0.0/16",
  "shared_vpc_cidr": "10.103.0.0/16",
  "app_ami": "ami-0a25a306450a2cba3",
  "app_instance_type": "t3.micro",
  "app_min_size": 2,
  "app_max_size": 4,
  "app_desired_size": 2
}
```

**Response:**
```json
{
  "stack_id": "20251103120000-abc123",
  "phase": "APPLIED",
  "message": "SD-WAN architecture deployed successfully...",
  "outputs": {
    "transit_gateway_id": {"value": "tgw-abc123"},
    "vpn_connection_id": {"value": "vpn-xyz789"},
    "vpn_tunnel1_address": {"value": "52.63.123.45"},
    "vpn_tunnel2_address": {"value": "13.239.45.67"},
    "alb_dns_name": {"value": "my-alb-123.ap-southeast-2.elb.amazonaws.com"},
    "alb_url": {"value": "http://my-alb-123.ap-southeast-2.elb.amazonaws.com"}
  },
  "vpn_config_path": "/path/to/vpn-configuration.json"
}
```

**Status Codes:**
- `200`: Success
- `400`: Validation error
- `500`: Deployment failed

---

### GET /sdwan/vpn-config/{stack_id}

Retrieve VPN configuration for OpenStack Edge setup.

**Path Parameters:**
- `stack_id`: Stack ID from deployment

**Response:**
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
  },
  "configuration_file": "/path/to/vpn-configuration.txt"
}
```

**Status Codes:**
- `200`: Success
- `404`: Stack not found

---

### GET /sdwan/stacks

List all deployed SD-WAN stacks.

**Response:**
```json
[
  {
    "stack_id": "20251103120000-abc123",
    "has_vpn_config": true,
    "tunnel1_address": "52.63.123.45",
    "tunnel2_address": "13.239.45.67"
  },
  {
    "stack_id": "20251103110000-def456",
    "has_vpn_config": true,
    "tunnel1_address": "54.66.123.45",
    "tunnel2_address": "13.210.45.67"
  }
]
```

**Status Codes:**
- `200`: Success

---

### DELETE /sdwan/destroy/{stack_id}

Destroy SD-WAN infrastructure.

**Path Parameters:**
- `stack_id`: Stack ID to destroy

**Response:**
```json
{
  "stack_id": "20251103120000-abc123",
  "status": "destroyed",
  "message": "SD-WAN infrastructure has been destroyed successfully"
}
```

**Status Codes:**
- `200`: Success
- `404`: Stack not found
- `500`: Destroy failed

---

### GET /sdwan/health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "sdwan-hybrid-cloud",
  "version": "1.0.0"
}
```

**Status Codes:**
- `200`: Healthy

---

## ELB/NLB Deployment Endpoints

### POST /elb/deploy

Deploy single VPC with NLB and EC2 instances.

**Request Body:**
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

**Response:**
```json
{
  "stack_id": "20251103120000-xyz789",
  "phase": "APPLIED",
  "logs": {
    "init": "...",
    "apply": "...",
    "output": "..."
  },
  "outputs": {
    "instance_dns": {"value": ["ec2-1.compute.amazonaws.com", "ec2-2.compute.amazonaws.com"]},
    "instance_public_ip": {"value": ["54.66.1.1", "54.66.1.2"]},
    "nlb_dns_name": {"value": "bpp-nlb-123.elb.ap-southeast-2.amazonaws.com"}
  }
}
```

**Status Codes:**
- `200`: Success
- `400`: Validation error
- `500`: Deployment failed

---

## Legacy AWS Deployment Endpoints

### POST /aws/deploy

Legacy endpoint for simple VPC deployment.

**Request Body:**
```json
{
  "region": "ap-southeast-2",
  "az": "ap-southeast-2a",
  "vpc_cidr": "10.25.0.0/16",
  "subnet_cidr": "10.25.1.0/24",
  "instance_count": 2,
  "ami": "ami-0a25a306450a2cba3",
  "instance_type": "t3.micro",
  "key_name": "bpp-keypair",
  "user_data_path": "scripts/init.sh",
  "name_prefix": "test"
}
```

**Response:**
```json
{
  "workspace_id": "uuid-here",
  "outputs": {
    "instance_dns": ["..."],
    "instance_public_ip": ["..."],
    "nlb_dns_name": "..."
  }
}
```

---

### POST /aws/destroy

Destroy legacy deployment.

**Request Body:**
```json
{
  "workspace_id": "uuid-here"
}
```

**Response:**
```json
{
  "workspace_id": "uuid-here",
  "status": "destroyed"
}
```

---

## Common Error Responses

### Validation Error (400)
```json
{
  "detail": [
    {
      "loc": ["body", "openstack_public_ip"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### Deployment Failed (500)
```json
{
  "detail": {
    "phase": "FAILED_APPLY",
    "error": "Terraform apply failed",
    "logs": {
      "init": "...",
      "apply": "error details..."
    }
  }
}
```

### Stack Not Found (404)
```json
{
  "detail": "Stack 20251103120000-abc123 not found or VPN configuration unavailable"
}
```

---

## OpenAPI Documentation

Interactive API documentation is available at:

- **Swagger UI**: http://localhost:8008/docs
- **ReDoc**: http://localhost:8008/redoc
- **OpenAPI JSON**: http://localhost:8008/openapi.json

---

## Authentication

Currently, no authentication is required (development mode).

**Production recommendations:**
- Add API key authentication
- Implement OAuth2/JWT
- Rate limiting
- IP whitelisting

---

## Rate Limiting

No rate limiting in development mode.

**Production recommendations:**
- Max 10 deployments per hour per client
- Max 100 API calls per minute
- Implement exponential backoff

---

## Examples

### Deploy SD-WAN with curl

```bash
curl -X POST http://localhost:8008/sdwan/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "name_prefix": "prod",
    "region": "ap-southeast-2",
    "azs": ["ap-southeast-2a", "ap-southeast-2b"],
    "openstack_cidr": "172.10.0.0/16",
    "openstack_public_ip": "203.0.113.50",
    "app_ami": "ami-0a25a306450a2cba3"
  }'
```

### Get VPN Config with curl

```bash
curl http://localhost:8008/sdwan/vpn-config/20251103120000-abc123 | jq
```

### Deploy SD-WAN with Python

```python
import requests

payload = {
    "name_prefix": "prod",
    "region": "ap-southeast-2",
    "azs": ["ap-southeast-2a", "ap-southeast-2b"],
    "openstack_cidr": "172.10.0.0/16",
    "openstack_public_ip": "203.0.113.50",
    "app_ami": "ami-0a25a306450a2cba3",
    "app_instance_type": "t3.micro",
    "app_min_size": 2,
    "app_max_size": 4,
    "app_desired_size": 2
}

response = requests.post(
    "http://localhost:8008/sdwan/deploy",
    json=payload
)

result = response.json()
print(f"Stack ID: {result['stack_id']}")
print(f"ALB URL: {result['outputs']['alb_url']['value']}")
```

### Get VPN Config with Python

```python
import requests

stack_id = "20251103120000-abc123"
response = requests.get(f"http://localhost:8008/sdwan/vpn-config/{stack_id}")

config = response.json()
print(f"Tunnel 1: {config['tunnel1']['address']}")
print(f"Tunnel 2: {config['tunnel2']['address']}")
print(f"Pre-shared Key: {config['tunnel1']['preshared_key']}")
```

---

## Webhooks (Future Feature)

Not yet implemented. Planned features:

- `POST /webhooks/register`: Register webhook URL
- Events: `deployment.started`, `deployment.completed`, `deployment.failed`
- Payload: Stack details and status

---

## Support

For API issues:
- Check logs: `.infra/work/{stack_id}/`
- OpenAPI docs: http://localhost:8008/docs
- Documentation: `docs/` folder

---

## Version History

- **v1.0.0** (2025-11-03): Initial release
  - SD-WAN hybrid cloud endpoints
  - ELB/NLB deployment
  - Legacy AWS deployment
  - OpenAPI documentation


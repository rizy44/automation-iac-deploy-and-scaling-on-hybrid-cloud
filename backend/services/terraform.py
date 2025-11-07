import os
import json
import time
import uuid
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any, Optional

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from ..core.config import settings

TEMPLATE_AWS_MAIN = "main.tf.j2"

def new_stack_id() -> str:
    ts = time.strftime("%Y%m%d%H%M%S")
    return f"{ts}-{uuid.uuid4().hex[:8]}"

def render_tf(template_relpath: str, context: Dict[str, Any], out_dir: Path) -> Path:
    env = Environment(
        loader=FileSystemLoader(str(settings.TEMPLATE_DIR)),
        undefined=StrictUndefined,
        autoescape=False,
        keep_trailing_newline=True,
    )
    tpl = env.get_template(template_relpath)
    out_dir.mkdir(parents=True, exist_ok=True)
    main_tf = out_dir / "main.tf"
    main_tf.write_text(tpl.render(**context), encoding="utf-8")
    return main_tf

def write_user_data_if_inline(workdir: Path, user_data_inline: Optional[str]) -> str:
    if not user_data_inline:
        return ""
    p = workdir / "user_data.sh"
    p.write_text(user_data_inline, encoding="utf-8")
    return str(p)

def project_name_exists(name_prefix: str) -> bool:
    """
    Check if project (stack) with this name_prefix already exists
    
    Args:
        name_prefix: Project name to check
    
    Returns:
        True if project exists, False otherwise
    """
    tf_root = settings.TF_WORK_ROOT
    
    if not tf_root.exists():
        return False
    
    for stack_dir in tf_root.iterdir():
        if not stack_dir.is_dir():
            continue
        
        metadata_file = stack_dir / "deploy_metadata.json"
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    if metadata.get("context", {}).get("name_prefix") == name_prefix:
                        return True
            except Exception:
                pass
    
    return False


def build_aws_env(region: str) -> Dict[str, str]:
    # Chỉ dùng 2 biến từ .env
    if not (settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY):
        # Trả về lỗi rõ ràng nếu thiếu creds
        raise RuntimeError("Missing AWS creds in .env: AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY")

    return {
        "AWS_ACCESS_KEY_ID": settings.AWS_ACCESS_KEY_ID,
        "AWS_SECRET_ACCESS_KEY": settings.AWS_SECRET_ACCESS_KEY,
        "AWS_REGION": region or settings.DEFAULT_REGION,
    }

def run(cmd: list[str], cwd: Path, extra_env: Optional[Dict[str, str]] = None, timeout: Optional[int] = None):
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    try:
        return subprocess.run(
            cmd,
            cwd=str(cwd),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout or settings.TF_TIMEOUT_SEC,
        )
    except FileNotFoundError:
        suggested = shutil.which("terraform") or "/usr/bin/terraform"
        raise RuntimeError(
            f"Terraform binary not found at configured TF_BIN: {settings.TF_BIN}. "
            f"Set TF_BIN in your .env to the correct path (e.g., {suggested})."
        )

def tf_init_apply(workdir: Path, aws_env: Dict[str, str]) -> Dict[str, Any]:
    logs: Dict[str, str] = {}

    try:
        p = run([settings.TF_BIN, "init", "-input=false", "-upgrade"], cwd=workdir, extra_env=aws_env)
        logs["init"] = p.stdout + "\n" + p.stderr
        if p.returncode != 0:
            return {"phase": "FAILED_INIT", "logs": logs}

        p = run([settings.TF_BIN, "apply", "-auto-approve", "-input=false"], cwd=workdir, extra_env=aws_env)
        logs["apply"] = p.stdout + "\n" + p.stderr
        if p.returncode != 0:
            return {"phase": "FAILED_APPLY", "logs": logs}

        p = run([settings.TF_BIN, "output", "-json"], cwd=workdir, extra_env=aws_env)
        logs["output"] = p.stdout + "\n" + p.stderr
        outputs = {}
        try:
            outputs = json.loads(p.stdout) if p.returncode == 0 else {}
        except Exception:
            outputs = {}

        return {"phase": "APPLIED", "logs": logs, "outputs": outputs}
    except RuntimeError as e:
        return {"phase": "FAILED_INIT", "logs": logs, "error": str(e)}

def deploy_aws_from_template(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    payload KHÔNG chứa creds.
    Cần các tham số infra:
      region, vpc_cidr, subnet_cidr, az, name_prefix, key_name (deprecated, not used),
      instance_count, ami, instance_type, user_data_inline/user_data_path
      auto_install_monitoring (bool): tự cài Grafana+Mimir+Loki nếu không có user_data_inline
    
    Keypairs sẽ được tạo tự động: <name_prefix>-vm-1, <name_prefix>-vm-2, ...
    """
    name_prefix = payload.get("name_prefix", "")
    
    # Check if project name already exists
    if project_name_exists(name_prefix):
        return {
            "phase": "FAILED_INIT",
            "error": f"Project '{name_prefix}' already exists. Use a different name_prefix.",
            "stack_id": None
        }
    
    stack_id = new_stack_id()
    workdir = settings.TF_WORK_ROOT / stack_id
    workdir.mkdir(parents=True, exist_ok=True)

    # Script tự động cài full monitoring stack (Grafana + Mimir + Loki)
    monitoring_bootstrap = """#!/usr/bin/env bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

# 1) Cài Docker + Compose + Nginx
apt-get update -y
apt-get install -y docker.io docker-compose nginx
systemctl enable --now docker nginx

# 2) Thư mục triển khai
mkdir -p /opt/monitoring
cd /opt/monitoring

# 3) Tạo file cấu hình Loki
cat >/opt/monitoring/loki-config.yml <<'EOF'
auth_enabled: false
limits_config:
  allow_structured_metadata: false
common:
  ring:
    kvstore:
      store: inmemory
server:
  http_listen_port: 3100
ingester:
  wal:
    enabled: true
    dir: /loki/wal
compactor:
  working_directory: /loki/compactor
  shared_store: filesystem
storage_config:
  boltdb_shipper:
    active_index_directory: /loki/boltdb-shipper-active
    cache_location: /loki/boltdb-shipper-cache
  filesystem:
    directory: /loki/chunks
schema_config:
  configs:
    - from: 2020-10-24
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h
EOF

# 4) Tạo file cấu hình Mimir
cat >/opt/monitoring/mimir-config.yml <<'EOF'
multitenancy_enabled: false
server:
  log_level: info
  http_listen_port: 9009
  grpc_listen_port: 9095
distributor:
  ring:
    kvstore:
      store: inmemory
ingester:
  ring:
    replication_factor: 1
    kvstore:
      store: inmemory
blocks_storage:
  backend: filesystem
  filesystem:
    dir: /mimir-data/blocks
compactor:
  data_dir: /mimir-data/compactor
store_gateway:
  sharding_ring:
    replication_factor: 1
memberlist:
  join_members:
    - mimir
EOF

# 5) Setup Grafana Provisioning Folder
mkdir -p /etc/grafana/provisioning/datasources

# 5a) Tạo datasources.yml theo Grafana official format
cat >/etc/grafana/provisioning/datasources/datasources.yml <<'EOF'
apiVersion: 1

datasources:
  - name: Mimir
    type: prometheus
    url: http://mimir:9009/prometheus
    access: proxy
    isDefault: true
    editable: true
    jsonData:
      prometheusVersion: latest

  - name: Loki
    type: loki
    url: http://loki:3100
    access: proxy
    isDefault: false
    editable: true
EOF

# 5b) Tạo docker-compose.yml
cat >/opt/monitoring/docker-compose.yml <<'EOF'
version: "3.8"
services:
  grafana:
    image: grafana/grafana:10.4.0
    container_name: grafana
    restart: always
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana-data:/var/lib/grafana
      - /etc/grafana/provisioning/datasources:/etc/grafana/provisioning/datasources:ro

  loki:
    image: grafana/loki:2.9.6
    container_name: loki
    restart: always
    command: ["-config.file=/etc/loki/local-config.yml"]
    volumes:
      - /opt/monitoring/loki-config.yml:/etc/loki/local-config.yml
      - loki-data:/loki
    ports:
      - "3100:3100"

  mimir:
    image: grafana/mimir:2.13.0
    container_name: mimir
    restart: always
    command: ["-config.file=/etc/mimir/mimir-config.yml"]
    volumes:
      - /opt/monitoring/mimir-config.yml:/etc/mimir/mimir-config.yml
      - mimir-data:/mimir-data
    ports:
      - "9009:9009"
      - "9095:9095"

volumes:
  grafana-data:
  loki-data:
  mimir-data:
EOF

# 6) Khởi chạy stack
docker-compose -f /opt/monitoring/docker-compose.yml up -d

# 7) Nginx reverse proxy
cat >/etc/nginx/sites-available/monitoring <<'EOF'
server {
  listen 80;

  location / {
    proxy_pass http://127.0.0.1:3000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  }

  location /loki/ {
    proxy_pass http://127.0.0.1:3100/loki/;
    proxy_set_header Host $host;
  }

  location /mimir/ {
    proxy_pass http://127.0.0.1:9009/;
    proxy_set_header Host $host;
  }
}
EOF

ln -sf /etc/nginx/sites-available/monitoring /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

echo "✅ Monitoring stack ready!"
echo "   Grafana: http://localhost:3000 (admin/admin)"
echo "   Loki API: http://localhost:3100"
echo "   Mimir API: http://localhost:9009"
echo ""
echo "✅ Grafana Datasources auto-provisioned:"
echo "   - Mimir (Prometheus): http://mimir:9009/prometheus"
echo "   - Loki: http://loki:3100"
"""

    user_data_path = payload.get("user_data_path")
    user_data_inline = payload.get("user_data_inline")
    auto_install = bool(payload.get("auto_install_monitoring", False))

    if not user_data_path:
        if user_data_inline:
            user_data_path = write_user_data_if_inline(workdir, user_data_inline)
        elif auto_install:
            user_data_path = write_user_data_if_inline(workdir, monitoring_bootstrap)
        else:
            user_data_path = write_user_data_if_inline(workdir, "#!/usr/bin/env bash\n")

    region = payload.get("region", settings.DEFAULT_REGION)
    context = {
        "region":          region,
        "vpc_cidr":        payload["vpc_cidr"],
        "subnet_cidr":     payload["subnet_cidr"],
        "az":              payload["az"],
        "name_prefix":     payload["name_prefix"],
        "instance_count":  int(payload["instance_count"]),
        "ami":             payload["ami"],
        "instance_type":   payload.get("instance_type", settings.DEFAULT_INSTANCE_TYPE),
        "user_data_path":  user_data_path,
    }

    render_tf(TEMPLATE_AWS_MAIN, context, workdir)

    # Save deployment context for future scaling operations
    metadata = {
        "stack_id": stack_id,
        "deployed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "context": context,
        "region": region
    }
    metadata_file = workdir / "deploy_metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)

    try:
        aws_env = build_aws_env(region=region)
    except RuntimeError as e:
        return {"phase": "FAILED_CREDENTIALS", "error": str(e), "stack_id": stack_id}

    # Create keypairs for all instances before terraform apply
    from .keypair_manager import create_keypair_for_instance
    
    instance_count = int(payload["instance_count"])
    keypairs_created = {}
    keypairs_failed = []
    
    for i in range(1, instance_count + 1):
        result = create_keypair_for_instance(
            stack_id=stack_id,
            instance_index=i,
            name_prefix=name_prefix,
            region=region
        )
        if result.get("success"):
            keypairs_created[f"{name_prefix}-vm-{i}"] = {
                "key_name": result["key_name"],
                "key_id": result.get("key_id"),
                "pem_path": result["pem_path"]
            }
        else:
            keypairs_failed.append({
                "key_name": result.get("key_name"),
                "error": result.get("error")
            })
    
    # If any keypair creation failed, return error
    if keypairs_failed:
        return {
            "phase": "FAILED_KEYPAIR_CREATION",
            "error": f"Failed to create {len(keypairs_failed)} keypairs",
            "failed_keypairs": keypairs_failed,
            "stack_id": stack_id
        }

    res = tf_init_apply(workdir, aws_env)
    res["stack_id"] = stack_id
    res["keypairs_created"] = keypairs_created
    return res


def deploy_sdwan_architecture(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deploy SD-WAN hybrid cloud architecture with Transit Gateway and Site-to-Site VPN.
    
    payload should contain:
      - name_prefix: Resource naming prefix
      - region: AWS region
      - azs: List of availability zones (2-3)
      - openstack_cidr: OpenStack datacenter CIDR (e.g., "172.10.0.0/16")
      - openstack_public_ip: Public IP of OpenStack datacenter
      - vpn_preshared_key: Pre-shared key for VPN tunnels
      - app_vpc_cidr, shared_vpc_cidr: VPC CIDR blocks
      - app_ami, app_instance_type: EC2 configuration
      - app_min_size, app_max_size, app_desired_size: ASG configuration
    """
    stack_id = new_stack_id()
    workdir = settings.TF_WORK_ROOT / stack_id
    workdir.mkdir(parents=True, exist_ok=True)
    
    # Copy VPN config template to workdir
    vpn_tpl_src = settings.TEMPLATE_DIR / "vpn-config.tpl"
    vpn_tpl_dst = workdir / "vpn-config.tpl"
    if vpn_tpl_src.exists():
        vpn_tpl_dst.write_text(vpn_tpl_src.read_text())
    
    region = payload.get("region", settings.DEFAULT_REGION)
    
    # Build context for Jinja2 template
    context = {
        "name_prefix":         payload["name_prefix"],
        "region":              region,
        "azs":                 payload["azs"],
        "openstack_cidr":      payload["openstack_cidr"],
        "openstack_public_ip": payload["openstack_public_ip"],
        "vpn_preshared_key":   payload["vpn_preshared_key"],
        "app_vpc_cidr":        payload["app_vpc_cidr"],
        "shared_vpc_cidr":     payload["shared_vpc_cidr"],
        "app_ami":             payload["app_ami"],
        "app_instance_type":   payload["app_instance_type"],
        "app_min_size":        payload["app_min_size"],
        "app_max_size":        payload["app_max_size"],
        "app_desired_size":    payload["app_desired_size"],
    }
    
    # Render Terraform template
    render_tf("sdwan-hybrid.tf.j2", context, workdir)
    
    # Build AWS environment variables
    try:
        aws_env = build_aws_env(region=region)
    except RuntimeError as e:
        return {"phase": "FAILED_CREDENTIALS", "error": str(e), "stack_id": stack_id}
    
    # Run Terraform init and apply
    res = tf_init_apply(workdir, aws_env)
    res["stack_id"] = stack_id
    
    # If successful, add VPN config path
    if res.get("phase") == "APPLIED":
        vpn_config_path = workdir / "vpn-configuration.json"
        if vpn_config_path.exists():
            res["vpn_config_path"] = str(vpn_config_path)
    
    return res


def get_vpn_configuration(stack_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve VPN configuration for a deployed SD-WAN stack.
    
    Returns VPN tunnel details needed for OpenStack StrongSwan setup.
    """
    workdir = settings.TF_WORK_ROOT / stack_id
    
    if not workdir.exists():
        return None
    
    vpn_config_file = workdir / "vpn-configuration.json"
    vpn_text_file = workdir / "vpn-configuration.txt"
    
    if not vpn_config_file.exists():
        return None
    
    try:
        with open(vpn_config_file, 'r') as f:
            config = json.load(f)
        
        return {
            "stack_id": stack_id,
            "tunnel1": config.get("tunnel1", {}),
            "tunnel2": config.get("tunnel2", {}),
            "bgp": config.get("bgp", {}),
            "routing": config.get("routing", {}),
            "configuration_file": str(vpn_text_file) if vpn_text_file.exists() else ""
        }
    except Exception as e:
        print(f"Error reading VPN configuration: {e}")
        return None


def destroy_stack(stack_id: str) -> Dict[str, Any]:
    """
    Destroy Terraform stack (SD-WAN or regular infrastructure).
    
    Runs `terraform destroy` and removes the workspace directory.
    """
    workdir = settings.TF_WORK_ROOT / stack_id
    
    if not workdir.exists():
        return {"success": False, "error": f"Stack {stack_id} not found"}
    
    logs: Dict[str, str] = {}
    
    try:
        # Get AWS credentials from first available main.tf to determine region
        region = settings.DEFAULT_REGION
        aws_env = build_aws_env(region=region)
        
        # Run terraform destroy
        p = run(
            [settings.TF_BIN, "destroy", "-auto-approve", "-input=false"],
            cwd=workdir,
            extra_env=aws_env
        )
        
        logs["destroy"] = p.stdout + "\n" + p.stderr
        
        if p.returncode != 0:
            return {"success": False, "logs": logs, "error": "Terraform destroy failed"}
        
        # Remove workspace directory
        import shutil
        shutil.rmtree(workdir)
        
        return {"success": True, "logs": logs}
        
    except Exception as e:
        return {"success": False, "error": str(e), "logs": logs}

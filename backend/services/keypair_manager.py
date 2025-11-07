"""
Keypair Manager - Quản lý SSH keypairs per-instance

Mỗi EC2 instance sẽ có keypair riêng với tên: <name_prefix>-vm-<number>.pem
"""

import boto3
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from ..core.config import settings


def generate_rsa_keypair() -> tuple[str, str]:
    """
    Generate RSA 2048-bit keypair
    
    Returns:
        (private_key_pem, public_key_openssh)
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    
    # Private key in PEM format
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')
    
    # Public key in OpenSSH format
    public_key = private_key.public_key()
    public_openssh = public_key.public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH
    ).decode('utf-8')
    
    return private_pem, public_openssh


def create_keypair_for_instance(
    stack_id: str,
    instance_index: int,
    name_prefix: str,
    region: str
) -> Dict[str, Any]:
    """
    Tạo keypair riêng cho 1 instance
    
    Args:
        stack_id: "20251104213408-xxx"
        instance_index: 1, 2, 3, ...
        name_prefix: "my-app"
        region: "ap-southeast-2"
    
    Returns:
        {
            "success": True,
            "key_name": "my-app-vm-1",
            "key_id": "key-12345...",
            "pem_path": "/path/to/my-app-vm-1.pem"
        }
    """
    key_name = f"{name_prefix}-vm-{instance_index}"
    workdir = settings.TF_WORK_ROOT / stack_id
    private_key_dir = workdir / "private-key"
    private_key_dir.mkdir(parents=True, exist_ok=True)
    
    # Set directory permissions to 700
    private_key_dir.chmod(0o700)
    
    pem_path = private_key_dir / f"{key_name}.pem"
    
    try:
        # Generate keypair
        private_pem, public_openssh = generate_rsa_keypair()
        
        # Save private key to file
        pem_path.write_text(private_pem, encoding='utf-8')
        pem_path.chmod(0o600)
        
        # Import public key to AWS
        ec2 = boto3.client('ec2', region_name=region)
        
        # Check if key already exists and delete it
        try:
            existing_keys = ec2.describe_key_pairs(KeyNames=[key_name])
            if existing_keys['KeyPairs']:
                ec2.delete_key_pair(KeyName=key_name)
        except ec2.exceptions.ClientError:
            pass  # Key doesn't exist, that's fine
        
        # Create new key pair
        response = ec2.import_key_pair(
            KeyName=key_name,
            PublicKeyMaterial=public_openssh.encode('utf-8')
        )
        
        return {
            "success": True,
            "key_name": key_name,
            "key_id": response.get('KeyId'),
            "pem_path": str(pem_path),
            "fingerprint": response.get('KeyFingerprint')
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "key_name": key_name
        }


def delete_keypair_for_instance(
    stack_id: str,
    instance_index: int,
    name_prefix: str,
    region: str
) -> Dict[str, Any]:
    """
    Xóa keypair của 1 instance (khi scale down)
    """
    key_name = f"{name_prefix}-vm-{instance_index}"
    workdir = settings.TF_WORK_ROOT / stack_id
    pem_path = workdir / "private-key" / f"{key_name}.pem"
    
    deleted_file = False
    deleted_aws_key = False
    
    try:
        # Delete from AWS
        ec2 = boto3.client('ec2', region_name=region)
        try:
            ec2.delete_key_pair(KeyName=key_name)
            deleted_aws_key = True
        except ec2.exceptions.ClientError as e:
            if 'does not exist' not in str(e):
                raise
        
        # Delete local file
        if pem_path.exists():
            pem_path.unlink()
            deleted_file = True
        
        return {
            "success": True,
            "key_name": key_name,
            "deleted_aws_key": deleted_aws_key,
            "deleted_file": deleted_file,
            "pem_path": str(pem_path)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "key_name": key_name
        }


def list_instance_keypairs(stack_id: str, region: str) -> List[Dict]:
    """
    Lấy danh sách tất cả keypairs của stack
    """
    workdir = settings.TF_WORK_ROOT / stack_id
    private_key_dir = workdir / "private-key"
    
    keypairs = []
    
    if not private_key_dir.exists():
        return keypairs
    
    # List local .pem files
    for pem_file in private_key_dir.glob("*.pem"):
        key_name = pem_file.stem  # Remove .pem extension
        keypairs.append({
            "key_name": key_name,
            "pem_file": pem_file.name,
            "pem_path": str(pem_file),
            "file_exists": True,
            "file_size": pem_file.stat().st_size
        })
    
    return sorted(keypairs, key=lambda x: x['key_name'])


def get_instance_keypair(
    stack_id: str,
    instance_index: int,
    name_prefix: str
) -> Optional[Dict[str, Any]]:
    """
    Lấy thông tin keypair của instance
    """
    key_name = f"{name_prefix}-vm-{instance_index}"
    workdir = settings.TF_WORK_ROOT / stack_id
    pem_path = workdir / "private-key" / f"{key_name}.pem"
    
    if not pem_path.exists():
        return None
    
    return {
        "key_name": key_name,
        "pem_path": str(pem_path),
        "exists": True
    }


def read_private_key(pem_path: str) -> Optional[str]:
    """
    Read private key content from file
    
    Args:
        pem_path: Full path to .pem file
    
    Returns:
        Private key content or None if file doesn't exist
    """
    path = Path(pem_path)
    if path.exists():
        return path.read_text(encoding='utf-8')
    return None


def cleanup_keypairs(stack_id: str, region: str) -> Dict[str, Any]:
    """
    Cleanup all keypairs for a stack (when destroying)
    """
    workdir = settings.TF_WORK_ROOT / stack_id
    private_key_dir = workdir / "private-key"
    
    deleted_count = 0
    errors = []
    
    try:
        ec2 = boto3.client('ec2', region_name=region)
        
        if private_key_dir.exists():
            for pem_file in private_key_dir.glob("*.pem"):
                key_name = pem_file.stem
                
                # Delete from AWS
                try:
                    ec2.delete_key_pair(KeyName=key_name)
                except Exception as e:
                    errors.append(f"AWS delete error for {key_name}: {str(e)}")
                
                # Delete local file
                try:
                    pem_file.unlink()
                    deleted_count += 1
                except Exception as e:
                    errors.append(f"File delete error for {pem_file}: {str(e)}")
        
        return {
            "success": len(errors) == 0,
            "deleted_count": deleted_count,
            "errors": errors
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from .terraform import run, build_aws_env, render_tf, TEMPLATE_AWS_MAIN
from ..core.config import settings


def get_stack_info(stack_id: str) -> Dict[str, Any]:
    """
    Get current information about a deployed stack.
    
    Returns:
        Dict with stack_id, current_instance_count, instances, nlb_dns, metadata
    """
    workdir = settings.TF_WORK_ROOT / stack_id
    
    if not workdir.exists():
        raise ValueError(f"Stack {stack_id} not found")
    
    # Load metadata
    metadata_file = workdir / "deploy_metadata.json"
    if not metadata_file.exists():
        raise ValueError(f"Stack {stack_id} metadata not found")
    
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)
    
    # Get current outputs from Terraform
    region = metadata.get("region", settings.DEFAULT_REGION)
    aws_env = build_aws_env(region=region)
    
    try:
        p = run([settings.TF_BIN, "output", "-json"], cwd=workdir, extra_env=aws_env)
        outputs = json.loads(p.stdout) if p.returncode == 0 else {}
    except Exception as e:
        outputs = {}
    
    # Extract instance information
    instance_ips = outputs.get("instance_public_ip", {}).get("value", [])
    current_count = len(instance_ips) if instance_ips else metadata.get("context", {}).get("instance_count", 0)
    
    return {
        "stack_id": stack_id,
        "current_instance_count": current_count,
        "instances": instance_ips,
        "nlb_dns": outputs.get("nlb_dns_name", {}).get("value", ""),
        "deployed_at": metadata.get("deployed_at"),
        "region": metadata.get("region"),
        "metadata": metadata
    }


def list_active_stacks() -> List[Dict[str, Any]]:
    """
    Scan TF_WORK_ROOT for all valid stacks with metadata.
    
    Returns:
        List of stack info dicts
    """
    stacks = []
    
    if not settings.TF_WORK_ROOT.exists():
        return stacks
    
    for stack_dir in settings.TF_WORK_ROOT.iterdir():
        if not stack_dir.is_dir():
            continue
        
        metadata_file = stack_dir / "deploy_metadata.json"
        if not metadata_file.exists():
            continue
        
        try:
            stack_info = get_stack_info(stack_dir.name)
            stacks.append(stack_info)
        except Exception:
            # Skip invalid stacks
            continue
    
    return stacks


def scale_stack(stack_id: str, target_count: int, reason: Optional[str] = None) -> Dict[str, Any]:
    """
    Scale a stack to target_count instances by re-rendering Terraform and applying.
    
    Automatically manages keypairs:
    - Scale up: creates new keypairs for new instances
    - Scale down: deletes keypairs for removed instances
    
    Uses LIFO (Last In First Out) - Terraform terminates highest index instances first.
    
    Args:
        stack_id: Stack identifier
        target_count: Desired number of instances
        reason: Optional reason for scaling
    
    Returns:
        Dict with success status, old/new counts, logs
    """
    from .keypair_manager import create_keypair_for_instance, delete_keypair_for_instance
    
    workdir = settings.TF_WORK_ROOT / stack_id
    
    if not workdir.exists():
        raise ValueError(f"Stack {stack_id} not found")
    
    # Validate target count
    if target_count < settings.SCALE_DOWN_MIN_INSTANCES:
        raise ValueError(f"target_count must be >= {settings.SCALE_DOWN_MIN_INSTANCES}")
    
    if target_count > settings.SCALE_UP_MAX_INSTANCES:
        raise ValueError(f"target_count must be <= {settings.SCALE_UP_MAX_INSTANCES}")
    
    # Load metadata
    metadata_file = workdir / "deploy_metadata.json"
    if not metadata_file.exists():
        raise ValueError(f"Stack {stack_id} metadata not found")
    
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)
    
    # Get current and new counts
    context = metadata["context"]
    old_count = context.get("instance_count", 1)
    name_prefix = context.get("name_prefix", "")
    region = metadata.get("region", settings.DEFAULT_REGION)
    
    if old_count == target_count:
        return {
            "success": True,
            "stack_id": stack_id,
            "old_count": old_count,
            "new_count": target_count,
            "reason": reason,
            "action": "no_change",
            "message": "Instance count already at target"
        }
    
    # Manage keypairs
    keypairs_added = []
    keypairs_deleted = []
    keypair_errors = []
    
    # Scale up: create keypairs for new instances
    if target_count > old_count:
        for i in range(old_count + 1, target_count + 1):
            result = create_keypair_for_instance(
                stack_id=stack_id,
                instance_index=i,
                name_prefix=name_prefix,
                region=region
            )
            if result.get("success"):
                keypairs_added.append(result["key_name"])
            else:
                keypair_errors.append(f"Failed to create {result.get('key_name')}: {result.get('error')}")
    
    # Scale down: delete keypairs for removed instances
    elif target_count < old_count:
        for i in range(target_count + 1, old_count + 1):
            result = delete_keypair_for_instance(
                stack_id=stack_id,
                instance_index=i,
                name_prefix=name_prefix,
                region=region
            )
            if result.get("success"):
                keypairs_deleted.append(result["key_name"])
            else:
                keypair_errors.append(f"Failed to delete {result.get('key_name')}: {result.get('error')}")
    
    # If there were keypair errors, return error (don't proceed with terraform)
    if keypair_errors:
        return {
            "success": False,
            "stack_id": stack_id,
            "old_count": old_count,
            "target_count": target_count,
            "error": "Failed to manage keypairs",
            "keypair_errors": keypair_errors
        }
    
    # Update context with new instance count
    context["instance_count"] = target_count
    
    # Re-render main.tf with new count
    render_tf(TEMPLATE_AWS_MAIN, context, workdir)
    
    # Apply Terraform
    aws_env = build_aws_env(region=region)
    
    logs = {}
    try:
        p = run([settings.TF_BIN, "apply", "-auto-approve", "-input=false"], 
                cwd=workdir, extra_env=aws_env)
        logs["apply"] = p.stdout + "\n" + p.stderr
        
        if p.returncode != 0:
            return {
                "success": False,
                "error": "Terraform apply failed",
                "logs": logs,
                "stack_id": stack_id,
                "old_count": old_count,
                "target_count": target_count,
                "keypairs_added": keypairs_added,
                "keypairs_deleted": keypairs_deleted
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "logs": logs,
            "stack_id": stack_id,
            "old_count": old_count,
            "target_count": target_count,
            "keypairs_added": keypairs_added,
            "keypairs_deleted": keypairs_deleted
        }
    
    # Update metadata with new context and scaling history
    import time
    metadata["context"] = context
    metadata["last_scaled_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    metadata["last_scale_reason"] = reason
    
    # Track scaling history
    if "scaling_history" not in metadata:
        metadata["scaling_history"] = []
    
    metadata["scaling_history"].append({
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "old_count": old_count,
        "new_count": target_count,
        "action": "scale_up" if target_count > old_count else "scale_down",
        "reason": reason,
        "keypairs_added": keypairs_added,
        "keypairs_deleted": keypairs_deleted
    })
    
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    action = "scale_up" if target_count > old_count else "scale_down"
    
    return {
        "success": True,
        "stack_id": stack_id,
        "old_count": old_count,
        "new_count": target_count,
        "reason": reason,
        "action": action,
        "logs": logs,
        "keypairs_added": keypairs_added,
        "keypairs_deleted": keypairs_deleted,
        "message": f"Successfully scaled from {old_count} to {target_count} instances"
    }



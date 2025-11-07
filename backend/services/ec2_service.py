import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from .scaling_service import get_stack_info
from ..core.config import settings


def get_instance_details(stack_id: str) -> List[Dict[str, Any]]:
    """
    Get detailed information about all instances in a stack.
    
    Returns:
        List of instance details with id, ip, dns, status
    """
    stack_info = get_stack_info(stack_id)
    workdir = settings.TF_WORK_ROOT / stack_id
    
    # Load metadata for region
    metadata_file = workdir / "deploy_metadata.json"
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)
    
    region = metadata.get("region", settings.DEFAULT_REGION)
    
    # Get Terraform outputs
    from .terraform import run, build_aws_env
    aws_env = build_aws_env(region=region)
    
    try:
        p = run([settings.TF_BIN, "output", "-json"], cwd=workdir, extra_env=aws_env)
        outputs = json.loads(p.stdout) if p.returncode == 0 else {}
    except Exception:
        outputs = {}
    
    instance_ids = outputs.get("instance_ids", {}).get("value", [])
    instance_ips = outputs.get("instance_public_ip", {}).get("value", [])
    instance_dns = outputs.get("instance_dns", {}).get("value", [])
    
    instances = []
    for i, instance_id in enumerate(instance_ids):
        instance_data = {
            "instance_id": instance_id,
            "public_ip": instance_ips[i] if i < len(instance_ips) else None,
            "public_dns": instance_dns[i] if i < len(instance_dns) else None,
            "index": i,
            "name": f"{metadata['context']['name_prefix']}-{i + 1}"
        }
        
        # Get current status from AWS
        try:
            status = get_instance_status(instance_id, region)
            instance_data["status"] = status
        except Exception:
            instance_data["status"] = "unknown"
        
        instances.append(instance_data)
    
    return instances


def get_instance_status(instance_id: str, region: str) -> str:
    """
    Get the current status of an EC2 instance.
    
    Returns:
        Instance state (running, stopped, stopping, starting, etc.)
    """
    try:
        cmd = [
            "aws", "ec2", "describe-instances",
            "--instance-ids", instance_id,
            "--region", region,
            "--query", "Reservations[0].Instances[0].State.Name",
            "--output", "text"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return "error"
    except Exception:
        return "unknown"


def start_instance(instance_id: str, region: str) -> Dict[str, Any]:
    """
    Start an EC2 instance.
    
    Returns:
        Dict with success status and details
    """
    try:
        cmd = [
            "aws", "ec2", "start-instances",
            "--instance-ids", instance_id,
            "--region", region
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            response_data = json.loads(result.stdout)
            starting_instances = response_data.get("StartingInstances", [])
            
            if starting_instances:
                instance = starting_instances[0]
                return {
                    "success": True,
                    "instance_id": instance_id,
                    "action": "start",
                    "current_state": instance.get("CurrentState", {}).get("Name", "unknown"),
                    "previous_state": instance.get("PreviousState", {}).get("Name", "unknown"),
                    "message": f"Instance {instance_id} start initiated"
                }
        
        return {
            "success": False,
            "instance_id": instance_id,
            "action": "start",
            "error": result.stderr or "Unknown error",
            "message": f"Failed to start instance {instance_id}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "instance_id": instance_id,
            "action": "start",
            "error": str(e),
            "message": f"Exception while starting instance {instance_id}"
        }


def stop_instance(instance_id: str, region: str) -> Dict[str, Any]:
    """
    Stop an EC2 instance.
    
    Returns:
        Dict with success status and details
    """
    try:
        cmd = [
            "aws", "ec2", "stop-instances",
            "--instance-ids", instance_id,
            "--region", region
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            response_data = json.loads(result.stdout)
            stopping_instances = response_data.get("StoppingInstances", [])
            
            if stopping_instances:
                instance = stopping_instances[0]
                return {
                    "success": True,
                    "instance_id": instance_id,
                    "action": "stop",
                    "current_state": instance.get("CurrentState", {}).get("Name", "unknown"),
                    "previous_state": instance.get("PreviousState", {}).get("Name", "unknown"),
                    "message": f"Instance {instance_id} stop initiated"
                }
        
        return {
            "success": False,
            "instance_id": instance_id,
            "action": "stop",
            "error": result.stderr or "Unknown error",
            "message": f"Failed to stop instance {instance_id}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "instance_id": instance_id,
            "action": "stop",
            "error": str(e),
            "message": f"Exception while stopping instance {instance_id}"
        }


def reboot_instance(instance_id: str, region: str) -> Dict[str, Any]:
    """
    Reboot an EC2 instance.
    
    Returns:
        Dict with success status and details
    """
    try:
        cmd = [
            "aws", "ec2", "reboot-instances",
            "--instance-ids", instance_id,
            "--region", region
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            return {
                "success": True,
                "instance_id": instance_id,
                "action": "reboot",
                "message": f"Instance {instance_id} reboot initiated"
            }
        
        return {
            "success": False,
            "instance_id": instance_id,
            "action": "reboot",
            "error": result.stderr or "Unknown error",
            "message": f"Failed to reboot instance {instance_id}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "instance_id": instance_id,
            "action": "reboot",
            "error": str(e),
            "message": f"Exception while rebooting instance {instance_id}"
        }


def batch_instance_action(stack_id: str, action: str, instance_indices: Optional[List[int]] = None) -> Dict[str, Any]:
    """
    Perform an action on multiple instances in a stack.
    
    Args:
        stack_id: Stack identifier
        action: Action to perform (start, stop, reboot)
        instance_indices: List of instance indices (0-based). If None, applies to all instances.
    
    Returns:
        Dict with batch operation results
    """
    if action not in ["start", "stop", "reboot"]:
        return {
            "success": False,
            "error": f"Invalid action: {action}. Must be one of: start, stop, reboot"
        }
    
    try:
        instances = get_instance_details(stack_id)
        
        # Filter instances if specific indices provided
        if instance_indices is not None:
            instances = [inst for inst in instances if inst["index"] in instance_indices]
        
        if not instances:
            return {
                "success": False,
                "error": "No instances found to perform action on"
            }
        
        # Load metadata for region
        workdir = settings.TF_WORK_ROOT / stack_id
        metadata_file = workdir / "deploy_metadata.json"
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        region = metadata.get("region", settings.DEFAULT_REGION)
        
        # Perform action on each instance
        results = []
        for instance in instances:
            instance_id = instance["instance_id"]
            
            if action == "start":
                result = start_instance(instance_id, region)
            elif action == "stop":
                result = stop_instance(instance_id, region)
            elif action == "reboot":
                result = reboot_instance(instance_id, region)
            
            result["instance_name"] = instance["name"]
            result["instance_index"] = instance["index"]
            results.append(result)
        
        # Summary
        successful = sum(1 for r in results if r["success"])
        total = len(results)
        
        return {
            "success": successful == total,
            "stack_id": stack_id,
            "action": action,
            "total_instances": total,
            "successful_operations": successful,
            "failed_operations": total - successful,
            "results": results,
            "message": f"Batch {action}: {successful}/{total} instances processed successfully"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Exception during batch {action} operation"
        }


from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from ..services.ec2_service import (
    get_instance_details,
    get_instance_status,
    start_instance,
    stop_instance,
    reboot_instance,
    batch_instance_action
)
from ..services.scaling_service import get_stack_info

router = APIRouter(prefix="/ec2", tags=["EC2 Instance Control"])


class InstanceActionRequest(BaseModel):
    instance_id: str
    region: Optional[str] = None


class BatchActionRequest(BaseModel):
    stack_id: str
    action: str  # start, stop, reboot
    instance_indices: Optional[List[int]] = None  # If None, applies to all instances


@router.get("/stack/{stack_id}/instances")
async def list_stack_instances(stack_id: str) -> Dict[str, Any]:
    """
    Get detailed information about all instances in a stack.
    
    Returns instance IDs, IPs, DNS names, and current status.
    """
    try:
        instances = get_instance_details(stack_id)
        stack_info = get_stack_info(stack_id)
        
        return {
            "success": True,
            "stack_id": stack_id,
            "total_instances": len(instances),
            "instances": instances,
            "stack_info": {
                "nlb_dns": stack_info.get("nlb_dns"),
                "deployed_at": stack_info.get("deployed_at"),
                "region": stack_info.get("region")
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving instances: {str(e)}")


@router.get("/instance/{instance_id}/status")
async def get_instance_status_endpoint(instance_id: str, region: str = "ap-southeast-2") -> Dict[str, Any]:
    """
    Get the current status of a specific EC2 instance.
    """
    try:
        status = get_instance_status(instance_id, region)
        
        return {
            "success": True,
            "instance_id": instance_id,
            "region": region,
            "status": status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting instance status: {str(e)}")


@router.post("/instance/start")
async def start_instance_endpoint(request: InstanceActionRequest) -> Dict[str, Any]:
    """
    Start a specific EC2 instance.
    """
    try:
        region = request.region or "ap-southeast-2"
        result = start_instance(request.instance_id, region)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to start instance"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting instance: {str(e)}")


@router.post("/instance/stop")
async def stop_instance_endpoint(request: InstanceActionRequest) -> Dict[str, Any]:
    """
    Stop a specific EC2 instance.
    """
    try:
        region = request.region or "ap-southeast-2"
        result = stop_instance(request.instance_id, region)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to stop instance"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error stopping instance: {str(e)}")


@router.post("/instance/reboot")
async def reboot_instance_endpoint(request: InstanceActionRequest) -> Dict[str, Any]:
    """
    Reboot a specific EC2 instance.
    """
    try:
        region = request.region or "ap-southeast-2"
        result = reboot_instance(request.instance_id, region)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to reboot instance"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rebooting instance: {str(e)}")


@router.post("/stack/batch-action")
async def batch_instance_action_endpoint(request: BatchActionRequest) -> Dict[str, Any]:
    """
    Perform an action on multiple instances in a stack.
    
    Actions: start, stop, reboot
    If instance_indices is not provided, applies to all instances in the stack.
    """
    try:
        result = batch_instance_action(
            stack_id=request.stack_id,
            action=request.action,
            instance_indices=request.instance_indices
        )
        
        if not result["success"] and "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error performing batch action: {str(e)}")


@router.post("/stack/{stack_id}/start")
async def start_all_instances_in_stack(stack_id: str) -> Dict[str, Any]:
    """
    Start all instances in a stack.
    """
    try:
        result = batch_instance_action(stack_id, "start")
        
        if not result["success"] and "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting stack instances: {str(e)}")


@router.post("/stack/{stack_id}/stop")
async def stop_all_instances_in_stack(stack_id: str) -> Dict[str, Any]:
    """
    Stop all instances in a stack.
    """
    try:
        result = batch_instance_action(stack_id, "stop")
        
        if not result["success"] and "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error stopping stack instances: {str(e)}")


@router.post("/stack/{stack_id}/reboot")
async def reboot_all_instances_in_stack(stack_id: str) -> Dict[str, Any]:
    """
    Reboot all instances in a stack.
    """
    try:
        result = batch_instance_action(stack_id, "reboot")
        
        if not result["success"] and "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rebooting stack instances: {str(e)}")


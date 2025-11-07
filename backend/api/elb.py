from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from ..services.terraform import deploy_aws_from_template
from ..services.scaling_service import get_stack_info, list_active_stacks

router = APIRouter(prefix="/elb", tags=["elb"])

class DeployReq(BaseModel):
    region: str
    vpc_cidr: str
    subnet_cidr: str
    az: str
    name_prefix: str
    instance_count: int = Field(ge=1)
    ami: str
    instance_type: str
    user_data_inline: str | None = None
    user_data_path: str | None = None
    auto_install_monitoring: bool = True

@router.post("/deploy")
def deploy(req: DeployReq):
    """
    Deploy AWS infrastructure (VPC, EC2, NLB) with per-instance SSH keypairs.
    
    Per-instance keypairs will be created automatically:
    - <name_prefix>-vm-1, <name_prefix>-vm-2, etc.
    - Stored in: .infra/work/<stack_id>/private-key/
    
    Returns stack_id and instance details
    """
    result = deploy_aws_from_template(req.model_dump())
    
    if result.get("phase") in ["FAILED_CREDENTIALS", "FAILED_INIT", "FAILED_KEYPAIR_CREATION"]:
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    if result.get("phase") == "FAILED_APPLY":
        raise HTTPException(status_code=500, detail="Infrastructure deployment failed")
    
    return result


@router.get("/projects")
def list_projects():
    """
    List all deployed projects (stacks)
    """
    try:
        stacks = list_active_stacks()
        return {
            "success": True,
            "total_projects": len(stacks),
            "projects": stacks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{stack_id}")
def get_project(stack_id: str):
    """
    Get detailed information about a specific project
    """
    try:
        stack_info = get_stack_info(stack_id)
        return {
            "success": True,
            "project": stack_info
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

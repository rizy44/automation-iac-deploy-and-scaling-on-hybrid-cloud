from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, IPvAnyAddress
from typing import List, Optional
import secrets
import string
from ..services.terraform import deploy_sdwan_architecture, get_vpn_configuration

router = APIRouter(prefix="/sdwan", tags=["sdwan"])


class SDWANDeployRequest(BaseModel):
    """Request model for deploying SD-WAN hybrid cloud architecture"""
    
    # Basic configuration
    name_prefix: str = Field(
        description="Prefix for all resource names",
        example="sdwan-prod"
    )
    region: str = Field(
        default="ap-southeast-2",
        description="AWS region to deploy resources"
    )
    azs: List[str] = Field(
        min_length=2,
        max_length=3,
        description="List of availability zones",
        example=["ap-southeast-2a", "ap-southeast-2b"]
    )
    
    # OpenStack configuration
    openstack_cidr: str = Field(
        default="172.10.0.0/16",
        description="CIDR block of OpenStack datacenter network"
    )
    openstack_public_ip: str = Field(
        description="Public IP address of OpenStack datacenter (for VPN endpoint)",
        example="203.0.113.50"
    )
    
    # VPN configuration
    vpn_preshared_key: Optional[str] = Field(
        default=None,
        description="Pre-shared key for VPN tunnels (auto-generated if not provided)",
        min_length=20
    )
    
    # VPC CIDR blocks
    app_vpc_cidr: str = Field(
        default="10.101.0.0/16",
        description="CIDR block for Application VPC"
    )
    shared_vpc_cidr: str = Field(
        default="10.103.0.0/16",
        description="CIDR block for Shared Services VPC"
    )
    
    # Application configuration
    app_ami: str = Field(
        default="ami-0a25a306450a2cba3",
        description="AMI ID for application instances"
    )
    app_instance_type: str = Field(
        default="t3.micro",
        description="Instance type for application servers"
    )
    app_min_size: int = Field(
        default=2,
        ge=1,
        le=10,
        description="Minimum number of instances in Auto Scaling Group"
    )
    app_max_size: int = Field(
        default=4,
        ge=1,
        le=20,
        description="Maximum number of instances in Auto Scaling Group"
    )
    app_desired_size: int = Field(
        default=2,
        ge=1,
        le=10,
        description="Desired number of instances in Auto Scaling Group"
    )
    
    def generate_vpn_key(self) -> str:
        """Generate a secure random pre-shared key"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(32))
    
    class Config:
        json_schema_extra = {
            "example": {
                "name_prefix": "sdwan-demo",
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
            }
        }


class SDWANDeployResponse(BaseModel):
    """Response model for SD-WAN deployment"""
    stack_id: str
    phase: str
    message: str
    outputs: Optional[dict] = None
    vpn_config_path: Optional[str] = None


class VPNConfigurationResponse(BaseModel):
    """Response model for VPN configuration details"""
    stack_id: str
    tunnel1: dict
    tunnel2: dict
    bgp: dict
    routing: dict
    configuration_file: str


@router.post("/deploy", response_model=SDWANDeployResponse)
def deploy_sdwan(req: SDWANDeployRequest):
    """
    Deploy complete SD-WAN hybrid cloud architecture
    
    This endpoint creates:
    - AWS Transit Gateway (central routing hub)
    - Site-to-Site VPN connection to OpenStack
    - App VPC with ALB and Auto Scaling Group
    - Shared Services VPC for common resources
    - All necessary networking (subnets, route tables, security groups)
    
    Returns stack_id and VPN configuration for OpenStack setup.
    """
    try:
        # Generate VPN key if not provided
        if not req.vpn_preshared_key:
            req.vpn_preshared_key = req.generate_vpn_key()
        
        # Validate configurations
        if req.app_desired_size < req.app_min_size or req.app_desired_size > req.app_max_size:
            raise HTTPException(
                status_code=400,
                detail=f"app_desired_size must be between app_min_size and app_max_size"
            )
        
        # Deploy infrastructure
        result = deploy_sdwan_architecture(req.model_dump())
        
        # Handle deployment failures
        if result.get("phase") in ["FAILED_CREDENTIALS", "FAILED_INIT", "FAILED_APPLY"]:
            raise HTTPException(
                status_code=500,
                detail={
                    "phase": result["phase"],
                    "error": result.get("error", "Deployment failed"),
                    "logs": result.get("logs", {})
                }
            )
        
        # Success response
        return SDWANDeployResponse(
            stack_id=result["stack_id"],
            phase=result["phase"],
            message="SD-WAN architecture deployed successfully. Use /sdwan/vpn-config/{stack_id} to get OpenStack configuration.",
            outputs=result.get("outputs", {}),
            vpn_config_path=result.get("vpn_config_path")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during deployment: {str(e)}"
        )


@router.get("/vpn-config/{stack_id}", response_model=VPNConfigurationResponse)
def get_vpn_config(stack_id: str):
    """
    Retrieve VPN configuration for a deployed stack
    
    Returns detailed VPN tunnel configuration needed to setup
    StrongSwan on OpenStack SD-WAN Edge.
    """
    try:
        config = get_vpn_configuration(stack_id)
        
        if not config:
            raise HTTPException(
                status_code=404,
                detail=f"Stack {stack_id} not found or VPN configuration unavailable"
            )
        
        return VPNConfigurationResponse(**config)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving VPN configuration: {str(e)}"
        )


@router.get("/stacks", response_model=List[dict])
def list_stacks():
    """
    List all deployed SD-WAN stacks
    
    Returns a list of stack IDs and their basic information.
    """
    try:
        from ..core.config import settings
        from pathlib import Path
        import json
        
        stacks = []
        work_root = settings.TF_WORK_ROOT
        
        if not work_root.exists():
            return []
        
        for stack_dir in work_root.iterdir():
            if stack_dir.is_dir():
                vpn_config_file = stack_dir / "vpn-configuration.json"
                if vpn_config_file.exists():
                    try:
                        with open(vpn_config_file) as f:
                            config = json.load(f)
                        stacks.append({
                            "stack_id": stack_dir.name,
                            "has_vpn_config": True,
                            "tunnel1_address": config.get("tunnel1", {}).get("address"),
                            "tunnel2_address": config.get("tunnel2", {}).get("address")
                        })
                    except:
                        stacks.append({
                            "stack_id": stack_dir.name,
                            "has_vpn_config": False
                        })
        
        return stacks
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing stacks: {str(e)}"
        )


@router.delete("/destroy/{stack_id}")
def destroy_sdwan(stack_id: str):
    """
    Destroy SD-WAN infrastructure for a given stack
    
    WARNING: This will delete all resources including VPN connections,
    Transit Gateway, VPCs, and all instances. This action cannot be undone.
    """
    try:
        from ..services.terraform import destroy_stack
        
        result = destroy_stack(stack_id)
        
        if result.get("success"):
            return {
                "stack_id": stack_id,
                "status": "destroyed",
                "message": "SD-WAN infrastructure has been destroyed successfully"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Failed to destroy stack",
                    "logs": result.get("logs", {})
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error destroying stack: {str(e)}"
        )


@router.get("/health")
def health_check():
    """Health check endpoint for SD-WAN service"""
    return {
        "status": "healthy",
        "service": "sdwan-hybrid-cloud",
        "version": "1.0.0"
    }


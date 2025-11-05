from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from ..services.terraform import deploy_aws_from_template

router = APIRouter(prefix="/elb", tags=["elb"])

class DeployReq(BaseModel):
    region: str
    vpc_cidr: str
    subnet_cidr: str
    az: str
    name_prefix: str
    key_name: str
    instance_count: int = Field(ge=1)
    ami: str
    instance_type: str
    user_data_inline: str | None = None
    user_data_path: str | None = None
    auto_install_monitoring: bool = True  # NEW: tự cài Grafana+Mimir+Loki nếu không có user_data_inline

@router.post("/deploy")
def deploy(req: DeployReq):
    # Không nhận creds qua API nữa – tất cả lấy từ .env
    result = deploy_aws_from_template(req.model_dump())
    if result.get("phase") == "FAILED_CREDENTIALS":
        raise HTTPException(status_code=500, detail=result["error"])
    return result

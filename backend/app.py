from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from uuid import uuid4
from pathlib import Path
import subprocess, json
from jinja2 import Environment, FileSystemLoader
from backend.api.elb import router as elb_router

app = FastAPI()
app.include_router(elb_router)
ROOT = Path(__file__).parent.resolve()
TEMPLATES_DIR = ROOT / "templates"
SCRIPTS_DIR = ROOT / "scripts"
WORKSPACES_DIR = ROOT / "workspaces"
WORKSPACES_DIR.mkdir(exist_ok=True)

env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=False)
tpl = env.get_template("main.tf.j2")

class DeployRequest(BaseModel):
    region: str = "ap-southeast-2"
    az: str = "ap-southeast-2a"
    vpc_cidr: str = "10.25.0.0/16"
    subnet_cidr: str = "10.25.1.0/24"
    instance_count: int = Field(ge=1, le=50)
    ami: str = "ami-0a25a306450a2cba3"
    instance_type: str = "t3.micro"
    key_name: str = "bpp-keypair"
    user_data_path: str = "scripts/init.sh"
    name_prefix: str = "u1t-h1gh-3go"

class DestroyRequest(BaseModel):
    workspace_id: str

def run(cmd: list[str], cwd: Path):
    p = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    if p.returncode != 0:
        raise HTTPException(status_code=500, detail=f"Command failed: {' '.join(cmd)}\nSTDOUT:\n{p.stdout}\nSTDERR:\n{p.stderr}")
    return p.stdout

@app.post("/aws/deploy")
def deploy(req: DeployRequest):
    # Tạo workspace
    ws_id = str(uuid4())
    ws_dir = WORKSPACES_DIR / ws_id
    ws_dir.mkdir()

    # Copy script init.sh
    (ws_dir / "scripts").mkdir()
    (ws_dir / "scripts" / "init.sh").write_text((SCRIPTS_DIR / "init.sh").read_text())
    
    # Render template -> main.tf
    rendered = tpl.render(
        region=req.region,
        az=req.az,
        vpc_cidr=req.vpc_cidr,
        subnet_cidr=req.subnet_cidr,
        instance_count=req.instance_count,
        ami=req.ami,
        instance_type=req.instance_type,
        key_name=req.key_name,
        user_data_path=req.user_data_path,
        name_prefix=req.name_prefix,
    )
    (ws_dir / "main.tf").write_text(rendered)

    # Terraform init & apply
    run(["terraform", "init", "-input=false"], cwd=ws_dir)
    run(["terraform", "apply", "-auto-approve", "-input=false"], cwd=ws_dir)

    # Lấy outputs
    out = run(["terraform", "output", "-json"], cwd=ws_dir)
    outputs = json.loads(out)

    return {
        "workspace_id": ws_id,
        "outputs": {
            "instance_dns": outputs.get("instance_dns", {}).get("value", []),
            "instance_public_ip": outputs.get("instance_public_ip", {}).get("value", []),
            "nlb_dns_name": outputs.get("nlb_dns_name", {}).get("value", ""),
        }
    }

@app.post("/aws/destroy")
def destroy(req: DestroyRequest):
    ws_dir = WORKSPACES_DIR / req.workspace_id
    if not ws_dir.exists():
        raise HTTPException(status_code=404, detail="workspace_id not found")

    run(["terraform", "destroy", "-auto-approve", "-input=false"], cwd=ws_dir)
    return {"workspace_id": req.workspace_id, "status": "destroyed"}

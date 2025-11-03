import os
import json
import time
import uuid
import subprocess
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
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout or settings.TF_TIMEOUT_SEC,
    )

def tf_init_apply(workdir: Path, aws_env: Dict[str, str]) -> Dict[str, Any]:
    logs: Dict[str, str] = {}

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

def deploy_aws_from_template(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    payload KHÔNG chứa creds.
    Cần các tham số infra:
      region, vpc_cidr, subnet_cidr, az, name_prefix, key_name,
      instance_count, ami, instance_type, user_data_inline/user_data_path
    """
    stack_id = new_stack_id()
    workdir = settings.TF_WORK_ROOT / stack_id
    workdir.mkdir(parents=True, exist_ok=True)

    user_data_path = payload.get("user_data_path")
    if not user_data_path and payload.get("user_data_inline"):
        user_data_path = write_user_data_if_inline(workdir, payload["user_data_inline"])
    if not user_data_path:
        user_data_path = write_user_data_if_inline(workdir, "#!/usr/bin/env bash\n")

    region = payload.get("region", settings.DEFAULT_REGION)
    context = {
        "region":          region,
        "vpc_cidr":        payload["vpc_cidr"],
        "subnet_cidr":     payload["subnet_cidr"],
        "az":              payload["az"],
        "name_prefix":     payload["name_prefix"],
        "key_name":        payload["key_name"],
        "instance_count":  int(payload["instance_count"]),
        "ami":             payload["ami"],
        "instance_type":   payload.get("instance_type", settings.DEFAULT_INSTANCE_TYPE),
        "user_data_path":  user_data_path,
    }

    render_tf(TEMPLATE_AWS_MAIN, context, workdir)

    try:
        aws_env = build_aws_env(region=region)
    except RuntimeError as e:
        return {"phase": "FAILED_CREDENTIALS", "error": str(e), "stack_id": stack_id}

    res = tf_init_apply(workdir, aws_env)
    res["stack_id"] = stack_id
    return res

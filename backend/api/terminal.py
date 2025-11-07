"""
Terminal API - WebSocket-based SSH terminal endpoints

Provides REST endpoints for managing SSH terminal sessions to EC2 instances
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional
import uuid
import asyncio
from ..services.terminal_service import terminal_manager
from ..services.scaling_service import get_stack_info
from ..services.keypair_manager import get_instance_keypair
from ..core.config import settings

router = APIRouter(prefix="/terminal", tags=["terminal"])


class TerminalConnectRequest(BaseModel):
    """Request to establish SSH terminal session"""
    stack_id: str
    instance_index: int
    username: str = "ubuntu"  # Default for Ubuntu AMI


class TerminalCommandRequest(BaseModel):
    """Request to send command through terminal"""
    session_id: str
    command: str


class TerminalResizeRequest(BaseModel):
    """Request to resize terminal"""
    session_id: str
    width: int
    height: int


@router.post("/connect")
def connect_terminal(req: TerminalConnectRequest):
    """
    Establish SSH terminal session to an EC2 instance
    
    Returns session_id to use for WebSocket connection
    
    Args:
        stack_id: Project/stack ID
        instance_index: Instance number (1, 2, 3, ...)
        username: SSH username (default: ubuntu)
    
    Returns:
        {
            "success": True,
            "session_id": "uuid",
            "ssh_command": "ssh -i key.pem ubuntu@ip"
        }
    """
    try:
        # Get stack info
        stack_info = get_stack_info(req.stack_id)
        if not stack_info:
            raise HTTPException(status_code=404, detail="Stack not found")
        
        name_prefix = stack_info["metadata"]["context"]["name_prefix"]
        region = stack_info["region"]
        
        # Get instance public IP
        instances = stack_info.get("instances", [])
        if req.instance_index < 1 or req.instance_index > len(instances):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid instance index. Available: 1-{len(instances)}"
            )
        
        public_ip = instances[req.instance_index - 1]
        
        # Get private key path
        keypair_info = get_instance_keypair(
            req.stack_id,
            req.instance_index,
            name_prefix
        )
        
        if not keypair_info:
            raise HTTPException(
                status_code=404,
                detail=f"Keypair not found for instance {req.instance_index}"
            )
        
        # Create unique session ID
        session_id = str(uuid.uuid4())
        
        # Create SSH session
        result = terminal_manager.create_session(
            session_id=session_id,
            hostname=public_ip,
            username=req.username,
            private_key_path=keypair_info["pem_path"]
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))
        
        return {
            "success": True,
            "session_id": session_id,
            "instance_ip": public_ip,
            "instance_name": f"{name_prefix}-vm-{req.instance_index}",
            "username": req.username,
            "ssh_command": f"ssh -i {keypair_info['pem_path']} {req.username}@{public_ip}"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws/{session_id}")
async def websocket_terminal(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for interactive terminal session
    
    Protocol:
    - Client sends: {"type": "command", "data": "command text"}
    - Client sends: {"type": "resize", "width": 120, "height": 30}
    - Server sends: {"type": "output", "data": "terminal output"}
    - Server sends: {"type": "error", "message": "error message"}
    - Server sends: {"type": "closed", "message": "session closed"}
    """
    await websocket.accept()
    
    try:
        # Verify session exists
        session = terminal_manager.sessions.get(session_id)
        if not session:
            await websocket.send_json({
                "type": "error",
                "message": "Session not found"
            })
            await websocket.close(code=4004)
            return
        
        # Start output reader task
        async def read_output():
            while True:
                output = terminal_manager.read_output(session_id)
                if output:
                    await websocket.send_json({
                        "type": "output",
                        "data": output
                    })
                await asyncio.sleep(0.1)
        
        # Start reading output in background
        read_task = asyncio.create_task(read_output())
        
        try:
            # Handle incoming messages
            while True:
                data = await websocket.receive_json()
                msg_type = data.get("type")
                
                if msg_type == "command":
                    command = data.get("data", "")
                    result = terminal_manager.send_command(session_id, command)
                    if not result.get("success"):
                        await websocket.send_json({
                            "type": "error",
                            "message": result.get("error")
                        })
                
                elif msg_type == "resize":
                    width = data.get("width", 120)
                    height = data.get("height", 30)
                    result = terminal_manager.resize_terminal(session_id, width, height)
                    if not result.get("success"):
                        await websocket.send_json({
                            "type": "error",
                            "message": result.get("error")
                        })
                
                elif msg_type == "disconnect":
                    break
        
        except WebSocketDisconnect:
            pass
        finally:
            read_task.cancel()
    
    except Exception as e:
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass
    
    finally:
        # Clean up session
        terminal_manager.close_session(session_id)
        await websocket.close()


@router.post("/disconnect")
def disconnect_terminal(req: TerminalCommandRequest):
    """
    Manually close a terminal session
    """
    try:
        result = terminal_manager.close_session(req.session_id)
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error"))
        
        return {
            "success": True,
            "message": f"Session {req.session_id} closed"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
def list_terminal_sessions():
    """
    List all active terminal sessions
    """
    try:
        sessions_info = terminal_manager.list_sessions()
        return {
            "success": True,
            **sessions_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup")
def cleanup_terminal_sessions():
    """
    Remove all inactive terminal sessions
    """
    try:
        cleaned_count = terminal_manager.cleanup_inactive_sessions()
        return {
            "success": True,
            "cleaned_sessions": cleaned_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


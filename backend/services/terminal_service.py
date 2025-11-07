"""
Terminal Service - WebSocket-based SSH terminal for EC2 instances

Provides SSH terminal access to EC2 instances through WebSocket connections
using xterm.js on the frontend and paramiko on the backend.
"""

import paramiko
import threading
import time
from typing import Optional, Dict, Any
from pathlib import Path
from ..core.config import settings


class SSHSession:
    """Manages a single SSH connection to an EC2 instance"""
    
    def __init__(self, 
                 hostname: str,
                 username: str,
                 private_key_path: str,
                 port: int = 22,
                 timeout: int = 30):
        """
        Initialize SSH session
        
        Args:
            hostname: EC2 instance public IP or DNS
            username: SSH username (e.g., 'ubuntu')
            private_key_path: Path to private key file
            port: SSH port (default 22)
            timeout: Connection timeout in seconds
        """
        self.hostname = hostname
        self.username = username
        self.private_key_path = private_key_path
        self.port = port
        self.timeout = timeout
        self.client = None
        self.channel = None
        self.is_connected = False
    
    def connect(self) -> Dict[str, Any]:
        """
        Establish SSH connection
        
        Returns:
            {
                "success": True/False,
                "error": error message if failed
            }
        """
        try:
            # Verify private key file exists
            key_file = Path(self.private_key_path)
            if not key_file.exists():
                return {
                    "success": False,
                    "error": f"Private key file not found: {self.private_key_path}"
                }
            
            # Create SSH client
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Load private key
            private_key = paramiko.RSAKey.from_private_key_file(
                self.private_key_path
            )
            
            # Connect to EC2
            self.client.connect(
                hostname=self.hostname,
                username=self.username,
                pkey=private_key,
                port=self.port,
                timeout=self.timeout,
                look_for_keys=False,
                allow_agent=False
            )
            
            # Open interactive shell channel
            self.channel = self.client.invoke_shell(
                term='xterm-256color',
                width=120,
                height=30
            )
            self.channel.setblocking(False)
            
            self.is_connected = True
            return {"success": True}
        
        except paramiko.AuthenticationException as e:
            return {
                "success": False,
                "error": f"Authentication failed: {str(e)}"
            }
        except paramiko.SSHException as e:
            return {
                "success": False,
                "error": f"SSH error: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Connection error: {str(e)}"
            }
    
    def send_command(self, command: str) -> Dict[str, Any]:
        """
        Send command through SSH channel
        
        Args:
            command: Command to send
        
        Returns:
            {"success": True/False, "error": error message if failed}
        """
        if not self.is_connected or not self.channel:
            return {"success": False, "error": "Not connected"}
        
        try:
            self.channel.send(command)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def read_output(self, max_size: int = 4096) -> Optional[str]:
        """
        Read available output from SSH channel
        
        Args:
            max_size: Maximum bytes to read
        
        Returns:
            Output string or None if no data
        """
        if not self.is_connected or not self.channel:
            return None
        
        try:
            if self.channel.recv_ready():
                return self.channel.recv(max_size).decode('utf-8', errors='ignore')
        except Exception:
            pass
        
        return None
    
    def resize_terminal(self, width: int, height: int) -> Dict[str, Any]:
        """
        Resize terminal size
        
        Args:
            width: Terminal width in columns
            height: Terminal height in lines
        
        Returns:
            {"success": True/False}
        """
        if not self.is_connected or not self.channel:
            return {"success": False, "error": "Not connected"}
        
        try:
            self.channel.resize_pty(width=width, height=height)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def disconnect(self) -> Dict[str, Any]:
        """
        Close SSH connection
        
        Returns:
            {"success": True}
        """
        try:
            if self.channel:
                self.channel.close()
            if self.client:
                self.client.close()
            self.is_connected = False
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def is_active(self) -> bool:
        """Check if session is still active"""
        return self.is_connected and self.channel and not self.channel.exit_status_ready()


class TerminalSessionManager:
    """Manages multiple SSH terminal sessions"""
    
    def __init__(self):
        self.sessions: Dict[str, SSHSession] = {}
        self.lock = threading.Lock()
    
    def create_session(self,
                       session_id: str,
                       hostname: str,
                       username: str,
                       private_key_path: str) -> Dict[str, Any]:
        """
        Create and connect a new SSH session
        
        Returns:
            {"success": True/False, "session_id": str, "error": error message}
        """
        with self.lock:
            # Check if session already exists
            if session_id in self.sessions:
                return {
                    "success": False,
                    "error": f"Session {session_id} already exists"
                }
            
            # Create new session
            session = SSHSession(
                hostname=hostname,
                username=username,
                private_key_path=private_key_path
            )
            
            # Connect
            result = session.connect()
            if not result.get("success"):
                return result
            
            # Store session
            self.sessions[session_id] = session
            return {
                "success": True,
                "session_id": session_id
            }
    
    def send_command(self, session_id: str, command: str) -> Dict[str, Any]:
        """Send command to a session"""
        session = self.sessions.get(session_id)
        if not session:
            return {"success": False, "error": f"Session {session_id} not found"}
        
        return session.send_command(command)
    
    def read_output(self, session_id: str) -> Optional[str]:
        """Read output from a session"""
        session = self.sessions.get(session_id)
        if not session:
            return None
        
        return session.read_output()
    
    def resize_terminal(self, session_id: str, width: int, height: int) -> Dict[str, Any]:
        """Resize terminal of a session"""
        session = self.sessions.get(session_id)
        if not session:
            return {"success": False, "error": f"Session {session_id} not found"}
        
        return session.resize_terminal(width, height)
    
    def close_session(self, session_id: str) -> Dict[str, Any]:
        """Close a session"""
        with self.lock:
            session = self.sessions.pop(session_id, None)
            if not session:
                return {"success": False, "error": f"Session {session_id} not found"}
            
            return session.disconnect()
    
    def list_sessions(self) -> Dict[str, Any]:
        """List all active sessions"""
        with self.lock:
            sessions_info = []
            for session_id, session in self.sessions.items():
                sessions_info.append({
                    "session_id": session_id,
                    "hostname": session.hostname,
                    "username": session.username,
                    "is_active": session.is_active()
                })
            
            return {
                "total_sessions": len(sessions_info),
                "sessions": sessions_info
            }
    
    def cleanup_inactive_sessions(self) -> int:
        """Remove inactive sessions"""
        with self.lock:
            inactive_sessions = [
                sid for sid, session in self.sessions.items()
                if not session.is_active()
            ]
            
            for session_id in inactive_sessions:
                self.sessions[session_id].disconnect()
                del self.sessions[session_id]
            
            return len(inactive_sessions)


# Global session manager instance
terminal_manager = TerminalSessionManager()


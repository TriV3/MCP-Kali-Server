#!/usr/bin/env python3

# This script connect the MCP AI agent to Kali Linux terminal and API Server.

# some of the code here was inspired from https://github.com/whit3rabbit0/project_astro , be sure to check them out

import sys
import os
import argparse
import logging
from typing import Dict, Any, Optional
import requests

from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_KALI_SERVER = "http://192.168.216.128:5000" # change to your linux IP
DEFAULT_REQUEST_TIMEOUT = 300  # 5 minutes default timeout for API requests

class KaliToolsClient:
    """Client for communicating with the Kali Linux Tools API Server"""
    
    def __init__(self, server_url: str, timeout: int = DEFAULT_REQUEST_TIMEOUT):
        """
        Initialize the Kali Tools Client
        
        Args:
            server_url: URL of the Kali Tools API Server
            timeout: Request timeout in seconds
        """
        self.server_url = server_url.rstrip("/")
        self.timeout = timeout
        logger.info(f"Initialized Kali Tools Client connecting to {server_url}")
        
    def safe_get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Perform a GET request with optional query parameters.
        
        Args:
            endpoint: API endpoint path (without leading slash)
            params: Optional query parameters
            
        Returns:
            Response data as dictionary
        """
        if params is None:
            params = {}

        url = f"{self.server_url}/{endpoint}"

        try:
            logger.debug(f"GET {url} with params: {params}")
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            return {"error": f"Request failed: {str(e)}", "success": False}
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return {"error": f"Unexpected error: {str(e)}", "success": False}

    def safe_post(self, endpoint: str, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform a POST request with JSON data.
        
        Args:
            endpoint: API endpoint path (without leading slash)
            json_data: JSON data to send
            
        Returns:
            Response data as dictionary
        """
        url = f"{self.server_url}/{endpoint}"
        
        try:
            logger.debug(f"POST {url} with data: {json_data}")
            response = requests.post(url, json=json_data, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            return {"error": f"Request failed: {str(e)}", "success": False}
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return {"error": f"Unexpected error: {str(e)}", "success": False}

    def execute_command(self, command: str) -> Dict[str, Any]:
        """
        Execute a generic command on the Kali server
        
        Args:
            command: Command to execute
            
        Returns:
            Command execution results
        """
        return self.safe_post("api/command", {"command": command})
    
    def check_health(self) -> Dict[str, Any]:
        """
        Check the health of the Kali Tools API Server
        
        Returns:
            Health status information
        """
        return self.safe_get("health")

def setup_mcp_server(kali_client: KaliToolsClient) -> FastMCP:
    """
    Set up the MCP server with all tool functions including enhanced file transfer capabilities
    
    Args:
        kali_client: Initialized KaliToolsClient
        
    Returns:
        Configured FastMCP instance with enhanced transfer tools
    """
    mcp = FastMCP("kali-mcp")
    
    # Remove enhanced server initialization for now
    # Will implement enhanced features on the Kali server side
    
    @mcp.tool()
    def tools_nmap(target: str, scan_type: str = "-sV", ports: str = "", additional_args: str = "") -> Dict[str, Any]:
        """
        Execute an Nmap scan against a target.
        
        Args:
            target: The IP address or hostname to scan
            scan_type: Scan type (e.g., -sV for version detection)
            ports: Comma-separated list of ports or port ranges
            additional_args: Additional Nmap arguments
            
        Returns:
            Scan results
        """
        data = {
            "target": target,
            "scan_type": scan_type,
            "ports": ports,
            "additional_args": additional_args
        }
        return kali_client.safe_post("api/tools/nmap", data)

    @mcp.tool()
    def tools_gobuster(url: str, mode: str = "dir", wordlist: str = "/usr/share/wordlists/dirb/common.txt", additional_args: str = "") -> Dict[str, Any]:
        """
        Execute Gobuster to find directories, DNS subdomains, or virtual hosts.
        
        Args:
            url: The target URL
            mode: Scan mode (dir, dns, fuzz, vhost)
            wordlist: Path to wordlist file
            additional_args: Additional Gobuster arguments
            
        Returns:
            Scan results
        """
        data = {
            "url": url,
            "mode": mode,
            "wordlist": wordlist,
            "additional_args": additional_args
        }
        return kali_client.safe_post("api/tools/gobuster", data)

    @mcp.tool()
    def tools_dirb(url: str, wordlist: str = "/usr/share/wordlists/dirb/common.txt", additional_args: str = "") -> Dict[str, Any]:
        """
        Execute Dirb web content scanner.
        
        Args:
            url: The target URL
            wordlist: Path to wordlist file
            additional_args: Additional Dirb arguments
            
        Returns:
            Scan results
        """
        data = {
            "url": url,
            "wordlist": wordlist,
            "additional_args": additional_args
        }
        return kali_client.safe_post("api/tools/dirb", data)

    @mcp.tool()
    def tools_nikto(target: str, additional_args: str = "") -> Dict[str, Any]:
        """
        Execute Nikto web server scanner.
        
        Args:
            target: The target URL or IP
            additional_args: Additional Nikto arguments
            
        Returns:
            Scan results
        """
        data = {
            "target": target,
            "additional_args": additional_args
        }
        return kali_client.safe_post("api/tools/nikto", data)

    @mcp.tool()
    def tools_sqlmap(url: str, data: str = "", additional_args: str = "") -> Dict[str, Any]:
        """
        Execute SQLmap SQL injection scanner.
        
        Args:
            url: The target URL
            data: POST data string
            additional_args: Additional SQLmap arguments
            
        Returns:
            Scan results
        """
        post_data = {
            "url": url,
            "data": data,
            "additional_args": additional_args
        }
        return kali_client.safe_post("api/tools/sqlmap", post_data)

    @mcp.tool()
    def tools_metasploit(module: str, options: Dict[str, Any] = {}) -> Dict[str, Any]:
        """
        Execute a Metasploit module.
        
        Args:
            module: The Metasploit module path
            options: Dictionary of module options
            
        Returns:
            Module execution results
        """
        data = {
            "module": module,
            "options": options
        }
        return kali_client.safe_post("api/tools/metasploit", data)

    @mcp.tool()
    def tools_hydra(
        target: str, 
        service: str, 
        username: str = "", 
        username_file: str = "", 
        password: str = "", 
        password_file: str = "", 
        additional_args: str = ""
    ) -> Dict[str, Any]:
        """
        Execute Hydra password cracking tool.
        
        Args:
            target: Target IP or hostname
            service: Service to attack (ssh, ftp, http-post-form, etc.)
            username: Single username to try
            username_file: Path to username file
            password: Single password to try
            password_file: Path to password file
            additional_args: Additional Hydra arguments
            
        Returns:
            Attack results
        """
        data = {
            "target": target,
            "service": service,
            "username": username,
            "username_file": username_file,
            "password": password,
            "password_file": password_file,
            "additional_args": additional_args
        }
        return kali_client.safe_post("api/tools/hydra", data)

    @mcp.tool()
    def tools_john(
        hash_file: str, 
        wordlist: str = "", 
        format_type: str = "", 
        additional_args: str = ""
    ) -> Dict[str, Any]:
        """
        Execute John the Ripper password cracker.
        
        Args:
            hash_file: Path to file containing hashes
            wordlist: Path to wordlist file
            format_type: Hash format type
            additional_args: Additional John arguments
            
        Returns:
            Cracking results
        """
        data = {
            "hash_file": hash_file,
            "wordlist": wordlist,
            "format_type": format_type,
            "additional_args": additional_args
        }
        return kali_client.safe_post("api/tools/john", data)

    @mcp.tool()
    def tools_wpscan(url: str, additional_args: str = "") -> Dict[str, Any]:
        """
        Execute WPScan WordPress vulnerability scanner.
        
        Args:
            url: The target WordPress URL
            additional_args: Additional WPScan arguments
            
        Returns:
            Scan results
        """
        data = {
            "url": url,
            "additional_args": additional_args
        }
        return kali_client.safe_post("api/tools/wpscan", data)

    @mcp.tool()
    def tools_enum4linux(target: str, additional_args: str = "-a") -> Dict[str, Any]:
        """
        Execute Enum4linux Windows/Samba enumeration tool.
        
        Args:
            target: The target IP or hostname
            additional_args: Additional enum4linux arguments
            
        Returns:
            Enumeration results
        """
        data = {
            "target": target,
            "additional_args": additional_args
        }
        return kali_client.safe_post("api/tools/enum4linux", data)

    @mcp.tool()
    def health() -> Dict[str, Any]:
        """
        Check the health status of the Kali API server.
        
        Returns:
            Server health information
        """
        return kali_client.check_health()
    
    @mcp.tool()
    def command(command: str) -> Dict[str, Any]:
        """
        Execute an arbitrary command on the Kali server.
        
        Args:
            command: The command to execute
            
        Returns:
            Command execution results
        """
        return kali_client.execute_command(command)

    # SSH Session Management Tools
    @mcp.tool()
    def ssh_session_start(
        target: str, 
        username: str, 
        password: str = "", 
        key_file: str = "", 
        port: int = 22, 
        session_id: str = ""
    ) -> Dict[str, Any]:
        """
        Start an interactive SSH session similar to reverse shell sessions.
        
        Args:
            target: Target IP or hostname
            username: SSH username
            password: SSH password (if using password auth)
            key_file: Path to SSH private key file (if using key auth)
            port: SSH port (default: 22)
            session_id: Optional session identifier
            
        Returns:
            SSH session startup status and session information
        """
        data = {
            "target": target,
            "username": username,
            "password": password,
            "key_file": key_file,
            "port": port,
            "session_id": session_id
        }
        return kali_client.safe_post("api/ssh/session/start", data)

    @mcp.tool()
    def ssh_session_command(session_id: str, command: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Execute a command in an active SSH session.
        
        Args:
            session_id: The SSH session ID
            command: The command to execute
            timeout: Command timeout in seconds
            
        Returns:
            Command execution results from the SSH session
        """
        data = {
            "command": command,
            "timeout": timeout
        }
        return kali_client.safe_post(f"api/ssh/session/{session_id}/command", data)

    @mcp.tool()
    def ssh_session_status(session_id: str = "") -> Dict[str, Any]:
        """
        Get the status of SSH sessions.
        
        Args:
            session_id: Optional specific session ID to check (if empty, shows all sessions)
            
        Returns:
            Status information for SSH sessions
        """
        if session_id:
            return kali_client.safe_get(f"api/ssh/session/{session_id}/status")
        else:
            return kali_client.safe_get("api/ssh/sessions")

    @mcp.tool()
    def ssh_session_stop(session_id: str) -> Dict[str, Any]:
        """
        Stop an SSH session.
        
        Args:
            session_id: The session ID to stop
            
        Returns:
            Stop operation result
        """
        return kali_client.safe_post(f"api/ssh/session/{session_id}/stop", {})

    @mcp.tool()
    def ssh_sessions() -> Dict[str, Any]:
        """
        List all active SSH sessions with their details.
        
        Returns:
            Dictionary containing all active sessions with their IDs, connection status, and timestamps
        """
        return kali_client.safe_get("api/ssh/sessions")

    @mcp.tool()
    def ssh_session_upload_content(
        session_id: str, 
        content: str, 
        remote_file: str, 
        encoding: str = "utf-8", 
        method: str = "auto"
    ) -> Dict[str, Any]:
        """
        SSH session: upload content directly to the target with optimized handling for large files.
        
        Args:
            session_id: The SSH session ID
            content: Content to upload (base64 encoded if binary)
            remote_file: Path where to save the file on the target
            encoding: Content encoding (utf-8, base64)
            method: Upload method (auto, single_command, streaming, chunked)
                   - auto: Automatically selects best method based on file size
                   - single_command: Best for < 50KB
                   - streaming: Best for 50KB-500KB  
                   - chunked: Best for > 500KB
        """
        data = {
            "content": content,
            "remote_file": remote_file,
            "encoding": encoding,
            "method": method
        }
        return kali_client.safe_post(f"api/ssh/session/{session_id}/upload_content", data)

    @mcp.tool()
    def ssh_session_download_content(
        session_id: str, 
        remote_file: str, 
        method: str = "auto", 
        max_size_mb: int = 100
    ) -> Dict[str, Any]:
        """
        SSH session: download file content from target with optimized handling for large files.
        
        Args:
            session_id: The SSH session ID
            remote_file: Path to the file on the target
            method: Download method (auto, direct, chunked)
                   - auto: Automatically selects best method based on file size
                   - direct: Best for < 1MB
                   - chunked: Best for >= 1MB
            max_size_mb: Maximum file size to download (safety limit)
        """
        data = {
            "remote_file": remote_file,
            "method": method,
            "max_size_mb": max_size_mb
        }
        return kali_client.safe_post(f"api/ssh/session/{session_id}/download_content", data)

    @mcp.tool()
    def ssh_estimate_transfer(file_size_bytes: int, operation: str = "upload") -> Dict[str, Any]:
        """
        Estimate SSH transfer time and get method recommendations for large files.
        
        Args:
            file_size_bytes: File size in bytes
            operation: Operation type (upload, download)
            
        Returns:
            Transfer time estimates and method recommendations
        """
        data = {
            "file_size_bytes": file_size_bytes,
            "operation": operation
        }
        return kali_client.safe_post("api/ssh/estimate_transfer", data)

    # Reverse Shell Management Tools
    @mcp.tool()
    def reverse_shell_listener_start(port: int = 4444, session_id: str = "") -> Dict[str, Any]:
        """
        Start a reverse shell listener on the specified port.
        
        Args:
            port: Port to listen on (default: 4444)
            session_id: Optional session identifier
            
        Returns:
            Listener startup status and session information
        """
        data = {
            "port": port,
            "session_id": session_id
        }
        return kali_client.safe_post("api/reverse-shell/listener/start", data)

    @mcp.tool()
    def reverse_shell_command(session_id: str, command: str, timeout: int = 10) -> Dict[str, Any]:
        """
        Execute a command in an active reverse shell session.
        
        Args:
            session_id: The session ID of the reverse shell
            command: The command to execute
            timeout: Command timeout in seconds
            
        Returns:
            Command execution results from the reverse shell
        """
        data = {
            "command": command,
            "timeout": timeout
        }
        return kali_client.safe_post(f"api/reverse-shell/{session_id}/command", data)

    @mcp.tool()
    def reverse_shell_status(session_id: str = "") -> Dict[str, Any]:
        """
        Get the status of reverse shell sessions.
        
        Args:
            session_id: Optional specific session ID to check (if empty, shows all sessions)
            
        Returns:
            Status information for reverse shell sessions
        """
        if session_id:
            return kali_client.safe_get(f"api/reverse-shell/{session_id}/status")
        else:
            return kali_client.safe_get("api/reverse-shell/sessions")

    @mcp.tool()
    def reverse_shell_stop(session_id: str) -> Dict[str, Any]:
        """
        Stop a reverse shell session.
        
        Args:
            session_id: The session ID to stop
            
        Returns:
            Stop operation result
        """
        return kali_client.safe_post(f"api/reverse-shell/{session_id}/stop", {})

    @mcp.tool()
    def reverse_shell_sessions() -> Dict[str, Any]:
        """
        List all active reverse shell sessions with their details.
        
        Returns:
            Dictionary containing all active sessions with their IDs, ports, connection status, and timestamps
        """
        return kali_client.safe_get("api/reverse-shell/sessions")

    @mcp.tool()
    def reverse_shell_send_payload(session_id: str, payload_command: str, timeout: int = 10, wait_seconds: int = 5) -> Dict[str, Any]:
        """
        Send a payload command to trigger a reverse shell connection in a non-blocking way.
        
        This function is specifically designed for sending reverse shell payloads or other
        commands that establish network connections back to the listener. It executes the
        payload in a background thread to avoid blocking the server.
        
        Waits a few seconds after execution and returns session status to verify if the
        reverse shell connection was established.
        
        Common use cases:
        - Sending reverse shell payloads to compromised web applications
        - Executing commands that establish network connections
        - Triggering actions on remote systems without blocking the API
        
        Args:
            session_id: The session ID of the reverse shell listener
            payload_command: The payload command to execute (e.g., curl with reverse shell)
            timeout: Timeout for the payload execution in seconds (default: 10)
            wait_seconds: Seconds to wait before checking session status (default: 5)
            
        Returns:
            Dictionary containing the payload execution status and session info
        """
        data = {
            "payload_command": payload_command,
            "timeout": timeout,
            "wait_seconds": wait_seconds
        }
        return kali_client.safe_post(f"api/reverse-shell/{session_id}/send-payload", data)

    # File Operations Tools
    @mcp.tool()
    def kali_upload(content: str, remote_path: str, encoding: str = "base64") -> Dict[str, Any]:
        """
        Upload content directly to the Kali server filesystem using robust chunking.
        
        Args:
            content: Base64 encoded content to upload (or raw content if encoding != "base64")
            remote_path: Destination path on the Kali server
            encoding: Content encoding ("base64", "utf-8", "binary")
        """
        data = {
            "content": content,
            "remote_path": remote_path,
            "encoding": encoding
        }
        return kali_client.safe_post("api/kali/upload", data)

    @mcp.tool()
    def kali_download(remote_file: str, mode: str = "content", local_directory: str = "/tmp") -> Dict[str, Any]:
        """
        Download a file from the Kali server filesystem.
        
        Args:
            remote_file: Path to the file on the Kali server
            mode: Download mode - "content" returns base64 content, "file" saves locally
            local_directory: Directory to save file when mode="file" (default: /tmp)
            
        Returns:
            Dict with file info and either content (base64) or local file path
        """
        data = {
            "remote_file": remote_file,
            "mode": mode,
            "local_directory": local_directory
        }
        return kali_client.safe_post("api/kali/download", data)

    @mcp.tool()
    def target_upload_file(
        session_id: str, 
        local_file: str, 
        remote_file: str, 
        method: str = "base64"
    ) -> Dict[str, Any]:
        """
        Reverse shell: upload a file to the target using file path.
        
        Args:
            session_id: The reverse shell session ID
            local_file: Path to the local file on the Kali server
            remote_file: Path where to save the file on the target
            method: Upload method (base64, wget, curl)
        """
        data = {
            "session_id": session_id,
            "local_file": local_file,
            "remote_file": remote_file,
            "method": method
        }
        return kali_client.safe_post("api/target/upload_file", data)

    @mcp.tool()
    def reverse_shell_upload_content(
        session_id: str, 
        content: str, 
        remote_file: str, 
        method: str = "base64", 
        encoding: str = "utf-8"
    ) -> Dict[str, Any]:
        """
        Reverse shell: upload content directly to the target.
        
        Args:
            session_id: The reverse shell session ID
            content: Base64 encoded content to upload
            remote_file: Path where to save the file on the target
            method: Upload method (base64)
            encoding: Content encoding (utf-8, binary)
        """
        data = {
            "session_id": session_id,
            "content": content,
            "remote_file": remote_file,
            "method": method,
            "encoding": encoding
        }
        return kali_client.safe_post(f"api/reverse-shell/{session_id}/upload-content", data)

    @mcp.tool()
    def target_download_file(
        session_id: str, 
        remote_file: str, 
        local_file: str, 
        method: str = "base64"
    ) -> Dict[str, Any]:
        """
        Reverse shell: download a file from target to Kali server.
        
        Args:
            session_id: The reverse shell session ID
            remote_file: Path to the file on the target
            local_file: Path where to save the file on the Kali server
            method: Download method (base64, cat)
        """
        data = {
            "session_id": session_id,
            "remote_file": remote_file,
            "local_file": local_file,
            "method": method
        }
        return kali_client.safe_post("api/target/download_file", data)

    @mcp.tool()
    def reverse_shell_download_content(
        session_id: str, 
        remote_file: str, 
        method: str = "base64"
    ) -> Dict[str, Any]:
        """
        Reverse shell: download file content from target and return as base64.
        
        Args:
            session_id: The reverse shell session ID
            remote_file: Path to the file on the target
            method: Download method (base64, cat)
        """
        data = {
            "session_id": session_id,
            "remote_file": remote_file,
            "method": method
        }
        return kali_client.safe_post(f"api/reverse-shell/{session_id}/download-content", data)

    # Additional missing tools from Kali server
    @mcp.tool()
    def reverse_shell_generate_payload(
        local_ip: str, 
        local_port: int = 4444, 
        payload_type: str = "bash", 
        encoding: str = "base64"
    ) -> Dict[str, Any]:
        """
        Generate reverse shell payloads that can be manually executed on targets.
        
        This generates various types of reverse shell commands that you can:
        - Copy-paste into a compromised terminal
        - Upload as a script file using file transfer functions
        - Execute through other exploitation methods
        - Use in social engineering attacks
        
        Args:
            local_ip: Your local IP address that the target should connect back to
            local_port: Local port to connect back to (default: 4444)
            payload_type: Type of payload (bash, python, nc, php, powershell, perl)
            encoding: Encoding format (plain, base64, url, hex)
            
        Returns:
            Generated payload in various formats ready for manual execution
        """
        data = {
            "local_ip": local_ip,
            "local_port": local_port,
            "payload_type": payload_type,
            "encoding": encoding
        }
        return kali_client.safe_post("api/reverse-shell/generate-payload", data)

    # Network and System Information Tools
    @mcp.tool()
    def system_network_info() -> Dict[str, Any]:
        """
        Get comprehensive network information for the Kali Linux system.
        
        Returns:
            Network information including interfaces, IP addresses, routing table, etc.
        """
        return kali_client.safe_get("api/system/network-info")

    return mcp

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run the Kali MCP Client")
    parser.add_argument("--server", type=str, default=DEFAULT_KALI_SERVER, 
                      help=f"Kali API server URL (default: {DEFAULT_KALI_SERVER})")
    parser.add_argument("--timeout", type=int, default=DEFAULT_REQUEST_TIMEOUT,
                      help=f"Request timeout in seconds (default: {DEFAULT_REQUEST_TIMEOUT})")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    return parser.parse_args()

def main():
    """Main entry point for the MCP server."""
    args = parse_args()
    
    # Configure logging based on debug flag
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    # Initialize the Kali Tools client
    kali_client = KaliToolsClient(args.server, args.timeout)
    
    # Check server health and log the result
    health = kali_client.check_health()
    if "error" in health:
        logger.warning(f"Unable to connect to Kali API server at {args.server}: {health['error']}")
        logger.warning("MCP server will start, but tool execution may fail")
    else:
        logger.info(f"Successfully connected to Kali API server at {args.server}")
        logger.info(f"Server health status: {health['status']}")
        if not health.get("all_essential_tools_available", False):
            logger.warning("Not all essential tools are available on the Kali server")
            missing_tools = [tool for tool, available in health.get("tools_status", {}).items() if not available]
            if missing_tools:
                logger.warning(f"Missing tools: {', '.join(missing_tools)}")
    
    # Set up and run the MCP server
    mcp = setup_mcp_server(kali_client)
    logger.info("Starting Kali MCP server")
    mcp.run()

if __name__ == "__main__":
    main()
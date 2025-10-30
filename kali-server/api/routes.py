#!/usr/bin/env python3
"""API Routes module for Kali Server."""

import os
import base64
import traceback
import queue
import threading
from flask import Flask, request, jsonify, Response, stream_with_context
from core.config import logger, active_sessions, active_ssh_sessions, VERSION, BLOCKING_TIMEOUT
from core.ssh_manager import SSHSessionManager
from core.reverse_shell_manager import ReverseShellManager
from core.command_executor import execute_command, stream_command_execution
from tools.kali_tools import (
    run_nmap, run_gobuster, run_dirb, run_nikto, run_sqlmap,
    run_metasploit, run_hydra, run_john, run_wpscan, run_enum4linux,
    run_subfinder, run_httpx, run_searchsploit, run_nuclei, run_arjun, run_fierce,
    run_subzy, run_assetfinder, run_waybackurls, run_shodan, run_byp4xx
)
from utils.kali_operations import upload_content, download_content




def sse_response(generator):
    """
    Proper SSE content type + disable buffering so events flush immediately.
    Use this for all streaming endpoints.
    """
    return Response(
        stream_with_context(generator),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # avoids buffering on nginx/akamai/alb
        },
    )

def setup_routes(app: Flask):
    """Setup all API routes for the Flask application."""
    
    # Health check
    @app.route("/health", methods=["GET"])
    def health():
        """Health check endpoint with tool availability status."""
        try:
            from shutil import which
            tools = [
                "nmap","gobuster","dirb","nikto","sqlmap","msfconsole","hydra",
                "john","wpscan","enum4linux","subfinder","httpx","nuclei","arjun",
                "fierce","subzy","assetfinder","waybackurls","byp4xx","ffuf"
            ]
            status = {}
            go_bin = os.path.expanduser("~/go/bin")
            for t in tools:
                status[t] = bool(which(t) or os.path.exists(os.path.join(go_bin, t)))

            all_ok = all(status.values())
            return jsonify({
                "status": "healthy",
                "message": "Kali Linux Tools API Server is running",
                "version": VERSION,
                "all_essential_tools_available": all_ok,
                "tools_status": status,
            })
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return jsonify({"status": "degraded", "error": str(e), "version": VERSION}), 500

    # Network information
    @app.route("/api/system/network-info", methods=["GET"])
    def get_network_info():
        """Get comprehensive network information for the Kali Linux system."""
        try:
            from utils.network_utils import get_network_info as get_net_info
            network_info = get_net_info()
            return jsonify(network_info)
        except Exception as e:
            logger.error(f"Error getting network info: {str(e)}")
            return jsonify({"error": str(e), "success": False}), 500

    # Command execution
    @app.route("/api/command", methods=["POST"])
    def command():
        """Execute an arbitrary command on the Kali server with streaming support."""
        try:
            params = request.json
            if not params or "command" not in params:
                return jsonify({
                    "error": "Command parameter is required"
                }), 400
            
            command = params["command"]
            streaming = params.get("streaming", False)
            
            # Check if streaming is requested or auto-detect
            from core.tool_config import is_streaming_tool
            tool_name = command.split()[0] if command.strip() else ""
            should_stream = streaming or is_streaming_tool(tool_name)
            
            if should_stream:
                # Stream the output in real-time
                return Response(
                    stream_with_context(stream_command_execution(command, streaming)),
                    content_type="text/plain; charset=utf-8",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive"
                    }
                )
            else:
                # Non-streaming execution with timeout
                DEFAULT_TIMEOUT = 10  # seconds for non-streaming commands
                timeout = params.get("timeout", DEFAULT_TIMEOUT)
                result = execute_command(command, timeout=timeout)
                return jsonify(result)
                
        except Exception as e:
            logger.error(f"Error in command endpoint: {str(e)}")
            return jsonify({
                "error": f"Server error: {str(e)}"
            }), 500

    # Tool endpoints
    @app.route("/api/tools/nmap", methods=["POST"])
    def nmap():
        try:
            params = request.json or {}
            result = run_nmap(params)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in nmap endpoint: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/tools/gobuster", methods=["POST"])
    def gobuster():
        try:
            params = request.json or {}
            streaming = params.get("streaming", False)
            
            if streaming:
                output_queue = queue.Queue()
                
                def generate_output():
                    def handle_output(source, line):
                        output_queue.put(f"data: {{\"type\": \"output\", \"source\": \"{source}\", \"line\": \"{line.replace('\"', '\\\"')}\"}}\n\n")
                    
                    # Execute command in separate thread
                    result_container = {}
                    
                    def execute_in_thread():
                        try:
                            result = run_gobuster(params, on_output=handle_output)
                            result_container['result'] = result
                        except Exception as e:
                            result_container['error'] = str(e)
                        finally:
                            output_queue.put("DONE")
                    
                    thread = threading.Thread(target=execute_in_thread)
                    thread.start()
                    
                    # Yield outputs as they come
                    while True:
                        try:
                            item = output_queue.get(timeout=1)
                            if item == "DONE":
                                break
                            yield item
                        except queue.Empty:
                            yield "data: {\"type\": \"heartbeat\"}\n\n"
                            continue
                    
                    # Wait for thread to complete
                    thread.join()
                    
                    # Send final result
                    if 'result' in result_container:
                        result = result_container['result']
                        yield f"data: {{\"type\": \"result\", \"success\": {str(result['success']).lower()}, \"return_code\": {result.get('return_code', 0)}}}\n\n"
                    elif 'error' in result_container:
                        yield f"data: {{\"type\": \"error\", \"message\": \"Server error: {result_container['error']}\"}}\n\n"
                    
                    yield f"data: {{\"type\": \"complete\"}}\n\n"
                
                return Response(
                    stream_with_context(generate_output()),
                    content_type="text/plain; charset=utf-8",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive"
                    }
                )
            else:
                result = run_gobuster(params)
                return jsonify(result)
        except Exception as e:
            logger.error(f"Error in gobuster endpoint: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/tools/dirb", methods=["POST"])
    def dirb():
        try:
            params = request.json or {}
            streaming = params.get("streaming", False)
            
            if streaming:
                output_queue = queue.Queue()
                
                def generate_output():
                    def handle_output(source, line):
                        output_queue.put(f"data: {{\"type\": \"output\", \"source\": \"{source}\", \"line\": \"{line.replace('\"', '\\\"')}\"}}\n\n")
                    
                    # Execute command in separate thread
                    result_container = {}
                    
                    def execute_in_thread():
                        try:
                            result = run_dirb(params, on_output=handle_output)
                            result_container['result'] = result
                        except Exception as e:
                            result_container['error'] = str(e)
                        finally:
                            output_queue.put("DONE")
                    
                    thread = threading.Thread(target=execute_in_thread)
                    thread.start()
                    
                    # Yield outputs as they come
                    while True:
                        try:
                            item = output_queue.get(timeout=1)
                            if item == "DONE":
                                break
                            yield item
                        except queue.Empty:
                            yield "data: {\"type\": \"heartbeat\"}\n\n"
                            continue
                    
                    # Wait for thread to complete
                    thread.join()
                    
                    # Send final result
                    if 'result' in result_container:
                        result = result_container['result']
                        yield f"data: {{\"type\": \"result\", \"success\": {str(result['success']).lower()}, \"return_code\": {result.get('return_code', 0)}}}\n\n"
                    elif 'error' in result_container:
                        yield f"data: {{\"type\": \"error\", \"message\": \"Server error: {result_container['error']}\"}}\n\n"
                    
                    yield f"data: {{\"type\": \"complete\"}}\n\n"
                
                return Response(
                    stream_with_context(generate_output()),
                    content_type="text/plain; charset=utf-8",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive"
                    }
                )
            else:
                result = run_dirb(params)
                return jsonify(result)
        except Exception as e:
            logger.error(f"Error in dirb endpoint: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/tools/nikto", methods=["POST"])
    def nikto():
        try:
            params = request.json or {}
            streaming = params.get("streaming", False)
            
            if streaming:
                output_queue = queue.Queue()
                
                def generate_output():
                    def handle_output(source, line):
                        output_queue.put(f"data: {{\"type\": \"output\", \"source\": \"{source}\", \"line\": \"{line.replace('\"', '\\\"')}\"}}\n\n")
                    
                    # Execute command in separate thread
                    result_container = {}
                    
                    def execute_in_thread():
                        try:
                            result = run_nikto(params, on_output=handle_output)
                            result_container['result'] = result
                        except Exception as e:
                            result_container['error'] = str(e)
                        finally:
                            output_queue.put("DONE")
                    
                    thread = threading.Thread(target=execute_in_thread)
                    thread.start()
                    
                    # Yield outputs as they come
                    while True:
                        try:
                            item = output_queue.get(timeout=1)
                            if item == "DONE":
                                break
                            yield item
                        except queue.Empty:
                            yield "data: {\"type\": \"heartbeat\"}\n\n"
                            continue
                    
                    # Wait for thread to complete
                    thread.join()
                    
                    # Send final result
                    if 'result' in result_container:
                        result = result_container['result']
                        yield f"data: {{\"type\": \"result\", \"success\": {str(result['success']).lower()}, \"return_code\": {result.get('return_code', 0)}}}\n\n"
                    elif 'error' in result_container:
                        yield f"data: {{\"type\": \"error\", \"message\": \"Server error: {result_container['error']}\"}}\n\n"
                    
                    yield f"data: {{\"type\": \"complete\"}}\n\n"
                
                return Response(
                    stream_with_context(generate_output()),
                    content_type="text/plain; charset=utf-8",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive"
                    }
                )
            else:
                result = run_nikto(params)
                return jsonify(result)
        except Exception as e:
            logger.error(f"Error in nikto endpoint: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/tools/sqlmap", methods=["POST"])
    def sqlmap():
        try:
            params = request.json or {}
            result = run_sqlmap(params)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in sqlmap endpoint: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/tools/metasploit", methods=["POST"])
    def metasploit():
        try:
            params = request.json or {}
            result = run_metasploit(params)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in metasploit endpoint: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/tools/hydra", methods=["POST"])
    def hydra():
        try:
            params = request.json or {}
            result = run_hydra(params)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in hydra endpoint: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/tools/john", methods=["POST"])
    def john():
        try:
            params = request.json or {}
            result = run_john(params)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in john endpoint: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/tools/wpscan", methods=["POST"])
    def wpscan():
        try:
            params = request.json or {}
            result = run_wpscan(params)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in wpscan endpoint: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/tools/enum4linux", methods=["POST"])
    def enum4linux():
        try:
            params = request.json or {}
            result = run_enum4linux(params)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in enum4linux endpoint: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500


    @app.route("/api/tools/byp4xx", methods=["POST"])
    def byp4xx():
        try:
            params = request.json or {}
            result = run_byp4xx(params)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in byp4xx endpoint: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/tools/subfinder", methods=["POST"])
    def subfinder():
        try:
            params = request.json or {}
            result = run_subfinder(params)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in subfinder endpoint: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/tools/httpx", methods=["POST"])
    def httpx():
        try:
            params = request.json or {}
            result = run_httpx(params)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in httpx endpoint: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500


    @app.route("/api/tools/fierce", methods=["POST"])
    def tools_fierce():
        try:
            params = request.json or {}
            result = run_fierce(params)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in fierce endpoint: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500
    @app.route("/api/tools/searchsploit", methods=["POST"])
    def searchsploit():
        try:
            params = request.json or {}
            result = run_searchsploit(params)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in searchsploit endpoint: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/tools/nuclei", methods=["POST"])
    def nuclei():
        try:
            params = request.json or {}
            result = run_nuclei(params)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in nuclei endpoint: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/tools/arjun", methods=["POST"])
    def arjun():
        try:
            params = request.json or {}
            result = run_arjun(params)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in arjun endpoint: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500
    # SSH session management
    @app.route("/api/ssh/session/start", methods=["POST"])
    def start_ssh_session():
        try:
            params = request.json
            if not params:
                return jsonify({"error": "Request body is required"}), 400
            
            target = params.get("target")
            username = params.get("username")
            password = params.get("password", "")
            key_file = params.get("key_file", "")
            port = params.get("port", 22)
            session_id = params.get("session_id", f"ssh_{target}_{username}")
            
            if not target or not username:
                return jsonify({"error": "Target and username are required"}), 400
            
            if session_id in active_ssh_sessions:
                return jsonify({"error": f"SSH session {session_id} already exists"}), 400
            
            ssh_manager = SSHSessionManager(target, username, password, key_file, port, session_id)
            result = ssh_manager.start_session()
            
            if result.get("success"):
                active_ssh_sessions[session_id] = ssh_manager
            
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error starting SSH session: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/ssh/session/<session_id>/command", methods=["POST"])
    def execute_ssh_command(session_id):
        try:
            if session_id not in active_ssh_sessions:
                return jsonify({"error": f"SSH session {session_id} not found"}), 404
            
            params = request.json
            if not params or "command" not in params:
                return jsonify({"error": "Command parameter is required"}), 400
            
            command = params["command"]
            timeout = params.get("timeout", 30)
            
            ssh_manager = active_ssh_sessions[session_id]
            result = ssh_manager.send_command(command, timeout)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error executing SSH command: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/ssh/session/<session_id>/status", methods=["GET"])
    def get_ssh_session_status(session_id):
        try:
            if session_id not in active_ssh_sessions:
                return jsonify({"error": f"SSH session {session_id} not found"}), 404
            
            ssh_manager = active_ssh_sessions[session_id]
            status = ssh_manager.get_status()
            return jsonify(status)
        except Exception as e:
            logger.error(f"Error getting SSH session status: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/ssh/session/<session_id>/stop", methods=["POST"])
    def stop_ssh_session(session_id):
        try:
            if session_id not in active_ssh_sessions:
                return jsonify({"error": f"SSH session {session_id} not found"}), 404
            
            ssh_manager = active_ssh_sessions[session_id]
            ssh_manager.stop()
            del active_ssh_sessions[session_id]
            
            return jsonify({
                "success": True,
                "message": f"SSH session {session_id} stopped successfully"
            })
        except Exception as e:
            logger.error(f"Error stopping SSH session: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/ssh/sessions", methods=["GET"])
    def list_ssh_sessions():
        try:
            sessions = {}
            for session_id, ssh_manager in active_ssh_sessions.items():
                sessions[session_id] = ssh_manager.get_status()
            return jsonify({"sessions": sessions})
        except Exception as e:
            logger.error(f"Error listing SSH sessions: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/ssh/session/<session_id>/upload_content", methods=["POST"])
    def upload_content_to_ssh_session(session_id):
        """Upload content to target via SSH session with integrity verification"""
        try:
            if session_id not in active_ssh_sessions:
                return jsonify({"error": f"SSH session {session_id} not found"}), 404
            
            params = request.json or {}
            content = params.get("content", "")
            remote_file = params.get("remote_file", "")
            encoding = params.get("encoding", "base64")
            
            if not content or not remote_file:
                return jsonify({
                    "error": "content and remote_file parameters are required"
                }), 400
            
            ssh_manager = active_ssh_sessions[session_id]
            
            # Use the new upload method with verification
            result = ssh_manager.upload_content(content, remote_file, encoding)
            
            # Check if the operation failed and determine appropriate HTTP status code
            if not result.get("success"):
                error_message = result.get("error", "Unknown error")
                
                # Check for permission errors
                if ("Permission denied" in error_message or
                    "Access denied" in error_message):
                    return jsonify(result), 403
                
                # Check for file system errors
                elif ("No space left" in error_message or
                      "Disk full" in error_message):
                    return jsonify(result), 507  # Insufficient Storage
                
                # Other errors - return 500
                else:
                    return jsonify(result), 500
            
            # Success case
            return jsonify(result)
                
        except Exception as e:
            logger.error(f"Error in SSH upload endpoint: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/ssh/session/<session_id>/download_content", methods=["POST"])
    def download_content_from_ssh_session(session_id):
        """Download content from target via SSH session with integrity verification"""
        try:
            if session_id not in active_ssh_sessions:
                return jsonify({"error": f"SSH session {session_id} not found"}), 404
            
            params = request.json or {}
            remote_file = params.get("remote_file", "")
            
            if not remote_file:
                return jsonify({
                    "error": "remote_file parameter is required"
                }), 400
            
            ssh_manager = active_ssh_sessions[session_id]
            
            # Use the new download method with verification
            result = ssh_manager.download_content(remote_file, encoding="base64")
            
            # Check if the operation failed and determine appropriate HTTP status code
            if not result.get("success"):
                error_message = result.get("error", "Unknown error")
                
                # Check for file not found errors
                if ("No such file or directory" in error_message or 
                    "File not found" in error_message or
                    "does not exist" in error_message):
                    return jsonify(result), 404
                
                # Check for permission errors
                elif ("Permission denied" in error_message or
                      "Access denied" in error_message):
                    return jsonify(result), 403
                
                # Other errors - return 500
                else:
                    return jsonify(result), 500
            
            # Success case
            return jsonify(result)
                    
        except Exception as e:
            logger.error(f"Error in SSH download endpoint: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/ssh/estimate_transfer", methods=["POST"])
    def estimate_ssh_transfer():
        """Estimate SSH transfer performance and provide recommendations"""
        try:
            params = request.json or {}
            file_size_bytes = params.get("file_size_bytes", 0)
            operation = params.get("operation", "upload")
            
            if file_size_bytes <= 0:
                return jsonify({
                    "error": "file_size_bytes parameter must be greater than 0"
                }), 400
            
            file_size_kb = file_size_bytes / 1024
            file_size_mb = file_size_bytes / (1024 * 1024)
            
            base_throughput_kbps = 1000
            overhead_factor = 1.2
            
            if file_size_bytes < 50 * 1024:
                recommended_method = "single_command"
                estimated_time = (file_size_kb * overhead_factor) / base_throughput_kbps + 1
            elif file_size_bytes < 500 * 1024:
                recommended_method = "streaming"
                estimated_time = (file_size_kb * overhead_factor) / base_throughput_kbps + 2
            else:
                recommended_method = "chunked"
                estimated_time = (file_size_kb * overhead_factor) / base_throughput_kbps + 3
            
            return jsonify({
                "success": True,
                "file_size_bytes": file_size_bytes,
                "file_size_kb": round(file_size_kb, 2),
                "file_size_mb": round(file_size_mb, 2),
                "operation": operation,
                "recommended_method": recommended_method,
                "estimated_time_seconds": round(estimated_time, 2),
                "estimated_throughput_kbps": base_throughput_kbps,
                "recommendations": [
                    "Compress files before transfer",
                    "Consider splitting large files",
                    "Use direct Kali upload for files on local network"
                ] if file_size_mb > 10 else []
            })
            
        except Exception as e:
            logger.error(f"Error in SSH estimate endpoint: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    # Reverse shell management
    @app.route("/api/reverse-shell/listener/start", methods=["POST"])
    def start_reverse_shell_listener():
        try:
            params = request.json or {}
            port = params.get("port", 4444)
            session_id = params.get("session_id", f"shell_{port}")
            listener_type = params.get("listener_type", "pwncat")
            
            if session_id in active_sessions:
                return jsonify({"error": f"Session {session_id} already exists"}), 400
            
            shell_manager = ReverseShellManager(port, session_id, listener_type)
            result = shell_manager.start_listener()
            
            if result.get("success"):
                active_sessions[session_id] = shell_manager
            
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error starting reverse shell listener: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/reverse-shell/<session_id>/command", methods=["POST"])
    def execute_shell_command(session_id):
        try:
            if session_id not in active_sessions:
                return jsonify({"error": f"Session {session_id} not found"}), 404
            
            params = request.json
            if not params or "command" not in params:
                return jsonify({"error": "Command parameter is required"}), 400
            
            command = params["command"]
            timeout = params.get("timeout", 60)
            
            shell_manager = active_sessions[session_id]
            result = shell_manager.send_command(command, timeout)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error executing shell command: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/reverse-shell/<session_id>/send-payload", methods=["POST"])
    def send_shell_payload(session_id):
        """Send a payload command in a non-blocking way (e.g., reverse shell payload)."""
        try:
            if session_id not in active_sessions:
                return jsonify({"error": f"Session {session_id} not found"}), 404
            
            params = request.json
            if not params or "payload_command" not in params:
                return jsonify({"error": "payload_command parameter is required"}), 400
            
            payload_command = params["payload_command"]
            timeout = params.get("timeout", 10)
            wait_seconds = params.get("wait_seconds", 5)
            
            shell_manager = active_sessions[session_id]
            result = shell_manager.send_payload(payload_command, timeout, wait_seconds)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error sending shell payload: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/reverse-shell/<session_id>/status", methods=["GET"])
    def get_shell_session_status(session_id):
        try:
            if session_id not in active_sessions:
                return jsonify({"error": f"Session {session_id} not found"}), 404
            
            shell_manager = active_sessions[session_id]
            status = shell_manager.get_status()
            return jsonify(status)
        except Exception as e:
            logger.error(f"Error getting shell session status: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/reverse-shell/<session_id>/stop", methods=["POST"])
    def stop_shell_session(session_id):
        try:
            if session_id not in active_sessions:
                return jsonify({"error": f"Session {session_id} not found"}), 404
            
            shell_manager = active_sessions[session_id]
            shell_manager.stop()
            del active_sessions[session_id]
            
            return jsonify({
                "success": True,
                "message": f"Shell session {session_id} stopped successfully"
            })
        except Exception as e:
            logger.error(f"Error stopping shell session: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/reverse-shell/sessions", methods=["GET"])
    def list_shell_sessions():
        try:
            sessions = {}
            for session_id, shell_manager in active_sessions.items():
                sessions[session_id] = shell_manager.get_status()
            return jsonify(sessions)
        except Exception as e:
            logger.error(f"Error listing shell sessions: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    # Additional reverse shell routes
    @app.route("/api/reverse-shell/generate-payload", methods=["POST"])
    def generate_reverse_shell_payload():
        try:
            params = request.json or {}
            local_ip = params.get("local_ip", "127.0.0.1")
            local_port = params.get("local_port", 4444)
            payload_type = params.get("payload_type", "bash")
            encoding = params.get("encoding", "base64")
            
            result = ReverseShellManager.generate_payload(local_ip, local_port, payload_type, encoding)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in generate payload endpoint: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/reverse-shell/<session_id>/upload-content", methods=["POST"])
    def upload_content_to_shell(session_id):
        try:
            if session_id not in active_sessions:
                return jsonify({"error": f"Session {session_id} not found"}), 404
            
            params = request.json
            if not params:
                return jsonify({"error": "Request body is required"}), 400
            
            content = params.get("content")
            remote_file = params.get("remote_file")
            encoding = params.get("encoding", "utf-8")
            
            if not content or not remote_file:
                return jsonify({"error": "content and remote_file are required"}), 400
            
            shell_manager = active_sessions[session_id]
            result = shell_manager.upload_content(content, remote_file, encoding)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in upload content endpoint: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/reverse-shell/<session_id>/download-content", methods=["POST"])
    def download_content_from_shell(session_id):
        try:
            if session_id not in active_sessions:
                return jsonify({"error": f"Session {session_id} not found"}), 404
            
            params = request.json
            if not params:
                return jsonify({"error": "Request body is required"}), 400
            
            remote_file = params.get("remote_file")
            method = params.get("method", "base64")
            
            if not remote_file:
                return jsonify({"error": "remote_file parameter is required"}), 400
            
            shell_manager = active_sessions[session_id]
            result = shell_manager.download_content(remote_file, method)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in download content endpoint: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    # File operations
    @app.route("/api/kali/upload", methods=["POST"])
    def upload_to_kali():
        try:
            params = request.json
            if not params:
                return jsonify({"error": "Request body is required"}), 400
            
            content = params.get("content")
            remote_path = params.get("remote_path")
            
            if not content or not remote_path:
                return jsonify({"error": "Content and remote_path are required"}), 400
            
            result = upload_content(content, remote_path)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in upload to Kali: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/kali/download", methods=["POST"])
    def download_from_kali():
        try:
            params = request.json
            if not params:
                return jsonify({"error": "Request body is required"}), 400
            
            remote_file = params.get("remote_file")
            
            if not remote_file:
                return jsonify({"error": "remote_file parameter is required"}), 400
            
            result = download_content(remote_file)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in download from Kali: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/target/upload_file", methods=["POST"])
    def upload_file_to_target_endpoint():
        try:
            params = request.json
            if not params:
                return jsonify({"error": "Request body is required"}), 400
            
            session_id = params.get("session_id")
            local_file = params.get("local_file")
            remote_file = params.get("remote_file")
            method = params.get("method", "base64")
            
            if not all([session_id, local_file, remote_file]):
                return jsonify({"error": "session_id, local_file, and remote_file are required"}), 400
            
            if session_id not in active_sessions:
                return jsonify({"error": f"Session {session_id} not found"}), 404
            
            shell_manager = active_sessions[session_id]
            # Read the local file content and upload via shell manager
            if not os.path.exists(local_file):
                result = {"error": f"Local file not found: {local_file}", "success": False}
            else:
                with open(local_file, "rb") as f:
                    file_content = f.read()
                content_b64 = base64.b64encode(file_content).decode('ascii')
                result = shell_manager.upload_content(content_b64, remote_file, "base64")
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in upload file to target: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/target/upload_content", methods=["POST"])
    def upload_content_to_target_endpoint():
        try:
            params = request.json
            if not params:
                return jsonify({"error": "Request body is required"}), 400
            
            session_id = params.get("session_id")
            content = params.get("content")
            remote_file = params.get("remote_file")
            method = params.get("method", "base64")
            encoding = params.get("encoding", "utf-8")
            
            if not all([session_id, content, remote_file]):
                return jsonify({"error": "session_id, content, and remote_file are required"}), 400
            
            if session_id not in active_sessions:
                return jsonify({"error": f"Session {session_id} not found"}), 404
            
            shell_manager = active_sessions[session_id]
            result = shell_manager.upload_content(content, remote_file, encoding)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in upload content to target: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/target/download_file", methods=["POST"])
    def download_file_from_target_endpoint():
        try:
            params = request.json
            if not params:
                return jsonify({"error": "Request body is required"}), 400
            
            session_id = params.get("session_id")
            remote_file = params.get("remote_file")
            local_file = params.get("local_file")
            method = params.get("method", "base64")
            
            if not all([session_id, remote_file, local_file]):
                return jsonify({"error": "session_id, remote_file, and local_file are required"}), 400
            
            if session_id not in active_sessions:
                return jsonify({"error": f"Session {session_id} not found"}), 404
            
            shell_manager = active_sessions[session_id]
            # Download via shell manager and save to local file
            result = shell_manager.download_content(remote_file, "base64")
            if result.get("success"):
                content_b64 = result.get("content", "")
                file_content = base64.b64decode(content_b64)
                os.makedirs(os.path.dirname(local_file), exist_ok=True)
                with open(local_file, "wb") as f:
                    f.write(file_content)
                result["local_file"] = local_file
                result["message"] = f"File downloaded successfully: {remote_file} -> {local_file}"
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in download file from target: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/target/download_content", methods=["POST"])
    def download_content_from_target_endpoint():
        try:
            params = request.json
            if not params:
                return jsonify({"error": "Request body is required"}), 400
            
            session_id = params.get("session_id")
            remote_file = params.get("remote_file")
            method = params.get("method", "base64")
            
            if not all([session_id, remote_file]):
                return jsonify({"error": "session_id and remote_file are required"}), 400
            
            if session_id not in active_sessions:
                return jsonify({"error": f"Session {session_id} not found"}), 404
            
            shell_manager = active_sessions[session_id]
            result = shell_manager.download_content(remote_file, "base64")
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in download content from target: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500


    @app.route("/api/tools/waybackurls", methods=["POST"])
    def waybackurls():
        try:
            params = request.json or {}
            result = run_waybackurls(params)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in waybackurls endpoint: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route("/api/tools/shodan", methods=["POST"])
    def shodan():
        try:
            params = request.json or {}
            result = run_shodan(params)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in shodan endpoint: {str(e)}")
            return jsonify({"error": f"Server error: {str(e)}"}), 500


    @app.route("/api/tools/subzy", methods=["POST"])
    def subzy():
        """Subzy subdomain takeover detection"""
        from tools.kali_tools import run_subzy
        data = request.get_json() or {}
        result = run_subzy(data)
        return jsonify(result)

    @app.route("/api/tools/assetfinder", methods=["POST"])
    def assetfinder():
        """Assetfinder subdomain discovery"""
        from tools.kali_tools import run_assetfinder
        data = request.get_json() or {}
        result = run_assetfinder(data)
        return jsonify(result)
    return app

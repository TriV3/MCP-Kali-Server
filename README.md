# MCP Kali Server

<!-- Badges -->
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Version: v0.2.1](https://img.shields.io/badge/version-v0.2.1-blue)


![MCP Kali Server Architecture](doc/MCP%20Kali%20Server.png)

A comprehensive Model Context Protocol (MCP) server for penetration testing and cybersecurity operations, providing seamless integration between Kali Linux tools and MCP-compatible clients.


## 🎥 Demo Video

**Automating Kali Linux with an MCP (Model Context Protocol) — HTB Demo**

In this video, I showcase how my MCP automates a Kali Linux workflow inside WSL2 and assists with solving a Hack The Box challenge — from enumeration to exploitation to auto-generated documentation.

[Watch the demo on YouTube](https://youtu.be/Wej1z-vfxz0)

---

## 🚀 Overview

This project provides a powerful MCP server that enables secure, programmatic access to Kali Linux penetration testing tools through a standardized interface. It includes advanced features like reverse shell management, SSH session handling, and comprehensive file operations with integrity verification.

## 🏗️ Architecture

This project is designed to work across different environments:

### 1. Kali Server (`kali-server/`)
**Runs on Kali Linux only** - The core server application that provides the actual penetration testing capabilities.

```
kali-server/
├── api/           # REST API routes and endpoints
├── core/          # Core functionality (SSH, reverse shells, config, Docker)
├── tools/         # Penetration testing tools integration
└── utils/         # Utility functions and file operations
```

**Features:**
- Docker test mode (`--test` option) - automatically manages test containers
- All penetration testing tools (nmap, gobuster, etc.)
- SSH and reverse shell session management
- File operations with integrity verification

### 2. MCP Server (`mcp-server/`)
**Can run on any system** - The Model Context Protocol server that provides a standardized interface for MCP clients.

```
mcp-server/
└── mcp_server.py  # MCP protocol implementation
```

**Note:** The MCP server communicates with the Kali server via HTTP, so they can be on different systems.

### Deployment Architecture

```
┌─────────────────┐    HTTP     ┌──────────────────┐    HTTP     ┌──────────────────┐
│   MCP Client    │ ◄─────────► │   MCP Server     │ ◄─────────► │   Kali Server    │
│  (Any system)   │             │  (Any system)    │             │  (Kali Linux)    │
└─────────────────┘             └──────────────────┘             │                  │
                                                                  │ ┌──────────────┐ │
                                                                  │ │   Docker     │ │
                                                                  │ │ (test mode)  │ │
                                                                  │ └──────────────┘ │
                                                                  └──────────────────┘
```

## ✨ Key Features

### 🔧 Penetration Testing Tools
- **Nmap**: Network discovery and security auditing
- **Gobuster**: Directory/file enumeration
- **Dirb**: Web content scanner
- **Nikto**: Web server scanner
- **Hydra**: Network logon cracker
- **SQLmap**: SQL injection testing
- **WPScan**: WordPress security scanner
- **John the Ripper**: Password cracking
- **Enum4linux**: SMB enumeration
- **Metasploit**: Exploitation framework

### 🐚 Advanced Session Management
- **SSH Session Manager**: Complete SSH session lifecycle management
  - `start_ssh_session`: Establish secure SSH connections
  - `execute_ssh_command`: Run commands in SSH sessions
  - `get_ssh_status`: Monitor SSH session status
  - `stop_ssh_session`: Cleanly terminate SSH sessions
  - `list_ssh_sessions`: View all active SSH sessions
- **Reverse Shell Manager**: Multi-session reverse shell handling
  - `start_reverse_shell_listener`: Start listening for reverse shells
  - `execute_shell_command`: Execute commands in reverse shells
  - `trigger_reverse_shell_action`: Non-blocking trigger execution for payloads
  - `get_shell_status`: Monitor reverse shell session status
  - `stop_reverse_shell`: Terminate reverse shell sessions
  - `list_reverse_shell_sessions`: View all active reverse shell sessions

### 📁 Comprehensive File Operations
- **Kali Server File Management**:
  - `upload_to_kali`: Upload files directly to Kali server
  - `download_from_kali`: Download files from Kali server
- **SSH File Transfer** (optimized for large files):
  - `ssh_upload_content`: Upload content via SSH with auto-optimization
  - `ssh_download_content`: Download content via SSH with chunking
  - `ssh_estimate_transfer_time`: Estimate transfer times and get recommendations
- **Reverse Shell File Transfer**:
  - `reverse_shell_upload_file`: Upload files via reverse shell
  - `reverse_shell_upload_content`: Upload content via reverse shell
  - `reverse_shell_download_file`: Download files via reverse shell
  - `reverse_shell_download_content`: Download content via reverse shell

### 🛠️ System Integration
- **Command Execution**: Direct command execution on Kali server
- **Health Monitoring**: Server health checks and status monitoring
- **Session Persistence**: Maintain multiple concurrent sessions

### 🔒 Security Features
- **Data Integrity**: SHA256 checksum verification for all file transfers
- **Secure Communications**: Encrypted SSH connections
- **Session Isolation**: Independent session management
- **Error Handling**: Comprehensive error detection and reporting

### 📊 Performance Optimization
- **Chunked Transfers**: Optimized for large file operations
- **Automatic Method Selection**: Smart selection based on file size
- **Background Processing**: Non-blocking operations for long-running tasks
- **Resource Management**: Efficient memory and CPU usage


## 🛠️ Installation

See [install.md](./install.md) for detailed installation instructions.

### MCP Client Configuration

After installation, configure your MCP client to connect to the Kali server:

📖 **[Configuration Guide](./CONFIG.md)**

This guide covers:
- Setting up `.claude/mcp_settings.json` for Claude Desktop
- Configuring alternative MCP clients
- Finding your Python path and Kali IP address
- Platform-specific examples (Windows, Linux, macOS)

### WSL Network Configuration

If you're running Kali Linux in WSL 2, proper network configuration is **critical** for the MCP server to function. See our comprehensive guide:

📖 **[WSL Network Configuration Guide](./doc/WSL_NETWORK_CONFIGURATION.md)**

This guide covers:
- Essential WSL configuration (`wsl.conf`)
- DNS resolution setup for Kali tools
- **Critical**: Understanding WSL 2 localhost behavior (Windows → Kali communication)
- Network testing and troubleshooting

⚠️ **Important**: The MCP client on Windows **must** be able to access the Kali server via `localhost`. Review this guide before running the server.

### Dependency Split
This project now separates Python dependencies for the two runtime components:
- `requirements.kali.txt` – Only what the Kali API server Python code needs (Flask, etc.)
- `requirements.mcp.txt` – Dependencies for the MCP server client interface (`requests`, FastMCP, test libs)
- `requirements.txt` – Informational file describing the split; contains no direct packages now.

Install on each machine as appropriate:
```
pip install -r requirements.kali.txt   # On Kali host running kali-server/
pip install -r requirements.mcp.txt    # On host running mcp-server/
```

## ⚠️ Security Warning

**IMPORTANT**: Be extremely cautious when running the Kali server with `sudo` privileges:

```bash
# ⚠️ DANGEROUS - Avoid if possible
sudo python kali_server.py
```

**Why this is risky:**
- The entire server runs with root privileges
- All API endpoints and commands execute with full system access
- Any compromise of the server grants complete root access to the system
- No privilege separation or access control

**Safer alternatives:**
- Run the server as a regular user (many tools work without root)
- Use specific sudo permissions only for commands that require them
- Consider containerization or virtualization for isolation
- Implement privilege escalation only when absolutely necessary

**For production environments**: Please see `TODO.md` for planned security enhancements including granular privilege management and access controls.


## 📖 Usage

See [usage.md](./usage.md) for detailed usage instructions and examples.

## 🧪 Testing

The project includes comprehensive test suites using Docker containers for isolated testing environments.

### Run All Tests
```bash
cd tests
./run_all.bat  # Windows
# or
chmod +x run_all.sh && ./run_all.sh  # Linux
```

### Docker Testing Environment
```bash
cd tests/docker
docker-compose up -d --build
python test_config_docker.py
```

### SSH Manager Tests
```bash
cd tests/kali
python -m pytest test_ssh_manager.py -v
```

### Test Configuration
Tests use Docker containers for consistent and isolated testing environments. The configuration is automatically set up in:
- `tests/kali/test_config.py` - Main test configuration (Docker-based)
- `tests/docker/test_config_docker.py` - Docker-specific test configuration

## 📋 Available MCP Tools

The MCP server provides the following tools:

| Tool | Description |
|------|-------------|
| `mcp_kali_mcp_nmap_scan` | Network scanning and enumeration |
| `mcp_kali_mcp_gobuster_scan` | Directory and file enumeration |
| `mcp_kali_mcp_hydra_attack` | Password brute forcing |
| `mcp_kali_mcp_start_ssh_session` | SSH session management |
| `mcp_kali_mcp_execute_ssh_command` | SSH command execution |
| `mcp_kali_mcp_ssh_upload_content` | File upload via SSH |
| `mcp_kali_mcp_ssh_download_content` | File download via SSH |
| `mcp_kali_mcp_start_reverse_shell_listener` | Reverse shell management |
| `mcp_kali_mcp_generate_reverse_shell_payload` | Payload generation |

## 🔍 File Operations

### Upload with Integrity Verification
```python
# The system automatically verifies file integrity using SHA256 checksums
upload_result = {
    "success": True,
    "source_checksum": "abc123...",
    "remote_checksum": "abc123...",
    "checksum_verified": True,
    "integrity_check": "PASSED"
}
```

### Download with Integrity Verification
```python
# All downloads include automatic integrity verification
download_result = {
    "success": True,
    "remote_checksum": "def456...",
    "local_checksum": "def456...",
    "checksum_verified": True,
    "integrity_check": "PASSED"
}
```

## 🚨 Security Considerations

- **Testing Environment**: All tests use isolated Docker containers for security
- **Network Security**: Ensure proper firewall configuration
- **Authentication**: Use strong passwords and key-based authentication
- **Session Management**: Regularly clean up unused sessions
- **File Permissions**: Set appropriate file permissions on uploaded files
- **Logging**: Monitor all activities through comprehensive logging

## 🐛 Troubleshooting

### Common Issues

1. **Connection Refused**
   ```bash
   # Check if server is running
   curl http://localhost:5000/health
   ```

2. **SSH Connection Failed**
   ```bash
   # Verify SSH connectivity
   ssh user@target-host
   ```

3. **Tool Not Found**
   ```bash
   # Install missing tools
   sudo apt update && sudo apt install nmap gobuster
   ```

4. **Docker Test Mode Issues**
   
   If you encounter Docker-related errors when using `--test` mode **on Kali Linux**:
   
   **Common Docker fixes on Kali Linux:**
   ```bash
   # Install Docker
   sudo apt update && sudo apt install docker.io
   
   # Start Docker service
   sudo systemctl start docker
   sudo systemctl enable docker
   
   # Add user to docker group (then logout/login)
   sudo usermod -aG docker $USER
   
   # Test Docker access
   docker --version
   docker ps
   ```
   
   **If Docker commands work manually but fail in test mode:**
   - The issue might be PATH-related in the Python environment
   - Try running with sudo: `sudo python kali_server.py --test`
   - Check Docker socket permissions: `ls -la /var/run/docker.sock`
   - Ensure you're running this on Kali Linux, not Windows

### Debug Mode
Enable debug logging:
```bash
# For the server
python kali_server.py --test --debug

# For Python logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Follow the coding standards (English comments, proper naming)
4. Add comprehensive tests
5. Update documentation
6. Submit a pull request

### Coding Standards
- All code, variables, and functions must be in English
- All comments and documentation must be in clear English
- Follow standard naming conventions
- Add tests for new features or bug fixes
- Update README and documentation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Original Project**: This project is initially a fork of [MCP-Kali-Server](https://github.com/Wh0am123/MCP-Kali-Server) but has been completely rewritten and restructured
- [Kali Linux](https://www.kali.org/) for the comprehensive penetration testing platform
- [Model Context Protocol](https://modelcontextprotocol.io/) for the standardized interface
- The cybersecurity community for continuous tool development

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/TriV3/MCP-Kali-Server/issues)
- **Documentation**: [Wiki](https://github.com/TriV3/MCP-Kali-Server/wiki)

---

**⚠️ Disclaimer**: This tool is designed for authorized penetration testing and security research only. Users are responsible for complying with applicable laws and regulations.

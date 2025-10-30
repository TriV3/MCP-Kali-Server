# Configuration Guide

This guide explains how to set up the MCP client configuration files for your environment.

## Quick Setup

### For Claude Desktop / Claude Code

1. **Copy the example file**:
   ```bash
   cp .claude/mcp_settings.json.example .claude/mcp_settings.json
   ```

2. **Edit `.claude/mcp_settings.json`** and replace:
   - `python` → Full path to your Python executable
   - `/path/to/your/MCP-Kali-Server/` → Your actual project path
   - `YOUR_KALI_IP` → Your Kali Linux IP address (e.g., `192.168.1.100`)

   **Windows Example**:
   ```json
   {
     "mcpServers": {
       "kali-mcp-server": {
         "command": "C:\\Users\\YourName\\AppData\\Local\\Programs\\Python\\Python312\\python.exe",
         "args": [
           "C:\\Users\\YourName\\Projects\\MCP-Kali-Server\\mcp-server\\mcp_server.py",
           "--server",
           "http://192.168.1.100:5000"
         ],
         "env": {
           "KALI_SERVER_URL": "http://192.168.1.100:5000"
         }
       }
     }
   }
   ```

   **Linux/macOS Example**:
   ```json
   {
     "mcpServers": {
       "kali-mcp-server": {
         "command": "/usr/bin/python3",
         "args": [
           "/home/username/MCP-Kali-Server/mcp-server/mcp_server.py",
           "--server",
           "http://192.168.1.100:5000"
         ],
         "env": {
           "KALI_SERVER_URL": "http://192.168.1.100:5000"
         }
       }
     }
   }
   ```

### For Other MCP Clients

1. **Copy the example file**:
   ```bash
   cp kali-mcp-config.json.example kali-mcp-config.json
   ```

2. **Edit `kali-mcp-config.json`** following the same pattern as above.

## Finding Your Values

### Python Path

**Windows**:
```cmd
where python
```

**Linux/macOS**:
```bash
which python3
```

### Kali Linux IP Address

**On your Kali machine**:
```bash
# Get recommended IP
curl -s http://localhost:5000/api/system/network-info | python -m json.tool | grep recommended_ip

# Or manually
ip addr show
```

### Project Path

Use the full absolute path to where you cloned this repository.

## Configuration Files

| File | Purpose | Commit to Git? |
|------|---------|----------------|
| `.claude/mcp_settings.json` | Your local MCP config for Claude Desktop | ❌ NO (in .gitignore) |
| `.claude/mcp_settings.json.example` | Template for others | ✅ YES |
| `kali-mcp-config.json` | Your local MCP config (alternative) | ❌ NO (in .gitignore) |
| `kali-mcp-config.json.example` | Template for others | ✅ YES |

## Troubleshooting

### "Command not found" Error

- Check that your Python path is correct
- On Windows, use double backslashes: `C:\\Users\\...`
- Verify Python is installed: `python --version`

### "Cannot connect to Kali server" Error

1. Verify Kali server is running:
   ```bash
   curl http://YOUR_KALI_IP:5000/health
   ```

2. Check firewall settings
3. Verify the IP address is correct
4. If using WSL, review [WSL_NETWORK_CONFIGURATION.md](./doc/WSL_NETWORK_CONFIGURATION.md)

## Security Notes

⚠️ **Never commit these files to Git**:
- `.claude/mcp_settings.json`
- `kali-mcp-config.json`
- `.mcp.json`

They contain:
- Your personal file paths
- Internal network IP addresses
- Machine-specific configurations

These files are automatically excluded via [.gitignore](./.gitignore).
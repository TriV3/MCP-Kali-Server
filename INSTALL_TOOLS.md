# Tool Installation Guide

This guide covers installing the reconnaissance and security tools used by MCP-Kali-Server that aren't included in a default Kali Linux installation.

## Prerequisites

Make sure Go is installed and configured:

```bash
# Check if Go is installed
go version

# If not installed
sudo apt update && sudo apt install -y golang

# Add Go bin to PATH (add to ~/.bashrc or ~/.zshrc)
export PATH=$PATH:$(go env GOPATH)/bin
```

## Go-Based Tools

These tools are written in Go and installed via `go install`:

### Subfinder (Subdomain Discovery)

```bash
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
```

### httpx (HTTP Probing)

```bash
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
```

### Nuclei (Vulnerability Scanner)

```bash
go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest

# Update templates
nuclei -update-templates
```

### Subzy (Subdomain Takeover Detection)

```bash
go install -v github.com/PentestPad/subzy@latest
```

### Assetfinder (Asset Discovery)

```bash
go install -v github.com/tomnomnom/assetfinder@latest
```

### Waybackurls (Historical URL Discovery)

```bash
go install -v github.com/tomnomnom/waybackurls@latest
```

### ffuf (Web Fuzzer)

Usually pre-installed on Kali, but if missing:

```bash
go install -v github.com/ffuf/ffuf/v2@latest
```

## Python-Based Tools

### Arjun (Parameter Discovery)

```bash
pip3 install arjun
```

## Manual Installation

### byp4xx (403 Bypass)

```bash
cd /home/kali
git clone https://github.com/lobuhi/byp4xx.git
chmod +x byp4xx/byp4xx
```

The tool expects byp4xx at `/home/kali/byp4xx/byp4xx`. Adjust the path in `kali_tools.py` if you install it elsewhere.

## Tools Included in Kali by Default

These tools should already be available:

- nmap
- gobuster
- dirb
- nikto
- sqlmap
- metasploit-framework
- hydra
- john
- wpscan
- enum4linux
- searchsploit (part of exploitdb)

If any are missing:

```bash
sudo apt update
sudo apt install -y nmap gobuster dirb nikto sqlmap metasploit-framework hydra john wpscan enum4linux exploitdb
```

## Verifying Installation

Quick check to confirm tools are accessible:

```bash
# Go tools (should be in PATH after installation)
subfinder -version
httpx -version
nuclei -version
subzy --help
assetfinder --help
waybackurls --help
ffuf -V

# Python tools
arjun --help

# Manual tools
/home/kali/byp4xx/byp4xx --help
```

## Troubleshooting

### Go tools not found after installation

Make sure your Go bin directory is in PATH:

```bash
echo 'export PATH=$PATH:$(go env GOPATH)/bin' >> ~/.bashrc
source ~/.bashrc
```

### Permission denied errors

Don't run Go install commands with sudo. Install as your regular user.

### Old tool versions

Update to latest:

```bash
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
# Repeat for other tools as needed
```

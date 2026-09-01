# User Scanner

<p align="center">
  <img src="https://github.com/user-attachments/assets/49ec8d24-665b-4115-8525-01a8d0ca2ef4" alt="User Scanner Logo" width="600" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Version-1.5.1.1-blueviolet?style=for-the-badge&logo=github" />
  <img src="https://img.shields.io/github/issues/kaifcodec/user-scanner?style=for-the-badge&logo=github" />
  <img src="https://img.shields.io/badge/Tested%20on-Termux-black?style=for-the-badge&logo=termux" />
  <img src="https://img.shields.io/badge/Tested%20on-Windows-cyan?style=for-the-badge&logo=Windows" />
  <img src="https://img.shields.io/badge/Tested%20on-Linux-black?style=for-the-badge&logo=Linux" />
  <img src="https://img.shields.io/pepy/dt/user-scanner?style=for-the-badge" />
  <a href="https://discord.gg/tVNrKVXb49" target="_blank">
     <img src="https://img.shields.io/badge/Discord-Join%20Chat-7289da?style=for-the-badge&logo=discord&logoColor=white" alt="Discord" />
  </a>
</p>

<p align="center">
  <a href="https://trendshift.io/repositories/16556" target="_blank">
    <img src="https://trendshift.io/api/badge/repositories/16556" alt="kaifcodec%2Fuser-scanner | Trendshift" width="250" height="55"/>
  </a>
</p>

---

A powerful **2-in-1 OSINT suite** engineered for deep **Email and Username Intelligence**.

With **465+ total scan vectors**—including **175+ email-integrated sites** and **290+ username platforms**—you can map digital footprints, analyze target behavior, uncover interests, full metadata of usernames and verify account registrations in seconds.

---

## 💖 Sponsored by

<p align="center">
  <a href="https://webvetted.com/user-scanner?ref=github&utm_source=github" target="_blank">
    <img width="800" height="250" alt="WebVetted Sponsor Banner" src="https://github.com/user-attachments/assets/a18398f5-193e-4659-87d6-ccdbf6d4d4c2" />
  </a>
  <br>
  <em><strong>Go beyond account enumeration.</strong> WebVetted turns an email or username into a complete identity investigation with deep OSINT enrichment, breach intel, AI analysis, and an interactive identity graph.</em>
  <br>
  <a href="https://webvetted.com/user-scanner?ref=github&utm_source=github" target="_blank"><strong>Start an Investigation →</strong></a>
</p>

---

<p align="center">
  <a href="https://noimosiny.com/" target="_blank">
    <img width="750" style="max-width: 100%; height: auto;" alt="banner-github" src="https://github.com/user-attachments/assets/05ca5b27-f9b4-4385-b0cf-768fbad05c39" />
  </a>
  <br>
  <em><strong>Comprehensive OSINT platform for professional investigators and analysts.</strong> Reverse email, phone number, and username search across 250+ modules. Automate your intelligence gathering with our powerful tools.</em>
  <br>
  <a href="https://noimosiny.com/" target="_blank"><strong>Get Started →</strong></a>
</p>

---

<p align="center">
  <a href="https://goodfirstissues.org/?ref=user-scanner&utm_source=github&utm_medium=banner&utm_campaign=user-scanner" target="_blank">
    <img width="750" style="max-width: 100%; height: auto;" alt="banner-github" src="https://github.com/user-attachments/assets/dafc6cbd-22e9-4294-a2c2-473f59f389bc" />
  </a>
  <br>
  <em><strong>Find beginner-friendly open-source issues and make your first pull request today.</strong></em>
  <br>
  <a href="https://goodfirstissues.org/?ref=user-scanner&utm_source=github&utm_medium=banner&utm_campaign=user-scanner" target="_blank"><strong>Get Started →</strong></a>
</p>

---

## ✨ Key Features

- 🔎 **Deep Email & Username OSINT:** Look up email registrations and perform advanced username profiling across 465+ platforms.
- 👤 **Rich Metadata Scraping:** Scrapes avatars, bio descriptions, follower counts, UID numbers, seller statuses, and account attributes.
- 🔀 **Cross-Scan & Pivot Engine:** Mines handles, profile links, and exposed email addresses from initial scans, automatically pivoting across secondary target vectors.
- 🤖 **Model Context Protocol (MCP) Server:** Native AI agent integration for Claude Desktop, Cursor, Antigravity, and LLMs to run autonomous OSINT scans and recursive pivots.
- 🛡️ **Hudson Rock Infostealer Breach Intel:** Query infostealer malware breach logs using the `--hudson` flag for high-priority target correlation.
- ⚡ **High-Throughput Parallel Engine:** Powered by `httpx` and `curl_cffi` for maximum concurrency with automated TLS fingerprint impersonation.
- 🔀 **Permutation & Alias Generator:** Wildcard-based username variation generation to catch typosquatting or alternative aliases.
- 📂 **Multi-Format Reports:** Automated exports to **PDF** (with profile photos), **JSON**, and **CSV** for pipeline integration.
- 🌐 **Advanced Proxy Pivoting:** Built-in proxy rotation with protocol auto-detection (`http`, `socks5`) and pre-scan health validation (`--validate-proxies`).
- 🎨 **Responsive Terminal UI:** Dynamic progress tracking, self-adaptive category grids (`-lu`/`-le`), and clear status reporting.

---

## 🚀 Installation

### 🐍 Via PyPI (Recommended)

```bash
# Upgrade pip and install user-scanner
python3 -m pip install --upgrade pip
pip install user-scanner

# Optional: Install with MCP Server support for AI agents
pip install "user-scanner[mcp]"
```

### 📦 Virtual Environment Setup

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\Activate.ps1

# Install package
pip install user-scanner
```

### ❄️ Via Nix (Linux & macOS)

```bash
# Run instantly without installing permanently
nix run github:kaifcodec/user-scanner/main -- --help

# Drop into a temporary shell with user-scanner active
nix shell github:kaifcodec/user-scanner/main
```

---

## 💻 Usage Guide

### 1. Basic Username & Email Scanning

Scan a single username or email address across all available platform modules:

```bash
user-scanner -u johndoe             # Single username scan
user-scanner -e johndoe@gmail.com   # Single email scan
```

### 2. Cross-Scan & Pivot Intelligence

An email scan proves an account exists but rarely reveals a handle. `--cross-scan` mines exposed handles, profile links, and secondary email addresses from target profiles, pivoting into multi-pass reconnaissance across all matching platforms:

| Pivot Direction | What it Mines |
| :--- | :--- |
| `-e` → **username** | Handles or social links exposed on an email's registered profile |
| `-u` → **username** | Secondary aliases advertised across target social profiles |
| `-u` → **email** | Public email addresses published on target profile pages |
| `-e` → **email** | Secondary addresses exposed by initial email profiles |

```bash
user-scanner -u johndoe --cross-scan                                  # Pivot from username scan
user-scanner -e johndoe@gmail.com --cross-scan                        # Pivot from email scan
user-scanner -e johndoe@gmail.com --cross-scan --cross-links verified # Platform-verified links only
user-scanner -u johndoe --cross-scan --cross-depth 2        # Follow links two hops deep
```

> 💡 *For confidence scoring, link classification rules, and cost models, see **[docs/CROSS_SCAN.md](docs/CROSS_SCAN.md)**.*

### 3. Hudson Rock Malware Breach Intelligence

Check if a target username or email address has been exposed in **infostealer malware infection logs**:

```bash
user-scanner -u johndoe --hudson             # Username malware log check
user-scanner -e johndoe@gmail.com --hudson   # Email malware log check
```

> 🖼️ *To view output terminal screenshots and visual previews, see **[docs/EXAMPLES.md](docs/EXAMPLES.md)**.*

### 4. Targeted Category & Module Scanning

Scan specific categories or individual modules, or list available modules in a responsive grid:

```bash
user-scanner -u johndoe -c dev                # Developer platforms only
user-scanner -e johndoe@gmail.com -m github   # Single module check
user-scanner -u johndoe -m github,instagram   # Specific comma-separated modules

user-scanner -lu                              # List user categories & modules grid
user-scanner -le                              # List email categories & modules grid
```

### 5. Bulk File Scanning

Scan multiple targets from an input file (one target per line):

```bash
user-scanner -uf usernames.txt   # Bulk username scan
user-scanner -ef emails.txt      # Bulk email scan
```

### 6. Report Exports, Options & Proxies

```bash
# Export results to PDF, JSON, or CSV
user-scanner -u johndoe -f pdf -o report.pdf
user-scanner -u johndoe -f json -o results.json

# Verbose URL reporting and show all results (including not found)
user-scanner -u johndoe -v --all

# Rotate proxies with pre-scan validation check
user-scanner -u johndoe -P proxies.txt --validate-proxies
```

### 7. AI & LLM Agent Integration (MCP Server)

Connect `user-scanner` directly to AI coding assistants and LLM platforms via the **Model Context Protocol (MCP)**. This enables AI agents (Claude Desktop, Cursor, Antigravity, Open-WebUI) to autonomously investigate handles and emails, pivot on exposed profiles, and analyze digital footprints.

#### Starting the Server

```bash
# Start the MCP server over standard I/O (stdio)
user-scanner-mcp

# Optional: Enable verbose logging to stderr
user-scanner-mcp -v
```

#### MCP Client Configuration

Add `user-scanner` to your client configuration (e.g. `claude_desktop_config.json` or `mcp_config.json`):

```json
{
  "mcpServers": {
    "user-scanner": {
      "command": "user-scanner-mcp"
    }
  }
}
```

#### Exposed AI Tools

| Tool | Description | Capabilities |
| :--- | :--- | :--- |
| `scan_username` | Deep username OSINT & profile enrichment across platforms | Targeted scans (`category`, `module`), recursive `cross_scan`, proxy injection, loudness toggles |
| `scan_email` | Deep email verification & account discovery across platforms | Target scoping, automated link pivoting (`cross_scan`), custom proxies, loudness toggles |
| `list_available_modules` | Dynamic catalog & module discovery | Allows AI agents to query all supported platforms and categories dynamically |

---

## 📚 Documentation Hub

Explore detailed documentation guides in the [`docs/`](docs/) directory:

- 📋 **[CLI Flags Reference](docs/FLAGS.md)** — Complete breakdown of every CLI flag and option.
- 🔀 **[Cross-Scan & Pivoting Guide](docs/CROSS_SCAN.md)** — In-depth guide to multi-pass cross-scan reconnaissance.
- 🔀 **[Pattern Syntax Guide](docs/PATTERNS.md)** — Wildcard and permutation patterns for username generation.
- 🐍 **[Library Mode Guide](docs/USAGE.md)** — Calling the Python engine programmatically from your own scripts.
- 🌐 **[Proxy & Network Guide](docs/PROXIES.md)** — Proxy rotation formats, health checks, and regional VPN troubleshooting.
- 🖼️ **[Media & Output Gallery](docs/EXAMPLES.md)** — Video demonstrations, terminal recordings, and screenshot previews.

---

## 🐍 Python Library Mode

Integrate the User Scanner engine directly into your Python scripts:

```python
import asyncio
from user_scanner.core import engine
from user_scanner.email_scan.shopping import etsy

async def main():
    # Engine validates target against module and returns Result object
    result = await engine.check(etsy, "test@gmail.com")
    print(result.to_json())

asyncio.run(main())
```

> 💡 *For complete Python API documentation and batch category checking examples, see **[docs/USAGE.md](docs/USAGE.md)**.*

---

## 💖 Support the Project

Web platforms constantly update authentication flows. Maintaining over 465+ scan modules requires around-the-clock commitment to keep the suite reliable and free for the cybersecurity community.

If `user-scanner` has saved you hours of manual pivoting or aided your investigations, consider supporting the project:

👉 **[Sponsor on GitHub](https://github.com/sponsors/kaifcodec)**

### Project Sponsors

Huge thanks to our amazing sponsors who support the ongoing development of `user-scanner`!

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/soxoj">
        <img src="https://github.com/soxoj.png?size=100" width="50px;" alt="soxoj"/>
        <br />
        <sub><b>@soxoj</b></sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/hienyimba">
        <img src="https://github.com/hienyimba.png?size=100" width="50px;" alt="hienyimba"/>
        <br />
        <sub><b>@hienyimba</b></sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/InDieTasten">
        <img src="https://github.com/InDieTasten.png?size=100" width="50px;" alt="InDieTasten"/>
        <br />
        <sub><b>@InDieTasten</b></sub>
      </a>
    </td>
  </tr>
</table>

---

## 📜 Contributing

We welcome community contributions! Please read our **[Contributing Guidelines](CONTRIBUTING.md)** before opening a PR or submitting new scan modules.

---

## ⚠️ Disclaimer

This tool is provided strictly for **educational purposes**, **authorized security research**, and **defensive OSINT investigations**. The developers assume no liability and are not responsible for any misuse, unintended consequences, or legal actions resulting from the deployment of this software.

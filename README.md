# User Scanner

![User Scanner Logo](https://github.com/user-attachments/assets/49ec8d24-665b-4115-8525-01a8d0ca2ef4)
<p align="center">
  <img src="https://img.shields.io/badge/Version-1.2.0.3-blueviolet?style=for-the-badge&logo=github" />
  <img src="https://img.shields.io/github/issues/kaifcodec/user-scanner?style=for-the-badge&logo=github" />
  <img src="https://img.shields.io/badge/Tested%20on-Termux-black?style=for-the-badge&logo=termux" />
  <img src="https://img.shields.io/badge/Tested%20on-Windows-cyan?style=for-the-badge&logo=Windows" />
  <img src="https://img.shields.io/badge/Tested%20on-Linux-balck?style=for-the-badge&logo=Linux" />
  <img src="https://img.shields.io/pypi/dm/user-scanner?style=for-the-badge" />
</p>

---

A powerful *Email OSINT tool* that checks if a specific email is registered on various sites, combined with *username scanning* for branding or OSINT — 2-in-1 tool.  

Perfect for fast, accurate and lightweight email OSINT

Perfect for finding a **unique username** across GitHub, Twitter, Reddit, Instagram, and more, all in a single command.  

## Features

- ✅ Email & username OSINT: check email registrations and username availability across social, developer, creator, and other platforms  
- ✅ Dual-mode usage: works as an email scanner, username scanner, or username-only tool  
- ✅ Clear results: `Registered` / `Not Registered` for emails and `Available` / `Taken` / `Error` for usernames with precise failure reasons  
- ✅ Fully modular architecture for easy addition of new platform modules  
- ✅ Bulk scanning support for usernames and emails via input files  
- ✅ Wildcard-based username permutations with automatic variation generation  
- ✅ Multiple output formats: console, **JSON**, and **CSV**, with file export support  
- ✅ Proxy support with rotation and pre-scan proxy validation  
- ✅ Smart auto-update system with interactive upgrade prompts via PyPI  

## Virtual Environment (optional but recommended)

```bash
# create venv
python -m venv .venv
````
## Activate venv
```bash
# Linux / macOS
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```
## Installation
```bash
# upgrade pip
python -m pip install --upgrade pip

# install
pip install user-scanner
```
---

## Important Flags

| Flag | Description |
|------|-------------|
| `-u, --username USERNAME` | Scan a single username across platforms |
| `-e, --email EMAIL`       | Scan a single email across platforms |
| `-uf, --username-file FILE` | Scan multiple usernames from file (one per line) |
| `-ef, --email-file FILE`  | Scan multiple emails from file (one per line) |
| `-c, --category CATEGORY` | Scan all platforms in a specific category |
| `-lu, --list-user` | List all available modules for username scanning |
| `-le, --list-email` | List all available modules for email scanning |
| `-m, --module MODULE`     | Scan a single specific module |
| `-p, --permute PERMUTE`   | Generate username permutations using a pattern/suffix |
| `-P, --proxy-file FILE`   | Use proxies from file (one per line) |
| `--validate-proxies`      | Validate proxies before scanning (tests against google.com) |
| `-s, --stop STOP`         | Limit the number of permutations generated |
| `-d, --delay DELAY`       | Delay (in seconds) between requests |
| `-f, --format {csv,json}` | Select output format |
| `-o, --output OUTPUT`     | Save results to a file |

---

## Usage

### Basic username/email scan

Scan a single email or username across **all** available modules/platforms:

```bash
user-scanner -e john_doe@gmail.com   # single email scanning 
user-scanner -u john_doe             # single username scanning 
```

### Selective scanning

Scan only specific categories or single modules:

```bash
user-scanner -u john_doe -c dev # developer platforms only
user-scanner -u john_doe -m github # only GitHub
```

### Bulk email/username scanning

Scan multiple emails/usernames from a file (one email/username per line):
- Can also be combined with categories or modules using `-c` , `-m` and other flags

```bash
user-scanner -ef emails.txt     # bulk email scan
user-scanner -uf usernames.txt  # bulk username scan
```
---
### Library mode for email_scan
Only available for `user-scanner>=1.2.0`

For full usage (eg. category checks, full scan) guide [click here](https://github.com/kaifcodec/user-scanner/blob/main/USAGE.md)

- Email scan example (single module):
```python
import asyncio
from user_scanner.core import engine
from user_scanner.email_scan.dev import github

async def main():
    # Engine detects 'email_scan' path -> returns "Registered" status
    result = await engine.check(github, "test@gmail.com")
    json_data = result.to_json() # returns JSON output
    csv_data = result.to_csv()   # returns CSV output

asyncio.run(main())

```
---

### Username/Email variations (suffix only)

Generate & check username variations using a permutation from the given suffix:

```bash
user-scanner -u john_ -p ab # john_a, ..., john_ab, john_ba
```

### Using Proxies

Route requests through proxy servers:

```bash
user-scanner -u john_doe -P proxies.txt
```

Validate proxies before scanning (tests each proxy against google.com):

```bash
user-scanner -u john_doe -P proxies.txt --validate-proxies # recommended
```

This will:
1. Filter out non-working proxies
2. Save working proxies to `validated_proxies.txt`
3. Use only validated proxies for scanning

---

## Screenshots: 

- Note*: New modules are constantly getting added so screenshots might show only limited, outdated output:

<img width="1080" height="930" alt="1000146237" src="https://github.com/user-attachments/assets/3cbcecaf-3620-49be-9d0a-8f94790acdf0" />

---


<img width="1072" height="848" alt="user-scanner's main usage screenshot" src="https://github.com/user-attachments/assets/34e44ca6-e314-419e-9035-d951b493b47f" />

---

## ❤️ Support the project

If this project helps you, consider supporting its development:

**BTC (SegWit):** `bc1q0dzkuav8lq9lwu7gc457vwlda4utfcr5hpv7ka`


---
## Contributing

Modules are organized under `user_scanner/`:

```
user_scanner/
├── email_scan/       # Currently in development
│   ├── social/       # Social email scan modules (Instagram, Mastodon, X, etc.)
|   ├── adult/        # Adult sites 
|    ...               # New sites to be added soon
├── user_scan/
│   ├── dev/          # Developer platforms (GitHub, GitLab, npm, etc.)
│   ├── social/       # Social platforms (Twitter/X, Reddit, Instagram, Discord, etc.)
│   ├── creator/      # Creator platforms (Hashnode, Dev.to, Medium, Patreon, etc.)
│   ├── community/    # Community platforms (forums, StackOverflow, HackerNews, etc.)
│   ├── gaming/       # Gaming sites (chess.com, Lichess, Roblox, Minecraft, etc.)
    ...
```

**Module guidelines:**
This project contains small "validator" modules that check whether a username exists on a given platform. Each validator is a single function that returns a Result object (see `core/orchestrator.py`).

Result semantics:
- Result.available() → `available`
- Result.taken() → `taken`
- Result.error(message: Optional[str]) → `error`, blocked, unknown, or request failure (include short diagnostic message when helpful)

Follow this document when adding or updating validators.

See [CONTRIBUTING.md](CONTRIBUTING.md) for examples.

---

## Dependencies: 
- [httpx](https://pypi.org/project/httpx/)
- [colorama](https://pypi.org/project/colorama/)

---

## License

This project is licensed under the **MIT License**. See [LICENSE](LICENSE) for details.

---

## ⚠️ Disclaimer

This tool is provided for **educational purposes** and **authorized security research** only.

- **User Responsibility:** Users are solely responsible for ensuring their usage complies with all applicable laws and the Terms of Service (ToS) of any third-party providers.
- **Methodology:** The tool interacts only with **publicly accessible, unauthenticated web endpoints**. It does not bypass authentication, security controls, or access private user data.
- **No Profiling:** This software performs only basic **yes/no availability checks**. It does not collect, store, aggregate, or analyze user data, behavior, or identities.
- **Limitation of Liability:** The software is provided **“as is”**, without warranty of any kind. The developers assume no liability for misuse or any resulting damage or legal consequences.

---

## 🛠️ Troubleshooting

Some sites may return **403 Forbidden** or **connection timeout** errors, especially if they are blocked in your region (this is common with some adult sites).

- If a site is blocked in your region, use a VPN and select a region where you know the site is accessible.
- Then run the tool again.

These issues are caused by regional or network restrictions, not by the tool itself. If it still fails, report the error by opening an issue.

# User Scanner

![User Scanner Logo](https://github.com/user-attachments/assets/49ec8d24-665b-4115-8525-01a8d0ca2ef4)
<p align="center">
  <img src="https://img.shields.io/badge/Version-1.4.1.9-blueviolet?style=for-the-badge&logo=github" />
  <img src="https://img.shields.io/github/issues/kaifcodec/user-scanner?style=for-the-badge&logo=github" />
  <img src="https://img.shields.io/badge/Tested%20on-Termux-black?style=for-the-badge&logo=termux" />
  <img src="https://img.shields.io/badge/Tested%20on-Windows-cyan?style=for-the-badge&logo=Windows" />
  <img src="https://img.shields.io/badge/Tested%20on-Linux-black?style=for-the-badge&logo=Linux" />
  <img src="https://img.shields.io/pepy/dt/user-scanner?style=for-the-badge" />
  <a href="https://discord.gg/CDHhq3jfx" target="_blank">
     <img src="https://img.shields.io/badge/Discord-Join%20Chat-7289da?style=for-the-badge&logo=discord&logoColor=white"   alt="Discord" />
  </a>
</p>


<p align="center">
  <a href="https://trendshift.io/repositories/16556" target="_blank">
    <img src="https://trendshift.io/api/badge/repositories/16556" alt="kaifcodec%2Fuser-scanner | Trendshift" width="250" height="55"/>
  </a>
</p>

---
A powerful **2-in-1 OSINT suite** engineered for deep **Email and Username Intelligence**.

With **350+ total scan vectors**—including **140+ email-integrated sites** and **210+ username platforms**—you can map digital footprints, analyze target behavior, uncover interests, and verify account registrations in seconds.

The ultimate reconnaissance tool for hunting down targets using just an email or username—now fully integrated with **Hudson Rock** for instant data breach intelligence.

---
## Sponsored by
<p align="center">
  <a href="https://webvetted.com/user-scanner?ref=github&utm_source=github" target="_blank">
    <img width="850" height="270" alt="WebVetted Sponsor Banner" src="https://github.com/user-attachments/assets/a18398f5-193e-4659-87d6-ccdbf6d4d4c2" />
  </a>
  <br>
  <em><strong>Go beyond account enumeration.</strong> Webvetted turns an email or username into a complete identity investigation with deep OSINT enrichment, breach intel,  AI analysis, and an interactive identity graph.</em>
  <br>
  <a href="https://webvetted.com/user-scanner?ref=github&utm_source=github" target="_blank"><strong>Start an Investigation →</strong></a>
</p>

---

## User Scanner Features:

- ✅ **Deep Email & Username OSINT:** Look up email registrations and perform advanced username profiling across 350+ platforms.
- ✅ **Profile Data Extraction:** Goes beyond basic availability checks to scrape and extract rich metadata, account details, and digital footprints from target profiles.
- ✅ **Dual-Mode Engine:** Run targeted email campaigns, massive username sweeps, or simultaneous dual-identifier scans.
- ✅ **Granular Status Reporting:** Get crystal-clear results (`Registered`/`Available` for emails; `Found`/`Not Found`/`Error` for usernames) backed by precise exception handling.
- ✅ **Modular & Extensible:** Built on a highly decoupled, modular architecture, adding new platform modules takes just a few lines of code.
- ✅ **Mass Bulk Scanning:** High-throughput processing for bulk lists of usernames and emails via structured input files.
- ✅ **Permutation Generator:** Wildcard-based username variation generation to catch typosquatting or alternative aliases.
- ✅ **Multi-Format Export:** Clean console output paired with structured, automated exports to **JSON** and **CSV** for easy pipeline integration.
- ✅ **Advanced Proxy Rotation:** Built-in proxy pivoting with automated rotation and pre-scan health checks to bypass strict rate-limiting.
- ✅ **Smart Auto-Update System:** Keeps your signatures and modules fresh with interactive, seamless PyPI update prompts.

## Virtual Environment (optional but recommended)

```bash
# create venv
python3 -m venv .venv
````
## Activate venv
```bash
# Linux / macOS
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```
## Installation

#### 🐍 Via PyPI (Standard Python Setup)
```bash
# Upgrade pip to the latest version
python3 -m pip install --upgrade pip

# Install the package globally or in your virtual environment
pip install user-scanner
```

#### ❄️ Via Nix (Linux & macOS)

```bash
# Run the scanner instantly without installing anything permanently
nix run github:kaifcodec/user-scanner/main -- --help

# Drop into a temporary shell where the 'user-scanner' command is active
nix shell github:kaifcodec/user-scanner/main

# (For Developers) Clone the repo and drop into an isolated workspace
nix develop .
```

It is also [available](https://search.nixos.org/packages?channel=unstable&from=0&size=50&sort=relevance&type=packages&query=user-scanner)
available in Nixpkgs. Keep in mind that the lastest releases might only
be present in the `unstable` channel.

```bash
nix-env -iA nixos.user-scanner
```

---
### Important Flags

See [Important flags](docs/FLAGS.md) here and use the tool powerfully


## Usage

### Basic username/email scan

Scan a single email or username across **all** available modules/platforms:

```bash
user-scanner -e johndoe@gmail.com   # single email scanning 
user-scanner -u johndoe             # single username scanning 
```
### Verbose mode 

Use `-v` flag to show the url of the sites being checked
```bash
user-scanner -v -e johndoe@gmail.com -c dev
```
Output:
```sh
  ...
  [✔] Huggingface [https://huggingface.co] (johndoe@gmail.com): Registered
  [✔] Envato [https://account.envato.com] (johndoe@gmail.com): Registered
  [✔] Replit [https://replit.com] (johndoe@gmail.com): Registered
  [✔] Xda [https://xda-developers.com] (johndoe@gmail.com): Registered
  ...
```

### Selective scanning

Scan only specific categories or single modules:

```bash
user-scanner -u johndoe -c dev                # developer platforms only
user-scanner -e johndoe@gmail.com -m github   # only GitHub
```

### Bulk email/username scanning

Scan multiple emails/usernames from a file (one email/username per line):
- Can also be combined with categories or modules using `-c` , `-m` and other flags

```bash
user-scanner -ef emails.txt     # bulk email scan
user-scanner -uf usernames.txt  # bulk username scan
```

### Pattern generation
See [Pattern Syntax](docs/PATTERNS.md) for more details

---
### Library mode for email_scan
Only available for `user-scanner>=1.2.0`

See full usage (eg. category checks, full scan) guide [library usage](docs/USAGE.md)

- Email scan example (single module):

```python
import asyncio
from user_scanner.core import engine
from user_scanner.email_scan.shopping import etsy

async def main():
    # Engine detects 'email_scan' path -> returns "Registered" status
    result = await engine.check(etsy, "test@gmail.com")
    json_data = result.to_json() # returns JSON output
    csv_data = result.to_csv()   # returns CSV output
    print(json_data)             # prints the json data

asyncio.run(main())
```
Output:

```json
{
  "email": "test@gmail.com",
  "category": "Shopping",
  "site_name": "Etsy",
  "status": "Registered",
  "url": "https://www.etsy.com",
  "extra": {
    "id": 98832,
    "name": "test123",
    "username": "test123",
    "gender": "private",
    "is_seller": "No",
    "has_public_page": "No",
    "stats": "0 followers | 0 following | 0 favorites",
    "privacy": "Items are Public | Shops are Public",
    "joined": "2010-09-19 05:04:06",
    "last_profile_update": "2020-07-31 01:40:24",
    "avatar": "https://i.etsystatic.com/site-assets/images/avatars/default_avatar.png?width=400"
  },
  "reason": ""
}
```
---


### Using Proxies

Validate proxies before scanning (tests each proxy against google.com):

```bash
user-scanner -u johndoe -P proxies.txt --validate-proxies # recommended
```

This will:
1. Filter out non-working proxies
2. Save working proxies to `validated_proxies.txt`
3. Use only validated proxies for scanning
---
## 💖 Support the project

Web platforms constantly update their authentication flows, meaning keeping over 300 modules running smoothly requires a relentless, around-the-clock commitment to maintaining code. What started as a passion project has evolved into a demanding, highly technical undertaking to ensure the tool remains reliable for the community.

While commercial threat intelligence platforms often charge thousands of dollars for these exact capabilities, `user-scanner` remains completely free and open-source. 

​If this tool just saved you hours of manual pivoting, helped you score a bug bounty, or secured your company's footprint, consider supporting this project. Keep OSINT powerful, open, and free.

[GitHub Sponsor](https://github.com/sponsors/kaifcodec)

## Sponsors

Huge thanks to our amazing sponsors who support the development of `user-scanner`!

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
        <img src="https://github.com/hienyimba.png?size=100" width="50px;" alt="heynimba"/>
        <br />
        <sub><b>@hienyimba</b></sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/InDieTasten">
        <img src="https://github.com/InDieTasten.png?size=100" width="50px;" alt="heynimba"/>
        <br />
        <sub><b>@InDieTasten</b></sub>
      </a>
    </td>
  </tr>
</table>


---
### Screenshots:
**Note**: Screenshots might be outdated

---
<img width="2160" height="3760" alt="1000188339" src="https://github.com/user-attachments/assets/da7d73a5-2a50-4704-b71c-993fe5a17644" />


---

[user-scanner_u_usage.webm](https://github.com/user-attachments/assets/d901510c-880e-4395-8274-3494d984f2de)

---

- Use the `--hudson` flag to check if a **username** or **email** has been exposed in **infostealer malware logs**.

```bash
user-scanner -e johndoe@gmail.com --hudson   # for email check
user-scanner -u johndoe --hudson             # for username check
```
<img width="1080" height="844" alt="1000183041" src="https://github.com/user-attachments/assets/366d4697-b94b-40b2-9844-f936b6fcea7f" />

---
## Contributing

See detailed [Contributing guidelines](CONTRIBUTING.md)

---

## ⚠️ Disclaimer

This tool is provided strictly for **educational purposes**, **authorized security research**, and **defensive OSINT investigations**. 

- **User Responsibility:** The user assumes all responsibility for ensuring that their deployment and use of this software complies with all applicable local, national, and international laws, as well as the Terms of Service (ToS) of any scanned platforms.
- **Data Source & Methodology:** This tool acts exclusively as an aggregator of **publicly accessible information** and legitimate third-party threat intelligence APIs. It does not bypass authentication mechanisms, exploit security vulnerabilities, or access non-public private data.
- **Information Aggregation:** While this software extracts public metadata and references external breach intelligence feeds (e.g., Hudson Rock), the developers do not host, store, or maintain any underlying personal data. All data is processed locally on the user's machine in real-time.
- **Limitation of Liability:** This software is provided **"as is"**, without warranty of any kind, express or implied. The developers accept no liability and are not responsible for any misuse, unintended consequences, damage, or legal actions resulting from the use of this tool.
---

## 🛠️ Troubleshooting

Some sites may return **403 Forbidden** or **connection timeout** errors, especially if they are blocked in your region (this is common with some adult sites).

- If a site is blocked in your region, use a VPN and select a region where you know the site is accessible.
- Then run the tool again.

These issues are caused by regional or network restrictions, not by the tool itself. If it still fails, report the error by opening an issue.

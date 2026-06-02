# User Scanner

![User Scanner Logo](https://github.com/user-attachments/assets/49ec8d24-665b-4115-8525-01a8d0ca2ef4)
<p align="center">
  <img src="https://img.shields.io/badge/Version-1.3.6.8-blueviolet?style=for-the-badge&logo=github" />
  <img src="https://img.shields.io/github/issues/kaifcodec/user-scanner?style=for-the-badge&logo=github" />
  <img src="https://img.shields.io/badge/Tested%20on-Termux-black?style=for-the-badge&logo=termux" />
  <img src="https://img.shields.io/badge/Tested%20on-Windows-cyan?style=for-the-badge&logo=Windows" />
  <img src="https://img.shields.io/badge/Tested%20on-Linux-black?style=for-the-badge&logo=Linux" />
  <img src="https://img.shields.io/pypi/dm/user-scanner?style=for-the-badge" />
</p>

<p align="center">
  <a href="https://trendshift.io/repositories/16556" target="_blank">
    <img src="https://trendshift.io/api/badge/repositories/16556" alt="kaifcodec%2Fuser-scanner | Trendshift" width="250" height="55"/>
  </a>
</p>

---
A powerful **2-in-1 OSINT suite** combining deep **Email OSINT** with comprehensive **Username Scanning**. 

With **205+ total scan vectors**—including **100+ email-integrated sites** and **105+ username platforms**—you can identify digital footprints or verify account registrations in seconds.

The ultimate tool for finding a **unique username** across GitHub, X, Reddit, Instagram, and more in a single command.


## Features

- ✅ Email & username OSINT: check email registrations and username availability across social, developer, creator, and other platforms  
- ✅ Dual-mode usage: works as an email scanner, username scanner, or username-only tool  
- ✅ Clear results: `Registered` / `Not Registered` for emails and `Not Found` / `Found` / `Error` for usernames with precise failure reasons  
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
## Support the project

If this project helps you, consider supporting its development:
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
  </tr>
</table>

---
### Screenshots:
**Note**: Screenshots might be outdated

---
<img width="2160" height="3760" alt="1000188339" src="https://github.com/user-attachments/assets/da7d73a5-2a50-4704-b71c-993fe5a17644" />


---
<img width="1080" height="730" alt="1000175084" src="https://github.com/user-attachments/assets/b399b924-6c4a-4b5b-af0d-67f7c0b39436" />

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

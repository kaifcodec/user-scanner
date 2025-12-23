# User Scanner

![User Scanner Logo](https://github.com/user-attachments/assets/49ec8d24-665b-4115-8525-01a8d0ca2ef4)
<p align="center">
  <img src="https://img.shields.io/badge/Version-1.0.10.1-blueviolet?style=for-the-badge&logo=github" />
  <img src="https://img.shields.io/github/issues/kaifcodec/user-scanner?style=for-the-badge&logo=github" />
  <img src="https://img.shields.io/badge/Tested%20on-Termux-black?style=for-the-badge&logo=termux" />
  <img src="https://img.shields.io/badge/Tested%20on-Windows-cyan?style=for-the-badge&logo=Windows" />
  <img src="https://img.shields.io/badge/Tested%20on-Linux-balck?style=for-the-badge&logo=Linux" />
  <img src="https://img.shields.io/pepy/dt/user-scanner?style=for-the-badge" />
</p>

---

Scan a username across multiple social, developer, and creator platforms to see if it’s available.  
Perfect for finding a **unique username** across GitHub, Twitter, Reddit, Instagram, and more, all in one command.


### Features

- ✅ Check usernames across **social networks**, **developer platforms**, and **creator communities**
- ✅ Can be used as a username OSINT tool
- ✅ Smart auto-update system, Detects new releases on PyPI and interactively prompts the user to upgrade.
- ✅ Clear **Available / Taken / Error** output for each platform
- ✅ Robust error handling: It prints the exact reason (e.g. Cannot use underscores, hyphens at the start/end)
- ✅ Fully modular: add new platform modules easily
- ✅ Wildcard-based username permutations for automatic variation generation using provided suffix
- ✅ Selection of results format (e.g. json, csv, console (default))
- ✅ Get the scanning results in preferred format (json/csv) in specified output file (suitable for power users)
- ✅ Command-line interface ready: works directly after `pip install`
- ✅ Very low and lightweight dependencies, can be run on any machine
---

### Installation

```bash
pip install user-scanner
```

---

### Usage

Scan a username across all platforms:

```bash
user-scanner -u <username>
```
Optionally, scan a specific category or single module:

```bash
user-scanner -u <username> -c dev
user-scanner -l # Lists all available modules
user-scanner -u <username> -m github
```

Also, the output file and format can be specified: <br>

```bash
user-scanner -u <username> -f console #Default format
user-scanner -u <username> -f csv
user-scanner -u <username> -f json
user-scanner -u <username> -f <format> -o <output-file>
```

Generate multiple username variations by appending a suffix:

```bash
user-scanner -u <username> -p <suffix>
```
Optionally, scan a specific category or single module with limit:

```bash
user-scanner -u <username> -p <suffix> -c dev
user-scanner -u <username> -p <suffix> -m github
user-scanner -u <username> -p <suffix> -s <number> # limit generation of usernames
user-scanner -u <username> -p <suffix> -d <seconds> # delay to avoid rate-limits (can be 0s-1s)
```
---

### Update

Update the tool to the latest PyPI version:

```bash
user-scanner -U

```

---

### Screenshot: 

- Note*: New modules are constantly getting added so this might have only limited, outdated output:


<img width="1080" height="770" alt="1000140392" src="https://github.com/user-attachments/assets/4638c8f6-40c6-46f8-ae17-ac65cd199d81" />


---

<img width="1080" height="352" alt="1000140393" src="https://github.com/user-attachments/assets/578b248c-2a05-4917-aab3-6372a7c28045" />

---

<img width="992" height="556" alt="1000141265" src="https://github.com/user-attachments/assets/9babb19f-bc87-4e7b-abe5-c52b8b1b672c" />


### Contributing: 

Modules are organized by category:

```
user_scanner/
├── dev/        # Developer platforms (GitHub, GitLab, etc.)
├── social/     # Social platforms (Twitter/X, Reddit, Instagram, etc.)
├── creator/    # Creator platforms (Hashnode, Dev.to, Medium, etc.)
├── community/  # Community platforms (forums, niche sites)
├── gaming/     # Gaming sites (chess.com, roblox, monkeytype etc.)
├── donation/   # Donation taking sites (buymeacoffe.com, similar...)
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

### Dependencies: 
- [httpx](https://pypi.org/project/httpx/)
- [colorama](https://pypi.org/project/colorama/)

---

### License

This project is licensed under the **MIT License**. See [LICENSE](LICENSE) for details.


---

### Star History

<a href="https://www.star-history.com/#kaifcodec/user-scanner&type=date&legend=top-left">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=kaifcodec/user-scanner&type=date&theme=dark&legend=top-left" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=kaifcodec/user-scanner&type=date&legend=top-left" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=kaifcodec/user-scanner&type=date&legend=top-left" />
 </picture>
</a>

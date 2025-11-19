# User Scanner

![1000136215](https://github.com/user-attachments/assets/49ec8d24-665b-4115-8525-01a8d0ca2ef4)
<p align="center">
  <img src="https://img.shields.io/badge/Version-1.0.2.0-blueviolet?style=for-the-badge&logo=github" />
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

- ✅ Check usernames across **social networks**, **developer platforms**, and **creator communities**.
- ✅ Clear **Available / Taken / Error** output for each platform.
- ✅ Fully modular: add new platform modules easily.
- ✅ Command-line interface ready: works directly after `pip install`.
- ✅ Can be used as username OSINT tool.
- ✅ Very low and lightweight dependencies, can be run on any machine.
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
---
### Example Output: 

- Note*: New modules are constantly getting added so this might have only limited, outdated output: 
```bash
 Checking username: johndoe078

== DEV SITES ==
  [✔] Codeberg: Available
  [✔] Cratesio: Available
  [✔] Dockerhub: Available
  [✘] Github: Taken
  [✔] Gitlab: Available
  [✔] Launchpad: Available
  [✔] Npmjs: Available
  [✔] Replit: Available

== SOCIAL SITES ==
  [✔] Bluesky: Available
  [✔] Discord: Available
  [✘] Instagram: Taken
  [✔] Mastodon: Available
  [✔] Pinterest: Available
  [✘] Reddit: Taken
  [✔] Snapchat: Available
  [✔] Telegram: Available 
  [✘] Threads: Taken
  [✔] X (Twitter): Available
  [✔] Youtube: Available

== CREATOR SITES ==
  [✔] Devto: Available
  [✔] Hashnode: Available
  [✔] Kaggle: Available
  [✔] Medium: Available
  [✔] Patreon: Available

== COMMUNITY SITES ==
  [✔] Coderlegion: Available

== GAMING SITES ==
  [✔] Chess_com: Available
  [✔] Osu: Available
  [✔] Roblox: Available
  ...
  ...
  ...
```
### Contributing: 

Modules are organized by category:

```
user_scanner/
├── dev/        # Developer platforms (GitHub, GitLab, etc.)
├── social/     # Social platforms (Twitter/X, Reddit, Instagram, etc.)
├── creator/    # Creator platforms (Hashnode, Dev.to, Medium, etc.)
├── community/  # Community platforms (forums, niche sites)
├── gaming/     # Gaming sites (chess.com, roblox, monkeytype etc.)
```

**Module guidelines:**
- Each module must define a `validate_<site>()` function that takes a `username` and returns:
  - `1` → Available  
  - `0` → Taken  
  - `2` → Error / Could not check
- Use `httpx` for requests, `colorama` for colored output.
- Optional: modules can define a CLI parser if they support custom arguments.

See [CONTRIBUTING.md](CONTRIBUTING.md) for examples.

### 📧 Contact:
- [Email](kaifcodec@gmail.com)
  
---

### Dependencies: 
- [httpx](https://pypi.org/project/httpx/)
- [colorama](https://pypi.org/project/colorama/)

---

### License

This project is licensed under the **MIT License**. See [LICENSE](LICENSE) for details.


<!--- 
## 🌟 Stars: 

<a href="https://www.star-history.com/#kaifcodec/user-scanner&type=date&legend=top-left">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=kaifcodec/user-scanner&type=date&theme=dark&legend=top-left" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=kaifcodec/user-scanner&type=date&legend=top-left" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=kaifcodec/user-scanner&type=date&legend=top-left" />
 </picture>
</a>
--->
---
## ⚠️ `community/` and `gaming/` are small, looking for contributions

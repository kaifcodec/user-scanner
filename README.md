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

### ⚠️ Email OSINT mode had not been implemented yet, still in progress 

A powerful *Email OSINT tool* that checks if a specific email is registered on various sites, combined with *username scanning* — 2-in-1 solution.  

Perfect for fast, accurate and lightweight email OSINT

Perfect for finding a **unique username** across GitHub, Twitter, Reddit, Instagram, and more, all in a single command.  

> **Note:** Originally based on [user-scanner](https://github.com/kaifcodec/user-scanner) by kaifcodec, significantly enhanced with proxy support, bulk scanning, and email validation.

## Features

- ✅ Check an email across multiple sites to see if it’s registered.  
- ✅ Scan usernames across **social networks**, **developer platforms**, **creator communities**, and more.  
- ✅ Can be used purely as a username tool.  
- ✅ Smart auto-update system detects new releases on PyPI and prompts the user to upgrade interactively.  
- ✅ Clear `Registered` and `Not Registered` for email scanning `Available` / `Taken` / `Error` output for username scans
- ✅ Robust error handling: displays the exact reason a username or email cannot be used (e.g., underscores or hyphens at the start/end).  
- ✅ Fully modular: easily add new platform modules.  
- ✅ Wildcard-based username permutations for automatic variation generation using a provided suffix.  
- ✅ Option to select results format (**JSON**, **CSV**, console).  
- ✅ Save scanning and OSINT results in the preferred format and output file (ideal for power users).  
- ✅ Command-line interface ready: works immediately after `pip install`.  
- ✅ Lightweight with minimal dependencies; runs on any machine.
- ✅ **Proxy support** with round-robin rotation (contributed by [moh-saidi](https://github.com/moh-saidi))
- ✅ **Proxy validation** to test and filter working proxies before scanning (contributed by [moh-saidi](https://github.com/moh-saidi))
- ✅ **Bulk username scanning** from file support for checking multiple usernames at once (contributed by [moh-saidi](https://github.com/moh-saidi))
- ✅ **Bulk email scanning** from file support for checking multiple emails at once (contributed by [moh-saidi](https://github.com/moh-saidi))
---

## Installation

```bash
pip install user-scanner
```

---

## Usage

### Basic username/email scan

Scan a single username across **all** available modules/platforms:

```bash
user-scanner -e john_doe@gmail.com
user-scanner --email john_doe@gmail.com # long version

user-scanner -u john_doe
user-scanner --username john_doe # long version

```

### Bulk username scanning

Scan multiple usernames from a file (one username per line):

```bash
user-scanner -uf usernames.txt
user-scanner --username-file usernames.txt # long version
```

Combine with categories or modules:

```bash
user-scanner -uf usernames.txt -c dev # scan multiple users on dev platforms only
user-scanner -uf usernames.txt -m github # scan multiple users on GitHub only
```

### Bulk email scanning

Scan multiple emails from a file (one email per line):

```bash
user-scanner -ef emails.txt
user-scanner --email-file emails.txt # long version
```

Combine with categories or modules:

```bash
user-scanner -ef emails.txt -c social # scan multiple emails on social platforms
user-scanner -ef emails.txt -m instagram # scan multiple emails on Instagram
```

### Selective scanning

Scan only specific categories or single modules:

```bash
user-scanner -u john_doe -c dev # developer platforms only
user-scanner -u john_doe -m github # only GitHub

```

List all available modules/categories:

```bash
user-scanner -l

```

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
user-scanner -u john_doe -P proxies.txt --validate-proxies
```

This will:
1. Test all proxies from the file
2. Filter out non-working proxies
3. Save working proxies to `validated_proxies.txt`
4. Use only validated proxies for scanning

See [PROXY_USAGE.md](PROXY_USAGE.md) for detailed proxy configuration and usage.

## Important Flags

| Flag | Description |
|------|-------------|
| `-u, --username USERNAME` | Scan a single username across platforms |
| `-e, --email EMAIL`       | Scan a single email across platforms |
| `-uf, --username-file FILE` | Scan multiple usernames from file (one per line) |
| `-ef, --email-file FILE`  | Scan multiple emails from file (one per line) |
| `-c, --category CATEGORY` | Scan all platforms in a specific category |
| `-l, --list` | List all available modules for username scanning |
| `-m, --module MODULE`     | Scan a single specific module |
| `-p, --permute PERMUTE`   | Generate username permutations using a pattern/suffix |
| `-P, --proxy-file FILE`   | Use proxies from file (one per line) |
| `--validate-proxies`      | Validate proxies before scanning (tests against google.com) |
| `-s, --stop STOP`         | Limit the number of permutations generated |
| `-d, --delay DELAY`       | Delay (in seconds) between requests |
| `-f, --format {csv,json}` | Select output format |
| `-o, --output OUTPUT`     | Save results to a file |

---

### Update

Update the tool to the latest PyPI version:

```bash
user-scanner -U
```
---

## Screenshot: 

- Note*: New modules are constantly getting added so this might have only limited, outdated output:

<img width="1072" height="848" alt="user-scanner's main usage screenshot" src="https://github.com/user-attachments/assets/34e44ca6-e314-419e-9035-d951b493b47f" />



---

<img width="1080" height="352" alt="user-scanner's wildcard username feature" src="https://github.com/user-attachments/assets/578b248c-2a05-4917-aab3-6372a7c28045" />

---

<img width="992" height="556" alt="user-scanner's JSON output screenshot" src="https://github.com/user-attachments/assets/9babb19f-bc87-4e7b-abe5-c52b8b1b672c" />

---

## Contributing

Modules are organized under `user_scanner/`:

```
user_scanner/
├── email_scan/       # Currently in development
│   └── social/       # Social email scan modules (Instagram, Mastodon, X, etc.)
|    ...               # New sites to be added soon
├── user_scan/
│   ├── dev/          # Developer platforms (GitHub, GitLab, npm, etc.)
│   ├── social/       # Social platforms (Twitter/X, Reddit, Instagram, Discord, etc.)
│   ├── creator/      # Creator platforms (Hashnode, Dev.to, Medium, Patreon, etc.)
│   ├── community/    # Community platforms (forums, StackOverflow, HackerNews, etc.)
│   ├── gaming/       # Gaming sites (chess.com, Lichess, Roblox, Minecraft, etc.)
│   └── donation/     # Donation platforms (BuyMeACoffee, Liberapay)
|...
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

## Star History

<a href="https://www.star-history.com/#kaifcodec/user-scanner&type=date&legend=top-left">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=kaifcodec/user-scanner&type=date&theme=dark&legend=top-left" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=kaifcodec/user-scanner&type=date&legend=top-left" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=kaifcodec/user-scanner&type=date&legend=top-left" />
 </picture>
</a>

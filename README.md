# User Scanner

Scan a username across multiple social, developer, and creator platforms to see if it’s available.  
Perfect for finding a **unique username** across GitHub, Twitter, Reddit, Instagram, and more, all in one command.

---

## Features

- ✅ Check usernames across **social networks**, **developer platforms**, and **creator communities**.
- ✅ Clear **Available / Taken / Error** output for each platform.
- ✅ Fully modular: add new platform modules easily.
- ✅ Command-line interface ready: works directly after `pip install`.

---

## Installation

```bash
pip install user-scanner
```

---

## Usage

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

## Contributing

Modules are organized by category:

```
user_scanner/
├── dev/        # Developer platforms (GitHub, GitLab, etc.)
├── social/     # Social platforms (Twitter/X, Reddit, Instagram, etc.)
├── creator/    # Creator platforms (Hashnode, Dev.to, Medium, etc.)
├── community/  # Community platforms (forums, niche sites)
```

**Module guidelines:**
- Each module must define a `validate_<site>()` function that takes a `username` and returns:
  - `1` → Available  
  - `0` → Taken  
  - `2` → Error / Could not check
- Use `httpx` for requests, `colorama` for colored output.
- Optional: modules can define a CLI parser if they support custom arguments.

See [CONTRIBUTING.md](CONTRIBUTING.md) for examples.

---

## Dependencies
- [httpx](https://pypi.org/project/httpx/)
- [colorama](https://pypi.org/project/colorama/)

---

## License

This project is licensed under the **MIT License**. See [LICENSE](LICENSE) for details.

## ⚠️ `community/` is small looking for contributions

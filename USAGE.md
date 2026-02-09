# 🛠 Library Mode Usage Guide

User Scanner provides a powerful **Library Mode** via its core engine. This allows you to integrate OSINT capabilities directly into your own Python scripts, returning clean, structured data in JSON or CSV formats.

---

### Quick Start: Single Module Scan

The engine automatically detects whether you are using a module from `email_scan` or `user_scan` by inspecting its path. It then adjusts the result labels (e.g., "Registered" vs "Taken") automatically.

### Email Scan Example
```python
import asyncio
from user_scanner.core import engine
from user_scanner.email_scan.social import instagram

async def main():
    # Engine detects 'email_scan' path -> Result status: "Registered" / "Not Registered"
    result = await engine.check(instagram, "target@gmail.com")
    
    # Get structured data
    json_data = result.to_json()
    csv_data = result.to_csv()
    
    print(json_data)
    
asyncio.run(main())
```
Output:
```json
{
        "email": "target@gmail.com",
        "category": "Social",
        "site_name": "Instagram",
        "status": "Registered",
        "reason": ""
}
```

### Username Scan Example
```python
import asyncio
from user_scanner.core import engine
from user_scanner.user_scan.dev import github

async def main():
    # Engine detects 'user_scan' path -> Result status: "Available" / "Taken"
    result = await engine.check(github, "johndoe123")
    
    print(result.to_json())

asyncio.run(main())
```
Output:

```json
{
        "username": "johndoe123",
        "category": "Dev",
        "site_name": "Github",
        "status": "Taken",
        "reason": ""
}
```
---

### Batch & Category Scans

You can scan entire folders of modules (e.g., all social media, all forums) or perform a full system scan across all categories.

#### Scan a Specific Category
```python
import asyncio
from user_scanner.core import engine
from user_scanner.core.formatter import into_json

async def main():
    target = "johndoe123"
    
    # Scans everything inside 'user_scan/social/'
    # Use is_email=False to tell the engine where to look for the category folder
    results = await engine.check_category("social", target, is_email=False)
    
    # 'into_json' wraps the results into a valid JSON array []
    print(into_json(results))

asyncio.run(main())
```

#### Full OSINT Scan (All Categories)
```python
import asyncio
from user_scanner.core import engine
from user_scanner.core.formatter import into_json

async def main():
    email = "target@example.com"
    
    # Scans every module available in 'email_scan/'
    results = await engine.check_all(email, is_email=True)
    
    # Save results to a file
    with open("report.json", "w") as f:
        f.write(into_json(results))

asyncio.run(main())
```

---

### Available Output Formats

Every `Result` object returned by the engine supports the following methods:

| Method | Description |
| :--- | :--- |
| `.to_json()` | Returns a formatted JSON string for a single result. |
| `.to_csv()` | Returns a comma-separated string for a single result. |
| `.as_dict()` | Returns a Python dictionary (useful for APIs). |
| `.show()` | Prints a colorized string to the console (CLI style). |

To format a **List** of results, use the `formatter`:
- `into_json(results_list)`
- `into_csv(results_list)`

---

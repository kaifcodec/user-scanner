# 🛠 Library Mode Usage Guide

User Scanner provides a powerful **Library Mode** via its core engine. This allows you to integrate OSINT capabilities directly into your own Python scripts, returning clean, structured data in JSON or CSV formats.

---

### Quick Start: Single Module Scan

The engine automatically detects whether you are using a module from `email_scan` or `user_scan` by inspecting its path. It then adjusts the result labels (e.g., "Registered" vs "Found") automatically.

### Email Scan Example
```python
import asyncio
from user_scanner.core import engine
from user_scanner.email_scan.social import instagram

async def main():
    # Engine detects 'email_scan' path -> Result status: "Registered" / "Not Registered" / "Error"
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
        "url": "https://instagram.com",
        "extra": "",
        "reason": ""
}
```

### Username Scan Example
```python
import asyncio
from user_scanner.core import engine
from user_scanner.user_scan.dev import github

async def main():
    # Engine detects 'user_scan' path -> Result status: "Not Found" / "Found" / "Error"
    result = await engine.check(github, "kaifcodec")
    
    print(result.to_json())

asyncio.run(main())
```
Output:

```json
{
    "status": "Found",
    "reason": "",
    "username": "kaifcodec",
    "site_name": "Github",
    "category": "Dev",
    "url": "https://github.com/kaifcodec",
    "extra": {
        "name": "Kaif",
        "bio": "EMPTY.",
        "followers": "243",
        "avatar": "https://avatars.githubusercontent.com/u/98528577?v=4",
        "public_repos": "28",
        "created_at": "2022-01-27T12:00:36Z",
        "links": "https://www.instagram.com/kaifcodec"
    }
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
Output:
```json
[
    {
        "status": "Not Found",
        "reason": "",
        "username": "johndoe123",
        "site_name": "7dach",
        "category": "Social",
        "url": "https://7dach.ru/profile/johndoe123",
        "extra": {}
    },
    {
        "status": "Not Found",
        "reason": "",
        "username": "johndoe123",
        "site_name": "Flickr",
        "category": "Social",
        "url": "https://www.flickr.com/photos/johndoe123/",
        "extra": {}
    },
    {
        "status": "Not Found",
        "reason": "",
        "username": "johndoe123",
        "site_name": "Mix",
        "category": "Social",
        "url": "https://mix.com/johndoe123",
        "extra": {}
    },
    {
        "status": "Found",
        "reason": "",
        "username": "johndoe123",
        "site_name": "Linkedin",
        "category": "Social",
        "url": "https://www.linkedin.com/in/johndoe123/",
        "extra": {}
    },
    {
        "status": "Found",
        "reason": "",
        "username": "johndoe123",
        "site_name": "Bluesky",
        "category": "Social",
        "url": "https://bsky.app/profile/johndoe123.bsky.social",
        "extra": {
            "followers": 1,
            "following": 12,
            "posts": 0,
            "avatar": "https://cdn.bsky.app/img/avatar/plain/did:plc:nhbohtxyngexrshwvm22i5dx/bafkreih432vhtni2i2wg2tqn4atnycy2xcoxvzmpd2ktyqzai3lvzmbesu"
        }
    },
    {
        "status": "Found",
        "reason": "",
        "username": "johndoe123",
        "site_name": "Minds",
        "category": "Social",
        "url": "https://www.minds.com/johndoe123",
        "extra": {}
    },
    {
        "status": "Found",
        "reason": "",
        "username": "johndoe123",
        "site_name": "Instagram",
        "category": "Social",
        "url": "https://www.instagram.com/johndoe123/",
        "extra": {
            "username": "johndoe123",
            "id": "6970864",
            "image": "https://instagram.fhan14-5.fna.fbcdn.net/v/t51.2885-19/573323465_1219825463302212_7278921664109726296_n.png?stp=dst-jpg_s150x150_tt6&efg=eyJ2ZW5jb2RlX3RhZyI6InByb2ZpbGVfcGljLmRqYW5nby4xNTAuYzIifQ&_nc_ht=instagram.fhan14-5.fna.fbcdn.net&_nc_cat=1&_nc_oc=Q6cZ2gHvJJBr73nz66-46FRy7yhLkJiXkcuv8X08Joc_yjMraZSbMoYRRLZuqYeE5-no4buNKZk6OcygbjRlNfGGAgxi&_nc_ohc=NFX067bI9oEQ7kNvwE_yq91&_nc_gid=fN_3hSU13wQ3aNpxzM8LXw&edm=AOmzUmYBAAAA&ccb=7-5&ig_cache_key=YW5vbnltb3VzX3Byb2ZpbGVfcGlj.3-ccb7-5&oh=00_Af_xUwRgNMsExsNAqG5MpAFSzm3NNEBU6C_12oKKbipiLg&oe=6A2C316A&_nc_sid=13eb94",
            "facebook_uid": "17841401765920108",
            "is_business": "False",
            "is_joined_recently": "False",
            "private": "True",
            "verified": "False",
            "follower_count": 0,
            "following_count": 0
        }
    },
    {
        "status": "Error",
        "reason": "Function validate_cups7 not found",
        "username": "johndoe123",
        "site_name": "Cups7",
        "category": "Social",
        "url": "",
        "extra": {}
    },
    {
        "status": "Found",
        "reason": "",
        "username": "johndoe123",
        "site_name": "Mastodon",
        "category": "Social",
        "url": "https://mastodon.social/@johndoe123",
        "extra": {
            "id": "110767520136069183",
            "followers": 0,
            "following": 0,
            "posts": 0,
            "avatar": "https://mastodon.social/avatars/original/missing.png"
        }
    },
    {
        "status": "Found",
        "reason": "",
        "username": "johndoe123",
        "site_name": "X (Twitter)",
        "category": "Social",
        "url": "https://x.com/johndoe123",
        "extra": {
            "name": "johndoe",
            "created_at": "Thu Mar 06 17:11:47 +0000 2008",
            "followers": "6",
            "following": "1",
            "avatar": "https://abs.twimg.com/sticky/default_profile_images/default_profile.png"
        }
    },
    {
        "status": "Found",
        "reason": "",
        "username": "johndoe123",
        "site_name": "Discord",
        "category": "Social",
        "url": "https://discord.com",
        "extra": {}
    },
    {
        "status": "Error",
        "reason": "Unexpected response body, report it via GitHub issues.",
        "username": "johndoe123",
        "site_name": "Facebook",
        "category": "Social",
        "url": "https://www.facebook.com/johndoe123",
        "extra": {}
    },
    {
        "status": "Found",
        "reason": "",
        "username": "johndoe123",
        "site_name": "About.me",
        "category": "Social",
        "url": "https://about.me/johndoe123",
        "extra": {}
    },
    {
        "status": "Found",
        "reason": "",
        "username": "johndoe123",
        "site_name": "Pinterest",
        "category": "Social",
        "url": "https://www.pinterest.com/johndoe123/",
        "extra": {
            "name": "John"
        }
    },
    {
        "status": "Not Found",
        "reason": "",
        "username": "johndoe123",
        "site_name": "Albicla",
        "category": "Social",
        "url": "https://albicla.com/johndoe123",
        "extra": {}
    },
    {
        "status": "Not Found",
        "reason": "",
        "username": "johndoe123",
        "site_name": "Gravatar",
        "category": "Social",
        "url": "https://gravatar.com/johndoe123",
        "extra": {}
    },
    {
        "status": "Found",
        "reason": "",
        "username": "johndoe123",
        "site_name": "Threads",
        "category": "Social",
        "url": "https://www.threads.net/@johndoe123",
        "extra": {}
    },
    {
        "status": "Found",
        "reason": "",
        "username": "johndoe123",
        "site_name": "Youtube",
        "category": "Social",
        "url": "https://youtube.com/@johndoe123",
        "extra": {
            "fullname": "John Doe (Godz)",
            "youtube_channel_id": "UCOvNRYBoOZnpkUqTx9YHRkA",
            "channel_url": "http://www.youtube.com/@johndoe123",
            "is_family_safe": "True",
            "image": "https://yt3.googleusercontent.com/ytc/AIdro_kfQgNpnyMrf6mRBrtZzsz7mfLGfQmRtPmQwb5l6Fqa1DA=s900-c-k-c0x00ffffff-no-rj",
            "subscribers": "3 subscribers"
        }
    },
    {
        "status": "Error",
        "reason": "HTTP 403",
        "username": "johndoe123",
        "site_name": "Reddit",
        "category": "Social",
        "url": "https://www.reddit.com/user/johndoe123/",
        "extra": {}
    },
    {
        "status": "Found",
        "reason": "",
        "username": "johndoe123",
        "site_name": "Telegram",
        "category": "Social",
        "url": "https://t.me/johndoe123",
        "extra": {}
    },
    {
        "status": "Error",
        "reason": "ConnectError: Network unreachable (is your internet on?)",
        "username": "johndoe123",
        "site_name": "Tiktok",
        "category": "Social",
        "url": "https://www.tiktok.com/@johndoe123",
        "extra": {}
    },
    {
        "status": "Not Found",
        "reason": "",
        "username": "johndoe123",
        "site_name": "Zhihu",
        "category": "Social",
        "url": "https://www.zhihu.com/people/johndoe123",
        "extra": {}
    },
    {
        "status": "Not Found",
        "reason": "",
        "username": "johndoe123",
        "site_name": "Anonup",
        "category": "Social",
        "url": "https://anonup.com/@johndoe123",
        "extra": {}
    },
    {
        "status": "Not Found",
        "reason": "",
        "username": "johndoe123",
        "site_name": "35photo",
        "category": "Social",
        "url": "https://35photo.pro/@johndoe123/",
        "extra": {}
    },
    {
        "status": "Error",
        "reason": "ConnectError: [errno 104] connection reset by peer",
        "username": "johndoe123",
        "site_name": "Vk",
        "category": "Social",
        "url": "https://vk.com/johndoe123",
        "extra": {}
    },
    {
        "status": "Found",
        "reason": "",
        "username": "johndoe123",
        "site_name": "Anilist",
        "category": "Social",
        "url": "https://anilist.co/user/johndoe123",
        "extra": {
            "id": 7319706,
            "avatar": "https://s4.anilist.co/file/anilistcdn/user/avatar/large/default.png"
        }
    },
    {
        "status": "Not Found",
        "reason": "",
        "username": "johndoe123",
        "site_name": "Openstreetmap",
        "category": "Social",
        "url": "https://www.openstreetmap.org/user/johndoe123",
        "extra": {}
    },
    {
        "status": "Found",
        "reason": "",
        "username": "johndoe123",
        "site_name": "Snapchat",
        "category": "Social",
        "url": "https://www.snapchat.com/@johndoe123",
        "extra": {
            "display_name": "John",
            "snapcode": "https://app.snapchat.com/web/deeplink/snapcode?username=johndoe123&type=SVG&bitmoji=enable"
        }
    }
]


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

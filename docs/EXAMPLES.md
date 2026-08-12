# 🖼️ User Scanner Media & Output Gallery

Demonstrations, visual terminal walkthroughs, and sample output formats for User Scanner.

---

## 📺 Video Demos

- **[Download / View Interactive Usage WebM Video](https://github.com/user-attachments/assets/d901510c-880e-4395-8274-3494d984f2de)**

---

## 📸 Terminal & Output Screenshots

### Dual-Mode Username & Email Scanning
<div align="center">
  <img width="850" alt="User Scanner Terminal Output" src="https://github.com/user-attachments/assets/da7d73a5-2a50-4704-b71c-993fe5a17644" />
</div>

---

### Hudson Rock Infostealer Malware Log Check (`--hudson`)
<div align="center">
  <img width="850" alt="Hudson Rock Malware Output" src="https://github.com/user-attachments/assets/366d4697-b94b-40b2-9844-f936b6fcea7f" />
</div>

---

## 📂 Sample Export Formats

### JSON Report Export (`-f json`)

```json
{
  "email": "target@example.com",
  "category": "Social",
  "site_name": "Instagram",
  "status": "Registered",
  "url": "https://www.instagram.com/target",
  "extra": {
    "username": "target",
    "id": "6970864",
    "image": "https://instagram.com/avatar.jpg",
    "private": "False",
    "verified": "False",
    "follower_count": 1250,
    "following_count": 340
  }
}
```

---

### CSV Export (`-f csv`)

```csv
target,Social,Instagram,Registered,https://www.instagram.com/target
```

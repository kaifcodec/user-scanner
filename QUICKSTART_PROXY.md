# Quick Start: Using Proxy Support

## Basic Usage

### 1. Create a proxy file (one proxy per line)
```
http://proxy1.example.com:8080
http://proxy2.example.com:3128
https://secure-proxy.example.com:443
192.168.1.100:8888
```

### 2. Scan with proxies
```bash
# Scan a username with proxies
user-scanner -u john_doe -P proxies.txt

# Scan with specific category
user-scanner -u john_doe -c dev -P proxies.txt

# Scan with output to file
user-scanner -u john_doe -P proxies.txt -o results.json -f json
```

## Validate Proxies First (Recommended)

```bash
# Test proxies against google.com before using
python validate_proxies.py

# This creates working_proxies.txt with only working proxies
user-scanner -u john_doe -P working_proxies.txt
```

## Batch Testing Multiple Usernames

```bash
# Create usernames.txt with one username per line
# Then run batch test
python test_batch.py
```

## Pro Tips

1. **Free proxies** - Most free proxies don't work (as you saw: 11/2000)
2. **Use validation** - Always validate proxies first with `validate_proxies.py`
3. **Rotation works** - Proxies rotate automatically (round-robin)
4. **Add delays** - Use `-d 0.5` to add delay between requests
5. **Without proxies** - Just omit `-P` flag to use direct connection

## 🎯 Example Workflow

```bash
# Step 1: Validate your proxy list
python validate_proxies.py

# Step 2: Scan with working proxies
user-scanner -u myusername -c social -P working_proxies.txt -o results.json -f json

# Step 3: Check results
cat results.json
```

## Files in This Implementation

- `validate_proxies.py` - Tests proxies against google.com
- `test_batch.py` - Batch tests multiple usernames
- `usernames.txt` - Sample username list
- `working_proxies.txt` - Validated working proxies (generated)
- `PROXY_USAGE.md` - Full documentation
- `proxies_example.txt` - Example proxy file format

## That's It!

You now have:
- Proxy support integrated
- Automatic proxy rotation
- Validation tools
- Batch testing capability

# Proxy Support Guide

## Overview

User-scanner now supports using proxies to route your requests through different IP addresses. This is useful for:
- Avoiding rate limits
- Testing from different geographic locations
- Improving privacy and anonymity
- Bypassing IP-based restrictions

## Proxy File Format

Create a text file with one proxy per line. Supported formats:

```
http://proxy.example.com:8080
https://secure-proxy.example.com:443
socks5://socks-proxy.example.com:1080
192.168.1.100:8888
```

### Features:
- **Comments**: Lines starting with `#` are ignored
- **Auto-protocol**: If no protocol is specified, `http://` is assumed
- **Multiple protocols**: Supports HTTP, HTTPS, and SOCKS5
- **Authentication**: Supports proxies with username/password

### Example with authentication:
```
http://username:password@proxy.example.com:8080
```

## Usage

### Basic Usage

Scan a username using proxies:
```bash
user-scanner -u john_doe -P proxies.txt
```

Scan an email using proxies:
```bash
user-scanner -e user@example.com -P proxies.txt
```

### Combining with Other Options

With specific category:
```bash
user-scanner -u john_doe -c dev -P proxies.txt
```

With output to file:
```bash
user-scanner -u john_doe -P proxies.txt -o results.json -f json
```

With delay between requests:
```bash
user-scanner -u john_doe -P proxies.txt -d 0.5
```

## How It Works

### Proxy Rotation

The tool uses **round-robin rotation** to distribute requests across all available proxies:
1. First request uses proxy #1
2. Second request uses proxy #2
3. When reaching the end of the list, it cycles back to proxy #1

This ensures even distribution of traffic across all your proxies.

### Thread Safety

The proxy manager is thread-safe, meaning when the tool runs multiple checks in parallel, each thread gets a different proxy without conflicts.

## Example Proxy File

See [proxies_example.txt](proxies_example.txt) for a complete example.

## Tips

1. **Free Proxies**: Be cautious with free proxy lists - they may be slow, unreliable, or insecure
2. **Testing**: Test your proxies before using them for large scans
3. **Quantity**: More proxies = better distribution and lower chance of rate limiting
4. **Speed**: SOCKS5 proxies are generally faster than HTTP proxies
5. **Authentication**: If your proxy requires authentication, include it in the format `protocol://user:pass@host:port`

## Error Handling

If a proxy fails:
- The request will timeout and be marked as an error
- The next request will use the next proxy in rotation
- Check the console output for connection errors

If the proxy file is invalid:
- The tool will display an error message and exit
- Check that the file exists and contains valid proxy entries

## Common Issues

### "No valid proxies found in file"
- Ensure the file contains at least one valid proxy
- Check that proxy lines are not all commented out

### Connection timeouts
- Verify your proxies are online and accessible
- Try increasing the timeout with longer delays (`-d` flag)
- Test proxies individually with a single module (`-m github`)

### Authentication errors
- Ensure credentials are correct
- Format: `http://username:password@proxy:port`
- Some proxies may not support authentication

## Security Note

WARNING: Proxies can see your traffic. Only use proxies you trust, especially when sending sensitive information. Free public proxies may log or intercept your data.

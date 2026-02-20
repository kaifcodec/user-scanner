## Important Flags

| Flag | Description |
|------|-------------|
| `-u, --username USERNAME` | Scan a single username across platforms |
| `-e, --email EMAIL`       | Scan a single email across platforms |
| `-uf, --username-file FILE` | Scan multiple usernames from file (one per line) |
| `-ef, --email-file FILE`  | Scan multiple emails from file (one per line) |
| `-c, --category CATEGORY` | Scan all platforms in a specific category |
| `-lu, --list-user`        | List all available modules for username scanning |
| `-le, --list-email`       | List all available modules for email scanning |
| `-v, --verbose`           | Enable verbose output to show urls of the websites |
| `-m, --module MODULE`     | Scan a single specific module |
| `-P, --proxy-file FILE`   | Use proxies from file (one per line) |
| `--validate-proxies`      | Validate proxies before scanning (tests against google.com) |
| `-s, --stop STOP`         | Limit pattern expansions (use with `[chars]{n}` in username/email) |
| `-r, --random`            | Randomize pattern expansion order |
| **Pattern syntax**        | Embed `[a-z]`, `[0-9]{1-2}` in username/email for expansion |
| `-d, --delay DELAY`       | Delay (in seconds) between requests |
| `-f, --format {csv,json}` | Select output format |
| `-o, --output OUTPUT`     | Save results to a file |

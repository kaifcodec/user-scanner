## Important Flags

| Flag                        | Description                                                 |
| --------------------------- | ----------------------------------------------------------- |
| `-u, --username USERNAME`   | Scan a single username across platforms                     |
| `-e, --email EMAIL`         | Scan a single email across platforms                        |
| `-uf, --username-file FILE` | Scan multiple usernames from file (one per line)            |
| `-ef, --email-file FILE`    | Scan multiple emails from file (one per line)               |
| `--allow-loud`              | Enable scanning sites that may send emails/notifications    |
| `--no-nsfw`                 | Disable NSFW site scanning                                  |
| `--hudson, --hudson-scan`   | Check for infostealer intelligence using Hudson Rock's API  |
| `--cross-scan`              | After the scan, follow the usernames, links and email addresses its results expose and scan those too (see [CROSS_SCAN.md](CROSS_SCAN.md)) |
| `--cross-links {all,verified,none}` | Which links a cross-scan may pivot from (default: `all`) |
| `--cross-emails {all,verified,none}` | Which addresses a cross-scan may scan as emails: `all` includes ones scraped from bio text, `verified` only ones a site published in its own email field, `none` scans none. Loud email modules are skipped unless `--allow-loud` (default: `verified`) |
| `--cross-depth N`           | Rounds of link-following; each round pivots off the accounts the previous one found (default: 1) |
| `--cross-sweep N`           | Targets — usernames and addresses together — swept against every module of their kind, across all rounds; `0` disables sweeping (default: 3) |
| `-c, --category CATEGORY`   | Scan all platforms in a specific category (comma-separated for multiple); also narrows `--cross-scan` |
| `-lu, --list-user`          | List all available modules for username scanning            |
| `-le, --list-email`         | List all available modules for email scanning               |
| `-v, --verbose`             | Enable verbose output to show urls of the websites          |
| `--all`                     | Show all results including Not Found/Not Registered/Error/Skipped |
| `-m, --module MODULE`       | Scan a specific module (comma-separated for multiple); also narrows `--cross-scan` |
| `-p, --permute PERMUTE`     | Generate username permutations using a pattern/suffix       |
| `-P, --proxy-file FILE`     | Use proxies from file (one per line)                        |
| `--validate-proxies`        | Validate proxies before scanning (tests against google.com) |
| `-s, --stop STOP`           | Limit the number of permutations generated                  |
| `-d, --delay DELAY`         | Delay (in seconds) between requests                         |
| `-t, --timeout TIMEOUT`     | Override default request timeout in seconds                 |
| `-C, --concurrency CONC`    | Override default concurrency limit                          |
| `-f, --format {csv,json,pdf}`| Select output format                                       |
| `-o, --output OUTPUT`       | Save results to a file (Can be used directly without `-f`)  |
| `-U, --update`              | Update the tool to the latest version                       |
| `--version`                 | Print the current version                                   |

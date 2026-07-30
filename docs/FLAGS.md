## Important Flags

| Flag                        | Description                                                 |
| --------------------------- | ----------------------------------------------------------- |
| `-u, --username USERNAME`   | Scan a single username across platforms                     |
| `-e, --email EMAIL`         | Scan a single email across platforms                        |
| `-uf, --username-file FILE` | Scan multiple usernames from file (one per line)            |
| `-ef, --email-file FILE`    | Scan multiple emails from file (one per line)               |
| `--only-found`              | Only show sites where the username/email was found          |
| `--allow-loud`              | Enable scanning sites that may send emails/notifications    |
| `--no-nsfw`                 | Disable NSFW site scanning                                  |
| `--hudson, --hudson-scan`   | Check for infostealer intelligence using Hudson Rock's API  |
| `-c, --category CATEGORY`   | Scan all platforms in a specific category (comma-separated for multiple) |
| `-lu, --list-user`          | List all available modules for username scanning            |
| `-le, --list-email`         | List all available modules for email scanning               |
| `-v, --verbose`             | Enable verbose output to show urls of the websites          |
| `-m, --module MODULE`       | Scan a specific module (comma-separated for multiple)                    |
| `-p, --permute PERMUTE`     | Generate username permutations using a pattern/suffix       |
| `-P, --proxy-file FILE`     | Use proxies from file (one per line)                        |
| `--validate-proxies`        | Validate proxies before scanning (tests against google.com) |
| `-s, --stop STOP`           | Limit the number of permutations generated                  |
| `-d, --delay DELAY`         | Delay (in seconds) between requests                         |
| `-t, --timeout TIMEOUT`     | Override default request timeout in seconds                 |
| `-C, --concurrency CONC`    | Override default concurrency limit                          |
| `-f, --format {csv,json}`   | Select output format                                        |
| `-o, --output OUTPUT`       | Save results to a file                                      |
| `-U, --update`              | Update the tool to the latest version                       |
| `--version`                | Print the current version                                   |

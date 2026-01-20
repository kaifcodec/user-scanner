# Git Workflow for Contributing Proxy Feature

# 1. After forking on GitHub, add your fork as a remote
git remote add myfork https://github.com/YOUR_USERNAME/user-scanner.git

# 2. Create a new branch for your feature
git checkout -b feature/proxy-support

# 3. Stage your changes
git add user_scanner/core/helpers.py
git add user_scanner/core/orchestrator.py
git add user_scanner/core/email_orchestrator.py
git add user_scanner/__main__.py
git add README.md
git add PROXY_USAGE.md
git add proxies_example.txt

# 4. Commit your changes
git commit -m "Add proxy file support with rotation

- Added ProxyManager class for thread-safe proxy loading and rotation
- Integrated proxy support into make_request() function
- Added -P/--proxy-file CLI argument
- Created comprehensive proxy documentation
- Supports HTTP, HTTPS, and SOCKS5 proxies
- Implements round-robin proxy rotation
- Includes proxy validation script

Closes #[issue_number]"

# 5. Push to your fork
git push myfork feature/proxy-support

# 6. Then go to GitHub and create a Pull Request from your fork to the original repo

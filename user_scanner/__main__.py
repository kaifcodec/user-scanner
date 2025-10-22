from user_scanner.core.orchestrator import run_checks

if __name__ == "__main__":
    username = input("Enter a username to scan: ").strip()
    run_checks(username)

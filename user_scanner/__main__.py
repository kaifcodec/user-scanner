import argparse
from user_scanner.core.orchestrator import run_checks

def main():
    parser = argparse.ArgumentParser(
        prog="user-scanner",
        description="Scan a username across dev, social, creator, and community platforms."
    )
    parser.add_argument(
        "-u", "--username",
        required=True,
        help="Username to scan across all supported platforms."
    )
    args = parser.parse_args()
    run_checks(args.username)

if __name__ == "__main__":
    main()

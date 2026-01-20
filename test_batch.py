"""
Test username scanner with validated proxies
"""
import subprocess
import sys
import os

def read_usernames(filename):
    """Read usernames from file"""
    usernames = []
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                usernames.append(line)
    return usernames

def test_usernames(usernames_file, proxy_file, category='dev', output_file='results.json'):
    """Test all usernames with proxies"""
    usernames = read_usernames(usernames_file)
    
    print(f"[*] Testing {len(usernames)} usernames")
    print(f"[*] Using proxy file: {proxy_file}")
    print(f"[*] Category: {category}")
    print(f"[*] Output: {output_file}\n")
    
    python_exe = r"C:/Users/ms070/OneDrive/Desktop/user-scanner/.venv/Scripts/python.exe"
    
    for i, username in enumerate(usernames, 1):
        print(f"\n{'='*60}")
        print(f"[{i}/{len(usernames)}] Testing username: {username}")
        print(f"{'='*60}\n")
        
        cmd = [
            python_exe,
            "-m", "user_scanner",
            "-u", username,
            "-c", category,
            "-P", proxy_file,
            "-f", "json",
            "-o", output_file
        ]
        
        subprocess.run(cmd)
    
    print(f"\n{'='*60}")
    print(f"[+] All tests complete! Results saved to {output_file}")
    print(f"{'='*60}")

if __name__ == "__main__":
    # Wait for proxy validation to complete
    if not os.path.exists("working_proxies.txt"):
        print("[!] working_proxies.txt not found!")
        print("[*] Please run validate_proxies.py first")
        sys.exit(1)
    
    test_usernames("usernames.txt", "working_proxies.txt", category="dev", output_file="scan_results.json")

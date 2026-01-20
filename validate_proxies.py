"""
Proxy Validator - Tests all proxies against google.com and keeps only working ones
"""
import httpx
from concurrent.futures import ThreadPoolExecutor, as_completed
from colorama import Fore, Style, init

init(autoreset=True)

def test_proxy(proxy, timeout=10):
    """Test if a proxy works by connecting to google.com"""
    try:
        with httpx.Client(proxy=proxy, timeout=timeout) as client:
            response = client.get("https://www.google.com", follow_redirects=True)
            if response.status_code == 200:
                return proxy, True
            else:
                return proxy, False
    except Exception:
        return proxy, False

def load_proxies(filename):
    """Load proxies from file"""
    proxies = []
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                proxies.append(line)
    return proxies

def validate_proxies(input_file, output_file, max_workers=50):
    """Validate all proxies and save working ones"""
    print(f"{Fore.CYAN}[*] Loading proxies from {input_file}...{Style.RESET_ALL}")
    proxies = load_proxies(input_file)
    total = len(proxies)
    print(f"{Fore.CYAN}[*] Found {total} proxies to test{Style.RESET_ALL}\n")
    
    working_proxies = []
    failed = 0
    tested = 0
    
    print(f"{Fore.YELLOW}[*] Testing proxies (this may take a few minutes)...{Style.RESET_ALL}")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(test_proxy, proxy): proxy for proxy in proxies}
        
        for future in as_completed(futures):
            proxy, is_working = future.result()
            tested += 1
            
            if is_working:
                working_proxies.append(proxy)
                print(f"{Fore.GREEN}[✓] {tested}/{total} - Working: {proxy}{Style.RESET_ALL}")
            else:
                failed += 1
                print(f"{Fore.RED}[✘] {tested}/{total} - Failed: {proxy}{Style.RESET_ALL}")
    
    # Save working proxies
    with open(output_file, 'w', encoding='utf-8') as f:
        for proxy in working_proxies:
            f.write(proxy + '\n')
    
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}[+] Validation Complete!{Style.RESET_ALL}")
    print(f"{Fore.GREEN}[+] Working proxies: {len(working_proxies)}/{total}{Style.RESET_ALL}")
    print(f"{Fore.RED}[-] Failed proxies: {failed}/{total}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}[+] Working proxies saved to: {output_file}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")

if __name__ == "__main__":
    input_file = "http_proxies (1).txt"
    output_file = "working_proxies.txt"
    
    print(f"{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}    PROXY VALIDATOR - Testing Against Google.com{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}\n")
    
    validate_proxies(input_file, output_file, max_workers=50)

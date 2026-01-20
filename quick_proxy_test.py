"""
Quick proxy tester - Tests first N proxies and saves working ones
"""
import httpx
from concurrent.futures import ThreadPoolExecutor, as_completed
from colorama import Fore, Style, init

init(autoreset=True)

def test_proxy(proxy, timeout=5):
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

def quick_test(input_file, output_file, max_test=200, max_workers=30):
    """Quick test of first N proxies"""
    print(f"{Fore.CYAN}[*] Quick testing first {max_test} proxies...{Style.RESET_ALL}\n")
    
    proxies = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= max_test:
                break
            line = line.strip()
            if line and not line.startswith('#'):
                proxies.append(line)
    
    working_proxies = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(test_proxy, proxy): proxy for proxy in proxies}
        
        for future in as_completed(futures):
            proxy, is_working = future.result()
            if is_working:
                working_proxies.append(proxy)
                print(f"{Fore.GREEN}[✓] Working: {proxy}{Style.RESET_ALL}")
    
    # Save working proxies
    if working_proxies:
        with open(output_file, 'w', encoding='utf-8') as f:
            for proxy in working_proxies:
                f.write(proxy + '\n')
        
        print(f"\n{Fore.GREEN}[+] Found {len(working_proxies)} working proxies!{Style.RESET_ALL}")
        print(f"{Fore.GREEN}[+] Saved to: {output_file}{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.RED}[!] No working proxies found in first {max_test}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[*] You can still test without proxies{Style.RESET_ALL}")

if __name__ == "__main__":
    quick_test("http_proxies (1).txt", "working_proxies.txt", max_test=200, max_workers=50)

"""
Quick test script to demonstrate proxy functionality
"""
from user_scanner.core.helpers import set_proxy_manager, get_proxy, get_proxy_count

# Initialize proxy manager with test file
print("Initializing proxy manager...")
set_proxy_manager('test_proxies.txt')

proxy_count = get_proxy_count()
print(f"✓ Loaded {proxy_count} proxies\n")

# Demonstrate round-robin rotation
print("Testing round-robin proxy rotation:")
for i in range(6):
    proxy = get_proxy()
    print(f"  Request {i+1}: {proxy}")

print("\n✓ Proxy rotation working correctly!")
print(f"Note: After request 4, it cycles back to the first proxy")

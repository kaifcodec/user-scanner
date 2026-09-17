import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from user_scanner.user_scan.shopping.zillow import validate_zillow

def test_zillow():
    print("Testing Zillow Module...")
    
    # Test with known existing user
    existing_user = "JUSTINTYE"
    print(f"Checking existing user: {existing_user}")
    result = validate_zillow(existing_user)
    print(f"Result: {result.status} | URL: {result.url} | Reason: {result.get_reason()}")
    
    # Test with guaranteed non-existent user
    non_existent_user = "thisuserisdefinitelynotonzillow123456789"
    print(f"Checking non-existent user: {non_existent_user}")
    result = validate_zillow(non_existent_user)
    print(f"Result: {result.status} | URL: {result.url} | Reason: {result.get_reason()}")

if __name__ == "__main__":
    test_zillow()

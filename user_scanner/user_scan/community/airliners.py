import hashlib
import re
from user_scanner.core.orchestrator import Result, make_request

def validate_airliners(user):
    url = f"https://www.airliners.net/user/{user}/profile"
    
    try:
        response = make_request(url, follow_redirects=True)
        
        if response.status_code == 202:
            html = response.text
            nonce_match = re.search(r"challenge_nonce:'([^']+)'", html)
            hmac_match = re.search(r"challenge_hmac:'([^']+)'", html)
            diff_match = re.search(r"difficulty:'([^']+)'", html)
            char_match = re.search(r"difficulty_char:'([^']+)'", html)
            issued_match = re.search(r"issued_at:'([^']+)'", html)
            
            if not all([nonce_match, hmac_match, diff_match, char_match, issued_match]):
                return Result.error("Failed to parse PoW challenge parameters", url=url)
                
            nonce = nonce_match.group(1)
            hmac = hmac_match.group(1)
            diff = int(diff_match.group(1))
            char = char_match.group(1)
            issued = issued_match.group(1)
            
            target_prefix = char * diff
            prefix_str = nonce + issued
            
            pow_bypass = None
            for i in range(1, 10000000):
                u = str(i)
                data = (prefix_str + u).encode('utf-8')
                hash_hex = hashlib.sha256(data).hexdigest()
                
                if hash_hex.startswith(target_prefix):
                    pow_bypass = f"{nonce}|{issued}|{u}|{hash_hex}|{hmac}"
                    break
                    
            if pow_bypass:
                response = make_request(
                    url, 
                    follow_redirects=True, 
                    cookies={"pow_bypass": pow_bypass}
                )
            else:
                return Result.error("Failed to solve PoW challenge", url=url)
                
        if response.status_code == 404:
            return Result.available(url=url)
        if response.status_code == 200:
            return Result.taken(url=url)
            
        return Result.error(f"Unexpected status code: {response.status_code}", url=url)
        
    except Exception as e:
        return Result.error(e, url=url)

import hashlib
import re
from user_scanner.core.helpers import get_random_user_agent
from user_scanner.core.orchestrator import Result, make_request

def validate_defensivecarry(user: str) -> Result:
    url = f"https://www.defensivecarry.com/members/?username={user}"
    
    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    
    try:
        response = make_request(url, follow_redirects=False, http2=False, headers=headers)
        
        if response.status_code == 202:
            html_text = response.text
            nonce_match = re.search(r"challenge_nonce:'([^']+)'", html_text)
            hmac_match = re.search(r"challenge_hmac:'([^']+)'", html_text)
            diff_match = re.search(r"difficulty:'([^']+)'", html_text)
            char_match = re.search(r"difficulty_char:'([^']+)'", html_text)
            issued_match = re.search(r"issued_at:'([^']+)'", html_text)
            
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
                    follow_redirects=False, 
                    http2=False,
                    headers=headers,
                    cookies={"pow_bypass": pow_bypass}
                )
            else:
                return Result.error("Failed to solve PoW challenge", url=url)
                
        if response.status_code in [301, 302, 303]:
            return Result.taken(url=url)
        elif response.status_code == 200 or response.status_code == 404:
            return Result.available(url=url)
            
        return Result.error(f"Unexpected status code: {response.status_code}", url=url)
        
    except Exception as e:
        return Result.error(e, url=url)

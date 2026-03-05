import httpx
import json
import uuid
import hashlib
import base64
import secrets
from user_scanner.core.result import Result

def generate_pkce_challenge():
    verifier = secrets.token_urlsafe(32)
    sha256_hash = hashlib.sha256(verifier.encode('ascii')).digest()
    challenge = base64.urlsafe_b64encode(sha256_hash).decode('ascii').replace('=', '')
    return challenge

async def _check(email: str) -> Result:
    url = "https://identity.walmart.com/orchestra/idp/graphql"
    show_url = "https://walmart.com"

    uid = str(uuid.uuid4()).replace("-", "")
    trace_id = f"00-{uid[:32]}-{uid[:16]}-00"
    # Use a shorter correlation ID format seen in recent captures
    corr_id = secrets.token_urlsafe(24)
    dynamic_challenge = generate_pkce_challenge()

    payload = {
        "query": "query GetLoginOptions($input:UserOptionsInput!){getLoginOptions(input:$input){loginOptions{...LoginOptionsFragment}canUseEmailOTP phoneCollectionRequired authCode errors{...LoginOptionsErrorFragment}}}fragment LoginOptionsFragment on LoginOptions{loginId loginIdType emailId phoneNumber{number countryCode isoCountryCode}canUsePassword canUsePhoneOTP canUseEmailOTP loginPhoneLastFour maskedPhoneNumberDetails{loginPhoneLastFour countryCode isoCountryCode}loginMaskedEmailId signInPreference loginPreference lastLoginPreference hasRemainingFactors isPhoneConnected otherAccountsWithPhone loginMaskedEmailId hasPasskeyOnProfile accountDomain residencyRegion{residencyCountryCode residencyRegionCode}isIdentityMergeRequired}fragment LoginOptionsErrorFragment on IdentityLoginOptionsError{code message version}",
        "variables": {
            "input": {
                "loginId": email,
                "loginIdType": "EMAIL",
                "ssoOptions": {
                    "wasConsentCaptured": True,
                    "callbackUrl": "https://www.walmart.com/account/verifyToken",
                    "clientId": "5f3fb121-076a-45f6-9587-249f0bc160ff",
                    "scope": "openid email offline_access",
                    "state": "/account/delete-account",
                    "challenge": dynamic_challenge
                }
            }
        }
    }

    headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json",
        'Accept-Encoding': "identity",
        'Content-Type': "application/json",
        'x-o-mart': "B2C",
        'x-o-gql-query': "query GetLoginOptions",
        'sec-ch-ua-platform': '"Android"',
        'x-o-segment': "oaoh",
        'device_profile_ref_id': "xpmjgxfheteohb199lo0r5qewtwjywqaifje",
        'sec-ch-ua': '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
        'x-enable-server-timing': "1",
        'sec-ch-ua-mobile': "?1",
        'x-latency-trace': "1",
        'traceparent': trace_id,
        'wm_mp': "true",
        'x-apollo-operation-name': "GetLoginOptions",
        'tenant-id': "elh9ie",
        'downlink': "10",
        'wm_qos.correlation_id': corr_id,
        'x-o-platform': "rweb",
        'x-o-platform-version': "usweb-1.244.0-11a85c27f6b1cd480b5bbfc2090ace49df92f6fc-2190302r",
        'accept-language': "en-US",
        'x-o-ccm': "server",
        'x-o-bu': "WALMART-US",
        'dpr': "2.75",
        'wm_page_url': f"https://identity.walmart.com/account/login?scope=openid%20email%20offline_access&redirect_uri=https%3A%2F%2Fwww.walmart.com%2Faccount%2FverifyToken&client_id=5f3fb121-076a-45f6-9587-249f0bc160ff&tenant_id=elh9ie&code_challenge={dynamic_challenge}&state=%2Faccount%2Fdelete-account",
        'x-o-correlation-id': corr_id,
        'origin': "https://identity.walmart.com",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': f"https://identity.walmart.com/account/login?scope=openid%20email%20offline_access&redirect_uri=https%3A%2F%2Fwww.walmart.com%2Faccount%2FverifyToken&client_id=5f3fb121-076a-45f6-9587-249f0bc160ff&tenant_id=elh9ie&code_challenge={dynamic_challenge}&state=%2Faccount%2Fdelete-account",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, content=json.dumps(payload), headers=headers)

            if response.status_code == 429:
                return Result.error("Rate limited")

            if response.status_code == 412:
                return Result.error("Precondition Failed (412) - Walmart detected session mismatch")

            if response.status_code != 200:
                return Result.error(f"HTTP Error: {response.status_code}")

            data = response.json()
            login_data = data.get("data", {}).get("getLoginOptions", {})
            login_options = login_data.get("loginOptions", {})
            errors = login_data.get("errors", [])

            pref = login_options.get("signInPreference", "")

            if pref in ["PASSWORD", "CHOICE"]:
                if any(err.get("code") == "COMPROMISED" for err in errors):
                    return Result.taken("Account flagged as compromised")
                return Result.taken(url=show_url)

            elif pref == "CREATE":
                return Result.available(url=show_url)

            return Result.error("Unexpected response structure")

    except Exception as e:
        return Result.error(e)

async def validate_walmart(email: str) -> Result:
    return await _check(email)

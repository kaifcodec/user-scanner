import httpx
import json
import uuid
import time
import hashlib
import base64
import secrets
from user_scanner.core.result import Result
from user_scanner.core.helpers import get_random_user_agent


def generate_pkce_challenge():
    # Create a random verifier (between 43-128 chars)
    verifier = secrets.token_urlsafe(32)
    # Hash it with SHA-256
    sha256_hash = hashlib.sha256(verifier.encode('ascii')).digest()
    # Base64URL encode and remove padding
    challenge = base64.urlsafe_b64encode(
        sha256_hash).decode('ascii').replace('=', '')
    return challenge


async def _check(email: str) -> Result:
    url = "https://identity.walmart.com/orchestra/idp/graphql"
    show_url = "https://walmart.com"

    # Dynamic IDs
    uid = str(uuid.uuid4()).replace("-", "")
    trace_id = f"00-{uid[:32]}-{uid[:16]}-00"
    corr_id = str(uuid.uuid4())
    current_ts = int(time.time() * 1000)
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
                    "state": "/orders",
                    "challenge": dynamic_challenge
                }
            }
        }
    }

    headers = {
        'User-Agent': get_random_user_agent(),
        'Accept': "application/json",
        'Accept-Encoding': "identity",
        'Content-Type': "application/json",
        'x-o-mart': "B2C",
        'x-o-gql-query': "query GetLoginOptions",
        'sec-ch-ua-platform': "\"Linux\"",
        'x-o-segment': "oaoh",
        'device_profile_ref_id': "rpyb19h9pul4ki2njkv8zfsblwwbnwuhkm1b",
        'sec-ch-ua': "\"Not(A:Brand\";v=\"8\", \"Chromium\";v=\"144\", \"Google Chrome\";v=\"144\"",
        'x-enable-server-timing': "1",
        'sec-ch-ua-mobile': "?0",
        'baggage': f"requestTs={current_ts},tpid={trace_id}",
        'x-latency-trace': "1",
        'traceparent': trace_id,
        'wm_mp': "true",
        'x-apollo-operation-name': "GetLoginOptions",
        'tenant-id': "elh9ie",
        'downlink': "10",
        'wm_qos.correlation_id': corr_id,
        'x-o-platform': "rweb",
        'x-o-platform-version': "usweb-1.242.0-00e39ccd818f325337906a20cd1bd8a1844c0596-2122244r",
        'accept-language': "en-US",
        'x-o-ccm': "server",
        'x-o-bu': "WALMART-US",
        'dpr': "2.75",
        'wm_page_url': f"https://identity.walmart.com/account/login?scope=openid%20email%20offline_access&redirect_uri=https%3A%2F%2Fwww.walmart.com%2Faccount%2FverifyToken&client_id=5f3fb121-076a-45f6-9587-249f0bc160ff&tenant_id=elh9ie&code_challenge={dynamic_challenge}&state=%2Forders&tp=TrackYourOrder",
        'x-o-correlation-id': corr_id,
        'origin': "https://identity.walmart.com",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': f"https://identity.walmart.com/account/login?scope=openid%20email%20offline_access&redirect_uri=https%3A%2F%2Fwww.walmart.com%2Faccount%2FverifyToken&client_id=5f3fb121-076a-45f6-9587-249f0bc160ff&tenant_id=elh9ie&code_challenge={dynamic_challenge}&state=%2Forders&tp=TrackYourOrder",
        'priority': "u=1, i"
    }

    try:
        async with httpx.AsyncClient(timeout=7.0) as client:
            response = await client.post(url, content=json.dumps(payload), headers=headers)

            if response.status_code == 429:
                return Result.error("Rate limited wait for few minutes")

            if response.status_code == 418:
                return Result.error("Caught by WAF (418), reporting suspicious headers")

            if response.status_code != 200:
                return Result.error(f"HTTP Error: {response.status_code}")

            data = response.json()
            login_options = data.get("data", {}).get(
                "getLoginOptions", {}).get("loginOptions", {})
            errors = data.get("data", {}).get(
                "getLoginOptions", {}).get("errors", [])

            pref = login_options.get("signInPreference", "")

            if pref in ["PASSWORD", "CHOICE"]:
                if any(err.get("code") == "COMPROMISED" for err in errors):
                    return Result.taken("Account is flagged as compromised")
                return Result.taken(url=show_url)

            elif pref == "CREATE":
                return Result.available(url=show_url)

            return Result.error("Unexpected response body structure, report it via GitHub issues")

    except httpx.ConnectTimeout:
        return Result.error("Connection timed out! maybe region blocks")
    except httpx.ReadTimeout:
        return Result.error("Server took too long to respond (Read Timeout)")
    except Exception as e:
        return Result.error(e)


async def validate_walmart(email: str) -> Result:
    return await _check(email)

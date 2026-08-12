import json
import uuid
import hashlib
import base64
import secrets
from user_scanner.core.impersonate import impersonate_request_async
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

    # No User-Agent or client hints: the impersonating transport supplies a set
    # that matches its TLS fingerprint, and overriding half of it re-trips the
    # 412 session-mismatch check.
    headers = {
        'Accept': "application/json",
        'Content-Type': "application/json",
        'x-o-mart': "B2C",
        'x-o-gql-query': "query GetLoginOptions",
        'x-o-segment': "oaoh",
        'device_profile_ref_id': "xpmjgxfheteohb199lo0r5qewtwjywqaifje",
        'x-enable-server-timing': "1",
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
        # Step 1: Request the login page to seed the session cookies; the
        # GraphQL endpoint answers 412 without them. The page URL carries this
        # call's PKCE challenge, so it has to be fetched per check rather than
        # through the shared once-per-session warm-up.
        await impersonate_request_async(
            headers['wm_page_url'],
            headers={
                'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                'Accept-Language': "en-US,en;q=0.9",
            },
            allow_redirects=True,
        )

        # Step 2: Post to the GraphQL endpoint
        response = await impersonate_request_async(
            url, "POST", data=json.dumps(payload), headers=headers
        )

        if response.status_code == 429:
            return Result.error("Rate limited")

        # Walmart answers 412 with a PerimeterX block payload whenever it
        # refuses the request — an unaccepted session, a flagged IP, a blocked
        # region — so the status alone does not name which one.
        if response.status_code == 412:
            return Result.error("Blocked by Walmart bot protection (412)")

        if response.status_code != 200:
            return Result.error(f"HTTP Error: {response.status_code}")

        data = response.json()
        errors = data.get("errors", [])

        # Check if there is an error stating Enum can't represent STEP_UP_REQUIRED
        # This validation failure happens specifically on existing accounts requiring a step-up check
        if errors and any("STEP_UP_REQUIRED" in err.get("message", "") for err in errors):
            return Result.taken(url=show_url)

        login_data = data.get("data", {}).get("getLoginOptions", {})
        if login_data is None:
            return Result.error("GraphQL getLoginOptions returned null")

        login_options = login_data.get("loginOptions", {}) or {}
        login_errors = login_data.get("errors", []) or []

        # Check if errors indicates a non-existent email
        if any(err.get("code") == "EMAIL_ID_INVALID" for err in login_errors):
            return Result.available(url=show_url)

        pref = login_options.get("signInPreference", "")

        if pref in ["PASSWORD", "CHOICE"]:
            if any(err.get("code") == "COMPROMISED" for err in login_errors):
                return Result.taken("Account flagged as compromised")
            return Result.taken(url=show_url)

        if pref == "CREATE":
            return Result.available(url=show_url)

        return Result.error("Unexpected response structure")

    except Exception as e:
        return Result.error(e)

async def validate_walmart(email: str) -> Result:
    return await _check(email)

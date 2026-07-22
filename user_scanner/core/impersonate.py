import threading
from typing import Callable, Literal, Optional

from curl_cffi import requests as cffi

from user_scanner.core.helpers import get_global_timeout, get_proxy
from user_scanner.core.result import Result

DEFAULT_IMPERSONATE = "chrome"
DEFAULT_TIMEOUT = 15.0

_sessions: dict[tuple, cffi.Session] = {}
_warmed: set[tuple] = set()
_lock = threading.Lock()


def impersonate_validate(
    url: str,
    func: Callable[[cffi.Response], Result],
    warmup_url: Optional[str] = None,
    impersonate: str = DEFAULT_IMPERSONATE,
    show_url: Optional[str] = None,
    **kwargs,
) -> Result:
    """Like ``generic_validate`` but routes the request through a browser-
    impersonating curl_cffi session, so it clears TLS-fingerprint bot walls
    (e.g. DataDome) that reject Python's default TLS stack regardless of headers.

    ``warmup_url`` is fetched once per session to obtain the clearance cookie the
    protected endpoint requires; a blocked warm-up still sets that cookie.
    """
    display_url = show_url or url
    try:
        response = impersonate_request(
            url, warmup_url=warmup_url, impersonate=impersonate, **kwargs
        )
        return func(response).update(url=display_url)
    except Exception as e:
        return Result.error(e, url=display_url)


def impersonate_request(
    url: str,
    method: Literal["GET", "POST"] = "GET",
    warmup_url: Optional[str] = None,
    impersonate: str = DEFAULT_IMPERSONATE,
    **kwargs,
) -> cffi.Response:
    """Issue a single request through a warmed, cookie-persistent browser-
    impersonating session and return the raw response. Reuses the same cached
    session as ``impersonate_validate`` for a given (impersonate, proxy), so a
    follow-up call (e.g. a profile API request) inherits the clearance cookie.
    """
    session = _get_warm_session(impersonate, get_proxy(), warmup_url)
    kwargs.setdefault("timeout", _timeout())
    kwargs.setdefault("allow_redirects", False)
    return session.request(method, url, **kwargs)


def _get_warm_session(
    impersonate: str, proxy: Optional[str], warmup_url: Optional[str]
) -> cffi.Session:
    key = (impersonate, proxy)
    with _lock:
        session = _sessions.get(key)
        if session is None:
            session = cffi.Session(
                # curl_cffi types this as a browser-name Literal; the value is a
                # validated runtime string, so widen it here only.
                impersonate=impersonate,  # type: ignore[arg-type]
                proxies={"http": proxy, "https": proxy} if proxy else None,
            )
            _sessions[key] = session

        if warmup_url and key not in _warmed:
            # A blocked (403) warm-up still returns normally and sets the cookie;
            # only a network error leaves the session unwarmed for a later retry.
            session.get(warmup_url, timeout=_timeout())
            _warmed.add(key)

    return session


def _timeout() -> float:
    # Honour the CLI -t flag (get_global_timeout), matching make_request();
    # fall back to DEFAULT_TIMEOUT when the user has not set one.
    global_timeout = get_global_timeout()
    return global_timeout if global_timeout is not None else DEFAULT_TIMEOUT

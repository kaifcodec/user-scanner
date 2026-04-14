from user_scanner.core.result import Result
from user_scanner.user_scan.social import facebook


def test_process_profile_response_taken():
    result = facebook._process_profile_response(
        200,
        '<meta property="og:title" content="Mark Zuckerberg" />'
        '<meta property="og:url" content="https://www.facebook.com/zuck" />'
    )

    assert result == Result.taken()


def test_process_profile_response_available():
    result = facebook._process_profile_response(
        200,
        'This content isn\'t available right now","body":"When this happens, '
        "it's usually because the owner only shared it with a small group"
    )

    assert result == Result.available()


def test_process_profile_response_ambiguous():
    result = facebook._process_profile_response(200, "<html><title>Facebook</title></html>")

    assert result == Result.error()


def test_validate_facebook_uses_public_profile_url(monkeypatch):
    captured = {}

    class FakeResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return (
                b'<meta property="og:title" content="Meta" />'
                b'<meta property="og:url" content="https://www.facebook.com/Meta" />'
            )

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["headers"] = dict(request.header_items())
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(facebook, "urlopen", fake_urlopen)

    result = facebook.validate_facebook("Meta")

    assert result == Result.taken()
    assert captured["url"] == "https://www.facebook.com/Meta"
    assert captured["timeout"] == 8.0
    assert captured["headers"]["User-agent"]

import json

from user_scanner.core.nextjs import (
    iter_next_app_flight_chunks,
    parse_next_pages_data,
    parse_next_pages_redirect,
)


def test_parse_next_pages_data():
    document = """
        <script nonce="abc" id="__NEXT_DATA__" type="application/json">
            {"props":{"pageProps":{"username":"alice"}}}
        </script>
    """
    assert parse_next_pages_data(document) == {
        "props": {"pageProps": {"username": "alice"}}
    }
    assert parse_next_pages_data('<script id="__NEXT_DATA__">{bad}</script>') is None


def test_parse_next_pages_data_unescapes_encoded_json():
    document = (
        '<script id="__NEXT_DATA__">'
        "{&quot;props&quot;:{&quot;pageProps&quot;:{}}}"
        "</script>"
    )
    assert parse_next_pages_data(document) == {"props": {"pageProps": {}}}


def test_next_app_flight_chunks_and_pages_redirect():
    chunks = ['0:{"followersCount":7}', '1:{"name":"Alice"}']
    document = "".join(
        f"<script>self.__next_f.push([1,{json.dumps(chunk)}])</script>"
        for chunk in chunks
    )
    assert list(iter_next_app_flight_chunks(document)) == chunks
    assert parse_next_pages_redirect(
        {"__N_REDIRECT": "/", "__N_REDIRECT_STATUS": 307}
    ) == ("/", 307)
    assert parse_next_pages_redirect({"__N_REDIRECT": "/"}) is None

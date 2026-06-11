from user_scanner.core.formatter import into_csv, into_json
from user_scanner.core.result import Result


def test_get_result_output_formats():
    res = Result.available(username="alice", site_name="ExampleSite", category="Cat")

    out_console = res.get_console_output()
    assert "Not Found" in out_console
    assert "ExampleSite" in out_console
    assert "alice" in out_console

    out_json = into_json([res])
    assert '"username": "alice"' in out_json
    assert '"site_name": "ExampleSite"' in out_json

    out_csv = into_csv([res])
    assert "alice" in out_csv
    assert "ExampleSite" in out_csv

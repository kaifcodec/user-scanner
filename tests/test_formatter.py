from user_scanner.core.formatter import into_csv, into_json, indentate, INDENT
from user_scanner.core.result import Result


def test_indentate():
    assert indentate("", -1) == ""
    assert indentate("", 0) == ""
    assert indentate("", 2) == 2 * INDENT

    msg = ("This is a test message\n"
           "made to test the identation\n"
           "and shouldn't be changed.")

    for i in range(0, 4):
        new = indentate(msg, i)
        for line in new.split("\n"):
            assert line.find(INDENT * i) == 0


def test_get_result_output_formats():
    res = Result.available(
        username="alice", site_name="ExampleSite", category="Cat")

    out_console = res.get_console_output()
    assert "Available" in out_console
    assert "ExampleSite" in out_console
    assert "alice" in out_console

    out_json = into_json([res])
    assert '"username": "alice"' in out_json
    assert '"site_name": "ExampleSite"' in out_json

    out_csv = into_csv([res])
    assert "alice" in out_csv
    assert "ExampleSite" in out_csv

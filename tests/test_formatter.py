from user_scanner.core.formatter import CSV_HEADER, into_csv, into_json
from user_scanner.core.result import Result


def test_get_result_output_formats():
    res = Result.available(username="alice", site_name="ExampleSite", category="Cat")
    res2 = Result.available(username="bob", site_name="ExampleSite", category="Cat")

    out_console = res.get_console_output()
    assert "Not Found" in out_console
    assert "ExampleSite" in out_console
    assert "alice" in out_console

    out_json = into_json([res])
    assert '"username": "alice"' in out_json
    assert '"site_name": "ExampleSite"' in out_json

    # Test CSV output with header included(Default behavior)
    out_csv = into_csv([res])
    assert "alice" in out_csv
    assert "ExampleSite" in out_csv

    # Test CSV output with header excluded
    out_csv_no_header = into_csv([res], include_header=False)
    assert "alice" in out_csv_no_header
    assert "ExampleSite" in out_csv_no_header
    assert out_csv_no_header.count(CSV_HEADER) == 0

    # Test CSV output with multiple results and header included
    first = into_csv([res], include_header=True)
    second = into_csv([res2], include_header=False)

    full = first + "\n" + second
    
    assert full.count(CSV_HEADER) == 1
    assert "alice" in full
    assert "bob" in full

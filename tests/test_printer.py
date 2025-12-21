from user_scanner.cli.printer import Printer, indentate, INDENT
from user_scanner.core.result import Result
import pytest


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


def test_creation():
    assert Printer("console").mode == "console"
    assert Printer("csv").mode == "csv"
    assert Printer("json").mode == "json"

    with pytest.raises(ValueError):
        Printer(2)


def test_is_properties():
    p = Printer("console")
    assert p.is_console is True
    assert p.is_csv is False
    assert p.is_json is False

    p = Printer("csv")
    assert p.is_console is False
    assert p.is_csv is True
    assert p.is_json is False

    p = Printer("json")
    assert p.is_console is False
    assert p.is_csv is False
    assert p.is_json is True


def test_get_result_output_formats():
    res = Result.available(username="alice", site_name="ExampleSite", category="Cat")

    p_console = Printer("console")
    out_console = p_console.get_result_output(res)
    assert "Available" in out_console
    assert "ExampleSite" in out_console
    assert "alice" in out_console

    p_json = Printer("json")
    out_json = p_json.get_result_output(res)
    assert '"username": "alice"' in out_json
    assert '"site_name": "ExampleSite"' in out_json

    p_csv = Printer("csv")
    out_csv = p_csv.get_result_output(res)
    assert "alice" in out_csv
    assert "ExampleSite" in out_csv

from user_scanner.cli.printer import Printer, indentate, INDENT
import pytest


def test_identate():
    assert indentate("", -1) == ""
    assert indentate("", 0) == ""
    assert indentate("", 2) == 2*INDENT

    msg = ("This is a test message\n"
           "made to test the identation\n"
           "and shouldn't be changed.")

    for i in range(0, 10):
        new = indentate(msg, i)
        print(new)
        for line in new.split("\n"):
            assert line.find(INDENT * i) == 0


def test_creation():
    Printer("console").mode == "console"
    Printer("csv").mode == "csv"
    Printer("json").mode == "json"

    with pytest.raises(ValueError):
        Printer(2)


def test_is():
    p = Printer("console")
    assert p.is_console == True
    assert p.is_csv == False
    assert p.is_json == False

    p = Printer("csv")
    assert p.is_console == False
    assert p.is_csv == True
    assert p.is_json == False

    p = Printer("json")
    assert p.is_console == False
    assert p.is_csv == False
    assert p.is_json == True

from user_scanner.core.helpers import ScanConfig
from user_scanner.core.result import Result
from user_scanner.core.terminal import rich_safe, scanning_description, strip_terminal_controls


def test_controls_are_removed_and_the_text_stays():
    raw = "a\x1b[31mX\x1b[0m\rHIDE\b\bOK\u202eplain"
    cleaned = strip_terminal_controls(raw)
    assert "\x1b" not in cleaned
    assert "\r" not in cleaned
    assert "\b" not in cleaned
    assert "\u202e" not in cleaned
    assert "aX" in cleaned
    assert "HIDE" in cleaned
    assert "plain" in cleaned


def test_osc8_link_is_not_a_link():
    raw = "\x1b]8;;https://evil.example\x07click here\x1b]8;;\x07"
    cleaned = strip_terminal_controls(raw)
    assert "\x1b" not in cleaned
    assert "https://evil.example" not in cleaned
    assert "click here" in cleaned


def test_ordinary_unicode_is_preserved():
    assert strip_terminal_controls("café — 名字") == "café — 名字"
    assert "\n" in strip_terminal_controls("one\ntwo")
    assert "\t" in strip_terminal_controls("one\ttwo")


def test_rich_markup_is_escaped_only_for_rich():
    assert rich_safe("[bold]hack[/bold]") == r"\[bold]hack\[/bold]"
    assert strip_terminal_controls("[bold]hack[/bold]") == "[bold]hack[/bold]"


def test_progress_description_cannot_break_the_style():
    description = scanning_description("user[red]x", "Site\x1b[0m")
    assert description.startswith("[cyan]")
    assert r"\[red]" in description
    assert "\x1b" not in description


def test_console_output_renders_hostile_fields_inertly():
    result = Result.taken(
        username="a\x1b[31mX",
        reason="ok\rHIDE",
        site_name="Site\x1b]8;;https://evil.example\x07click",
        url="https://example.com/\x1b[0m",
        extra={"bio\u202e": "line\b1\nline2"},
    )
    text = result.get_console_output(ScanConfig(verbose=True))
    # Colorama's own styles stay. The sequences that arrived in the data do not.
    assert "\x1b]8" not in text
    assert "\x1b[31m" not in text
    assert "\r" not in text
    assert "\b" not in text
    assert "\u202e" not in text
    assert "aX" in text
    assert "okHIDE" in text
    assert "click" in text
    assert "line2" in text

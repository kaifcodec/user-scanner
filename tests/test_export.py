import contextlib
import io
import json
import sys
import pytest

from user_scanner.core.result import Result
import user_scanner.__main__ as cli


def test_json_export_new_file(monkeypatch, tmp_path):
    output = tmp_path / "new_report.json"
    monkeypatch.setattr(
        sys, "argv", ["user-scanner", "-u", "audit", "-f", "json", "-o", str(output)]
    )
    monkeypatch.setattr(cli, "check_for_updates", lambda: None)
    monkeypatch.setattr(cli, "print_banner", lambda: None)
    monkeypatch.setattr(
        cli, "run_user_full", lambda *args: [Result.taken(username="audit", site_name="Example")]
    )

    with contextlib.redirect_stdout(io.StringIO()) as captured:
        cli.main()

    assert output.exists()
    data = json.loads(output.read_text(encoding="utf-8"))
    assert len(data) == 1
    assert data[0]["username"] == "audit"
    assert "JSON Results saved" in captured.getvalue()


def test_json_export_append_valid_existing(monkeypatch, tmp_path):
    output = tmp_path / "report.json"
    initial_data = [{"username": "prior_user", "site_name": "PriorSite"}]
    output.write_text(json.dumps(initial_data), encoding="utf-8")

    monkeypatch.setattr(
        sys, "argv", ["user-scanner", "-u", "audit", "-f", "json", "-o", str(output)]
    )
    monkeypatch.setattr(cli, "check_for_updates", lambda: None)
    monkeypatch.setattr(cli, "print_banner", lambda: None)
    monkeypatch.setattr(
        cli, "run_user_full", lambda *args: [Result.taken(username="audit", site_name="Example")]
    )

    with contextlib.redirect_stdout(io.StringIO()) as captured:
        cli.main()

    data = json.loads(output.read_text(encoding="utf-8"))
    assert len(data) == 2
    assert data[0]["username"] == "prior_user"
    assert data[1]["username"] == "audit"
    assert "JSON Results saved" in captured.getvalue()


@pytest.mark.parametrize(
    "corrupt_content",
    [
        '[{"prior": "truncated"}',
        '{"prior": "valid_object_not_list"}',
        '"string_not_list"',
        '42',
    ],
)
def test_json_export_preserves_corrupt_existing_file(monkeypatch, tmp_path, corrupt_content):
    output = tmp_path / "report.json"
    output.write_text(corrupt_content, encoding="utf-8")

    monkeypatch.setattr(
        sys, "argv", ["user-scanner", "-u", "audit", "-f", "json", "-o", str(output)]
    )
    monkeypatch.setattr(cli, "check_for_updates", lambda: None)
    monkeypatch.setattr(cli, "print_banner", lambda: None)
    monkeypatch.setattr(
        cli, "run_user_full", lambda *args: [Result.taken(username="audit", site_name="Example")]
    )

    with contextlib.redirect_stdout(io.StringIO()) as captured:
        cli.main()

    # Original corrupt file bytes must remain untouched
    assert output.read_text(encoding="utf-8") == corrupt_content
    stdout = captured.getvalue()
    assert "Failed to append to existing JSON file" in stdout
    assert "JSON Results saved" not in stdout


def test_json_export_empty_existing_file(monkeypatch, tmp_path):
    output = tmp_path / "empty_report.json"
    output.write_text("", encoding="utf-8")

    monkeypatch.setattr(
        sys, "argv", ["user-scanner", "-u", "audit", "-f", "json", "-o", str(output)]
    )
    monkeypatch.setattr(cli, "check_for_updates", lambda: None)
    monkeypatch.setattr(cli, "print_banner", lambda: None)
    monkeypatch.setattr(
        cli, "run_user_full", lambda *args: [Result.taken(username="audit", site_name="Example")]
    )

    with contextlib.redirect_stdout(io.StringIO()) as captured:
        cli.main()

    data = json.loads(output.read_text(encoding="utf-8"))
    assert len(data) == 1
    assert data[0]["username"] == "audit"
    assert "JSON Results saved" in captured.getvalue()


def test_bulk_targets_stay_inside_the_output_directory(monkeypatch, tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    secret = tmp_path / "secret.txt"
    secret.write_text("keep", encoding="utf-8")
    names = tmp_path / "names.txt"
    names.write_text(
        "\n".join(
            [
                "../../secret.txt",
                str(secret),
                "a\u2215b",
                "a\uff0fb",
                "ok",
            ]
        ),
        encoding="utf-8",
    )
    # The slug for the last target is predictable. A symlink at that name
    # points outside the output directory and must not be followed.
    planted = out / "report_005_ok.json"
    planted.symlink_to(secret)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "user-scanner",
            "-uf",
            str(names),
            "-f",
            "json",
            "-o",
            str(out / "report.json"),
        ],
    )
    monkeypatch.setattr(cli, "check_for_updates", lambda: None)
    monkeypatch.setattr(cli, "print_banner", lambda: None)
    monkeypatch.setattr(
        cli, "run_user_full", lambda *args: [Result.taken(site_name="Example")]
    )

    with contextlib.redirect_stdout(io.StringIO()) as captured:
        cli.main()

    assert secret.read_text(encoding="utf-8") == "keep"
    assert planted.is_symlink()
    reports = [path for path in out.iterdir() if path.is_file() and not path.is_symlink()]
    assert reports
    for path in reports:
        assert path.resolve().is_relative_to(out.resolve())
    stdout = captured.getvalue()
    assert "Refusing to write scan output outside" in stdout
    assert "JSON Results saved" in stdout

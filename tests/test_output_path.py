import pytest

from user_scanner.core.output_path import export_path_for_target, slug_target


def test_slug_drops_traversal_and_unicode_separators():
    assert slug_target("../../chosen/path") == "chosen_path"
    assert slug_target(r"..\..\chosen\path") == "chosen_path"
    assert "/" not in slug_target("/tmp/absolute")
    assert slug_target("a\u2215b") == "a_b"
    assert slug_target("a\uff0fb") == "a_b"
    assert slug_target("a\x00b\r\nc") == "a_b_c"
    assert slug_target("...") == "target"
    assert slug_target("") == "target"


def test_single_requested_path_is_the_caller_choice(tmp_path):
    requested = tmp_path / "report.json"
    path = export_path_for_target(
        requested=str(requested),
        target="../../secret",
        index=1,
        multiple=False,
        default_ext="json",
    )
    assert path == requested


def test_bulk_names_stay_inside_the_requested_directory(tmp_path):
    requested = tmp_path / "out" / "report.json"
    path = export_path_for_target(
        requested=str(requested),
        target="../../secret.txt",
        index=1,
        multiple=True,
        default_ext="json",
    )
    assert path == (tmp_path / "out" / "report_001_secret.txt.json").resolve()
    assert path.is_relative_to(tmp_path.resolve())


def test_symlink_that_leaves_the_output_directory_is_refused(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    secret = tmp_path / "secret.txt"
    secret.write_text("keep", encoding="utf-8")
    link = out / "report_001_ok.json"
    link.symlink_to(secret)

    with pytest.raises(ValueError, match="outside"):
        export_path_for_target(
            requested=str(out / "report.json"),
            target="ok",
            index=1,
            multiple=True,
            default_ext="json",
        )

    assert secret.read_text(encoding="utf-8") == "keep"


def test_default_single_target_name_is_a_slug(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    path = export_path_for_target(
        requested=None,
        target="../../chosen/path",
        index=1,
        multiple=False,
        default_ext="json",
    )
    assert path == (tmp_path / "chosen_path_report.json").resolve()
    assert path.parent == tmp_path.resolve()


def test_parent_of_a_relative_request_is_resolved(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    path = export_path_for_target(
        requested="nested/report.json",
        target="ok",
        index=2,
        multiple=True,
        default_ext="json",
    )
    assert path == (tmp_path / "nested" / "report_002_ok.json").resolve()

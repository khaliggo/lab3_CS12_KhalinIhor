#!/usr/bin/env python3
"""Pytest suite for task2.py (clean utility)."""
import os
import sys
import pytest
import task2
from task2 import (
    find_empty_files,
    find_empty_dirs,
    delete_files,
    delete_dirs,
    _warn,
    _confirm,
    _print_list,
)

sys.path.insert(0, os.path.dirname(__file__))


@pytest.fixture()
def tree(tmp_path):
    """
    Build a directory tree with known empty / non-empty entries:

    tmp_path/
        empty_file.txt          (0 bytes)
        nonempty_file.txt       (has content)
        empty_dir/              (empty directory)
        nonempty_dir/
            child.txt           (has content)
        nested/
            inner_empty/        (empty directory inside nested)
    """
    (tmp_path / "empty_file.txt").write_bytes(b"")
    (tmp_path / "nonempty_file.txt").write_text("hello")

    (tmp_path / "empty_dir").mkdir()

    nd = tmp_path / "nonempty_dir"
    nd.mkdir()
    (nd / "child.txt").write_text("content")

    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "inner_empty").mkdir()

    return tmp_path


# ===========================================================================
# find_empty_files
# ===========================================================================

class TestFindEmptyFiles:
    def test_finds_empty_file(self, tree):
        result = find_empty_files(str(tree))
        names = [os.path.basename(p) for p in result]
        assert "empty_file.txt" in names

    def test_excludes_nonempty_file(self, tree):
        result = find_empty_files(str(tree))
        names = [os.path.basename(p) for p in result]
        assert "nonempty_file.txt" not in names

    def test_returns_list(self, tree):
        assert isinstance(find_empty_files(str(tree)), list)

    def test_no_files_in_empty_root(self, tmp_path):
        assert find_empty_files(str(tmp_path)) == []

    def test_all_nonempty_gives_empty_list(self, tmp_path):
        (tmp_path / "a.txt").write_text("data")
        (tmp_path / "b.txt").write_text("more")
        assert find_empty_files(str(tmp_path)) == []

    def test_multiple_empty_files(self, tmp_path):
        for name in ("x.txt", "y.txt", "z.txt"):
            (tmp_path / name).write_bytes(b"")
        result = find_empty_files(str(tmp_path))
        assert len(result) == 3

    def test_recursive_discovery(self, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "deep_empty.txt").write_bytes(b"")
        result = find_empty_files(str(tmp_path))
        names = [os.path.basename(p) for p in result]
        assert "deep_empty.txt" in names

    def test_oserror_on_stat_warns(self, tmp_path, monkeypatch, capsys):
        (tmp_path / "f.txt").write_bytes(b"")
        original_getsize = os.path.getsize

        def fake_getsize(path):
            if path.endswith("f.txt"):
                raise OSError(13, "Permission denied")
            return original_getsize(path)

        monkeypatch.setattr(os.path, "getsize", fake_getsize)
        find_empty_files(str(tmp_path))
        err = capsys.readouterr().err
        assert "warning" in err


# ===========================================================================
# find_empty_dirs
# ===========================================================================

class TestFindEmptyDirs:
    def test_finds_empty_dir(self, tree):
        result = find_empty_dirs(str(tree))
        names = [os.path.basename(p) for p in result]
        assert "empty_dir" in names

    def test_excludes_root(self, tree):
        result = find_empty_dirs(str(tree))
        abs_root = os.path.abspath(str(tree))
        assert abs_root not in result

    def test_excludes_nonempty_dir(self, tree):
        result = find_empty_dirs(str(tree))
        names = [os.path.basename(p) for p in result]
        assert "nonempty_dir" not in names

    def test_returns_list(self, tree):
        assert isinstance(find_empty_dirs(str(tree)), list)

    def test_no_empty_dirs_returns_empty(self, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "file.txt").write_text("x")
        assert find_empty_dirs(str(tmp_path)) == []

    def test_nested_empty_dirs_all_reported(self, tmp_path):
        a = tmp_path / "a"
        a.mkdir()
        b = a / "b"
        b.mkdir()
        result = find_empty_dirs(str(tmp_path))
        names = [os.path.basename(p) for p in result]
        assert "a" in names
        assert "b" in names

    def test_deepest_first_ordering(self, tmp_path):
        a = tmp_path / "a"
        a.mkdir()
        b = a / "b"
        b.mkdir()
        result = find_empty_dirs(str(tmp_path))
        # deepest (longest path) comes first
        assert len(result[0]) >= len(result[-1])

    def test_inner_empty_reported(self, tree):
        result = find_empty_dirs(str(tree))
        names = [os.path.basename(p) for p in result]
        assert "inner_empty" in names

    def test_parent_with_only_empty_children_reported(self, tmp_path):
        parent = tmp_path / "parent"
        parent.mkdir()
        (parent / "child").mkdir()
        result = find_empty_dirs(str(tmp_path))
        names = [os.path.basename(p) for p in result]
        assert "parent" in names
        assert "child" in names

    def test_parent_with_file_not_reported(self, tmp_path):
        parent = tmp_path / "parent"
        parent.mkdir()
        (parent / "file.txt").write_text("x")
        (parent / "child").mkdir()
        result = find_empty_dirs(str(tmp_path))
        names = [os.path.basename(p) for p in result]
        assert "parent" not in names
        assert "child" in names


# ===========================================================================
# delete_files
# ===========================================================================

class TestDeleteFiles:
    def test_deletes_file(self, tmp_path):
        f = tmp_path / "empty.txt"
        f.write_bytes(b"")
        delete_files([str(f)])
        assert not f.exists()

    def test_prints_deleted_message(self, tmp_path, capsys):
        f = tmp_path / "empty.txt"
        f.write_bytes(b"")
        delete_files([str(f)])
        out = capsys.readouterr().out
        assert "Deleted file" in out

    def test_dry_run_does_not_delete(self, tmp_path):
        f = tmp_path / "empty.txt"
        f.write_bytes(b"")
        delete_files([str(f)], dry_run=True)
        assert f.exists()

    def test_dry_run_prints_would_delete(self, tmp_path, capsys):
        f = tmp_path / "empty.txt"
        f.write_bytes(b"")
        delete_files([str(f)], dry_run=True)
        out = capsys.readouterr().out
        assert "dry-run" in out
        assert "would delete file" in out

    def test_oserror_warns(self, tmp_path, monkeypatch, capsys):
        f = tmp_path / "f.txt"
        f.write_bytes(b"")

        def fake_remove(path):
            raise OSError(13, "Permission denied")

        monkeypatch.setattr(os, "remove", fake_remove)
        delete_files([str(f)])
        err = capsys.readouterr().err
        assert "warning" in err

    def test_empty_list_no_output(self, capsys):
        delete_files([])
        assert capsys.readouterr().out == ""

    def test_deletes_multiple_files(self, tmp_path):
        files = []
        for name in ("a.txt", "b.txt", "c.txt"):
            f = tmp_path / name
            f.write_bytes(b"")
            files.append(str(f))
        delete_files(files)
        for f in files:
            assert not os.path.exists(f)


# ===========================================================================
# delete_dirs
# ===========================================================================

class TestDeleteDirs:
    def test_deletes_directory(self, tmp_path):
        d = tmp_path / "empty_dir"
        d.mkdir()
        delete_dirs([str(d)])
        assert not d.exists()

    def test_prints_deleted_message(self, tmp_path, capsys):
        d = tmp_path / "empty_dir"
        d.mkdir()
        delete_dirs([str(d)])
        out = capsys.readouterr().out
        assert "Deleted directory" in out

    def test_dry_run_does_not_delete(self, tmp_path):
        d = tmp_path / "empty_dir"
        d.mkdir()
        delete_dirs([str(d)], dry_run=True)
        assert d.exists()

    def test_dry_run_prints_would_delete(self, tmp_path, capsys):
        d = tmp_path / "empty_dir"
        d.mkdir()
        delete_dirs([str(d)], dry_run=True)
        out = capsys.readouterr().out
        assert "dry-run" in out
        assert "would delete directory" in out

    def test_oserror_warns(self, tmp_path, monkeypatch, capsys):
        d = tmp_path / "d"
        d.mkdir()

        def fake_rmdir(path):
            raise OSError(13, "Permission denied")

        monkeypatch.setattr(os, "rmdir", fake_rmdir)
        delete_dirs([str(d)])
        err = capsys.readouterr().err
        assert "warning" in err

    def test_empty_list_no_output(self, capsys):
        delete_dirs([])
        assert capsys.readouterr().out == ""


# ===========================================================================
# _warn
# ===========================================================================

class TestWarn:
    def test_prints_to_stderr(self, capsys):
        _warn("something bad")
        err = capsys.readouterr().err
        assert "clean: warning: something bad" in err

    def test_does_not_print_to_stdout(self, capsys):
        _warn("oops")
        assert capsys.readouterr().out == ""


# ===========================================================================
# _confirm
# ===========================================================================

class TestConfirm:
    def test_y_returns_true(self, monkeypatch):
        monkeypatch.setattr("builtins.input", lambda _: "y")
        assert _confirm("Continue?") is True

    def test_yes_returns_true(self, monkeypatch):
        monkeypatch.setattr("builtins.input", lambda _: "yes")
        assert _confirm("Continue?") is True

    def test_n_returns_false(self, monkeypatch):
        monkeypatch.setattr("builtins.input", lambda _: "n")
        assert _confirm("Continue?") is False

    def test_empty_returns_false(self, monkeypatch):
        monkeypatch.setattr("builtins.input", lambda _: "")
        assert _confirm("Continue?") is False

    def test_eoferror_returns_false(self, monkeypatch, capsys):
        def _raise_eof(_):
            raise EOFError()

        monkeypatch.setattr("builtins.input", _raise_eof)
        assert _confirm("Continue?") is False

    def test_keyboardinterrupt_returns_false(self, monkeypatch, capsys):
        def _raise_kb(_):
            raise KeyboardInterrupt()

        monkeypatch.setattr("builtins.input", _raise_kb)
        assert _confirm("Continue?") is False


# ===========================================================================
# _print_list
# ===========================================================================

class TestPrintList:
    def test_prints_title(self, capsys):
        _print_list("My Title", [])
        out = capsys.readouterr().out
        assert "My Title" in out

    def test_prints_none_for_empty(self, capsys):
        _print_list("Title", [])
        out = capsys.readouterr().out
        assert "(none)" in out

    def test_prints_each_path(self, capsys):
        _print_list("Title", ["/a/b", "/c/d"])
        out = capsys.readouterr().out
        assert "/a/b" in out
        assert "/c/d" in out


# ===========================================================================
# main() integration
# ===========================================================================

class TestMain:
    def _run(self, monkeypatch, argv, capsys, input_fn=None):
        monkeypatch.setattr(sys, "argv", ["clean"] + argv)
        if input_fn:
            monkeypatch.setattr("builtins.input", input_fn)
        exit_code = 0
        try:
            task2.main()
        except SystemExit as exc:
            exit_code = exc.code
        out, err = capsys.readouterr()
        return exit_code, out, err

    # --- invalid directory ---

    def test_invalid_directory_exits_1(self, monkeypatch, capsys):
        code, _, err = self._run(monkeypatch, ["/nonexistent_xyz_99"], capsys)
        assert code == 1
        assert "no such directory" in err

    # --- list mode (no --delete) ---

    def test_list_mode_exits_0(self, tree, monkeypatch, capsys):
        code, _, _ = self._run(monkeypatch, [str(tree)], capsys)
        assert code == 0

    def test_list_mode_shows_empty_file(self, tree, monkeypatch, capsys):
        _, out, _ = self._run(monkeypatch, [str(tree)], capsys)
        assert "empty_file.txt" in out

    def test_list_mode_shows_empty_dir(self, tree, monkeypatch, capsys):
        _, out, _ = self._run(monkeypatch, [str(tree)], capsys)
        assert "empty_dir" in out

    def test_list_files_only(self, tree, monkeypatch, capsys):
        _, out, _ = self._run(monkeypatch, [str(tree), "--files"], capsys)
        assert "empty_file.txt" in out
        assert "Empty directories" not in out

    def test_list_dirs_only(self, tree, monkeypatch, capsys):
        _, out, _ = self._run(monkeypatch, [str(tree), "--dirs"], capsys)
        assert "empty_dir" in out
        assert "Empty files" not in out

    def test_nothing_to_do_when_all_nonempty(
        self, tmp_path, monkeypatch, capsys
    ):
        (tmp_path / "full.txt").write_text("data")
        _, out, _ = self._run(monkeypatch, [str(tmp_path)], capsys)
        assert "Nothing to do" in out

    # --- default directory (cwd) ---

    def test_default_directory_is_cwd(self, tmp_path, monkeypatch, capsys):
        (tmp_path / "e.txt").write_bytes(b"")
        monkeypatch.chdir(tmp_path)
        _, out, _ = self._run(monkeypatch, [], capsys)
        assert "e.txt" in out

    # --- dry-run ---

    def test_dry_run_does_not_delete_file(self, tree, monkeypatch, capsys):
        empty_file = tree / "empty_file.txt"
        self._run(monkeypatch, [str(tree), "--dry-run", "--files"], capsys)
        assert empty_file.exists()

    def test_dry_run_shows_would_delete(self, tree, monkeypatch, capsys):
        _, out, _ = self._run(monkeypatch,
                              [str(tree), "--dry-run", "--files"],
                              capsys)
        assert "would delete" in out

    def test_dry_run_implies_delete_flag(self, tree, monkeypatch, capsys):
        # --dry-run without --delete should still print deletion preview
        _, out, _ = self._run(monkeypatch, [str(tree), "--dry-run"], capsys)
        assert "would delete" in out

    # --- --delete with --yes ---

    def test_delete_yes_removes_empty_file(self, tree, monkeypatch, capsys):
        empty_file = tree / "empty_file.txt"
        self._run(monkeypatch,
                  [str(tree), "--delete", "--yes", "--files"],
                  capsys)
        assert not empty_file.exists()

    def test_delete_yes_removes_empty_dir(self, tree, monkeypatch, capsys):
        empty_dir = tree / "empty_dir"
        self._run(
            monkeypatch, [str(tree), "--delete", "--yes", "--dirs"], capsys
        )
        assert not empty_dir.exists()

    def test_delete_yes_prints_done(self, tree, monkeypatch, capsys):
        _, out, _ = self._run(
            monkeypatch, [str(tree), "--delete", "--yes"], capsys
        )
        assert "Done" in out

    def test_delete_files_only_leaves_empty_dir(
            self, tree, monkeypatch, capsys):
        empty_dir = tree / "empty_dir"
        self._run(
            monkeypatch, [str(tree), "--delete", "--yes", "--files"], capsys
        )
        assert empty_dir.exists()

    def test_delete_dirs_only_leaves_empty_file(
            self, tree, monkeypatch, capsys):
        empty_file = tree / "empty_file.txt"
        self._run(
            monkeypatch, [str(tree), "--delete", "--yes", "--dirs"], capsys
        )
        assert empty_file.exists()

    # --- --delete with confirmation prompt ---

    def test_delete_confirm_yes_deletes(self, tree, monkeypatch, capsys):
        empty_file = tree / "empty_file.txt"
        self._run(
            monkeypatch,
            [str(tree), "--delete", "--files"],
            capsys,
            input_fn=lambda _: "y",
        )
        assert not empty_file.exists()

    def test_delete_confirm_no_aborts(self, tree, monkeypatch, capsys):
        empty_file = tree / "empty_file.txt"
        self._run(
            monkeypatch,
            [str(tree), "--delete", "--files"],
            capsys,
            input_fn=lambda _: "n",
        )
        assert empty_file.exists()

    def test_delete_confirm_no_prints_aborted(self, tree, monkeypatch, capsys):
        _, out, _ = self._run(
            monkeypatch,
            [str(tree), "--delete", "--files"],
            capsys,
            input_fn=lambda _: "n",
        )
        assert "Aborted" in out

    def test_nothing_found_skips_delete_prompt(
            self, tmp_path, monkeypatch, capsys):
        (tmp_path / "full.txt").write_text("x")
        code, out, _ = self._run(
            monkeypatch, [str(tmp_path), "--delete", "--yes"], capsys
        )
        assert "Nothing to do" in out
        assert code == 0

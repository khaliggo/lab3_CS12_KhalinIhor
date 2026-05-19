#!/usr/bin/env python3
"""Pytest suite for task1.py (dir utility)."""
import os
import stat
import sys
import pytest
from task1 import (
    get_file_type_char,
    get_permissions_string,
    format_long,
    list_directory,
)

# Ensure task1 is importable from the same directory
sys.path.insert(0, os.path.dirname(__file__))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_dir(tmp_path):
    """Return a temporary directory pre-populated with known entries."""
    (tmp_path / "alpha.txt").write_text("hello")
    (tmp_path / "beta.py").write_text("world")
    (tmp_path / ".hidden").write_text("secret")
    sub = tmp_path / "subdir"
    sub.mkdir()
    return tmp_path


# ---------------------------------------------------------------------------
# get_file_type_char
# ---------------------------------------------------------------------------

class TestGetFileTypeChar:
    def test_regular_file(self, tmp_path):
        f = tmp_path / "reg.txt"
        f.write_text("x")
        mode = os.lstat(f).st_mode
        assert get_file_type_char(mode) == '-'

    def test_directory(self, tmp_path):
        mode = os.lstat(tmp_path).st_mode
        assert get_file_type_char(mode) == 'd'

    def test_symlink(self, tmp_path):
        target = tmp_path / "target.txt"
        target.write_text("t")
        link = tmp_path / "link"
        link.symlink_to(target)
        mode = os.lstat(link).st_mode
        assert get_file_type_char(mode) == 'l'

    def test_fifo(self, tmp_path):
        fifo = tmp_path / "myfifo"
        os.mkfifo(fifo)
        mode = os.lstat(fifo).st_mode
        assert get_file_type_char(mode) == 'p'

    def test_returns_string(self, tmp_path):
        f = tmp_path / "f"
        f.write_text("")
        result = get_file_type_char(os.lstat(f).st_mode)
        assert isinstance(result, str)
        assert len(result) == 1


# ---------------------------------------------------------------------------
# get_permissions_string
# ---------------------------------------------------------------------------

class TestGetPermissionsString:
    def test_length_is_nine(self, tmp_path):
        f = tmp_path / "f.txt"
        f.write_text("")
        result = get_permissions_string(os.lstat(f).st_mode)
        assert len(result) == 9

    def test_only_valid_chars(self, tmp_path):
        f = tmp_path / "f.txt"
        f.write_text("")
        result = get_permissions_string(os.lstat(f).st_mode)
        assert all(c in 'rwx-' for c in result)

    def test_all_permissions_set(self):
        # mode with all bits set: rwxrwxrwx
        mode = stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO
        assert get_permissions_string(mode) == 'rwxrwxrwx'

    def test_no_permissions(self):
        # mode with no permission bits
        assert get_permissions_string(0) == '---------'

    def test_owner_only_read(self):
        mode = stat.S_IRUSR
        result = get_permissions_string(mode)
        assert result[0] == 'r'
        assert result[1] == '-'
        assert result[2] == '-'
        assert result[3:] == '------'

    def test_owner_read_write_exec(self):
        mode = stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR
        result = get_permissions_string(mode)
        assert result[:3] == 'rwx'
        assert result[3:] == '------'

    def test_group_permissions(self):
        mode = stat.S_IRGRP | stat.S_IWGRP
        result = get_permissions_string(mode)
        assert result[:3] == '---'
        assert result[3] == 'r'
        assert result[4] == 'w'
        assert result[5] == '-'
        assert result[6:] == '---'

    def test_other_permissions(self):
        mode = stat.S_IROTH | stat.S_IXOTH
        result = get_permissions_string(mode)
        assert result[:6] == '------'
        assert result[6] == 'r'
        assert result[7] == '-'
        assert result[8] == 'x'

    def test_returns_string(self):
        assert isinstance(get_permissions_string(0o644), str)


# ---------------------------------------------------------------------------
# format_long
# ---------------------------------------------------------------------------

class TestFormatLong:
    def test_returns_string(self, tmp_dir):
        result = format_long("alpha.txt", str(tmp_dir))
        assert isinstance(result, str)

    def test_contains_filename(self, tmp_dir):
        result = format_long("alpha.txt", str(tmp_dir))
        assert "alpha.txt" in result

    def test_regular_file_type_char(self, tmp_dir):
        result = format_long("alpha.txt", str(tmp_dir))
        assert result[0] == '-'

    def test_directory_type_char(self, tmp_dir):
        result = format_long("subdir", str(tmp_dir))
        assert result[0] == 'd'

    def test_symlink_type_char(self, tmp_dir):
        target = tmp_dir / "alpha.txt"
        link = tmp_dir / "mylink"
        link.symlink_to(target)
        result = format_long("mylink", str(tmp_dir))
        assert result[0] == 'l'

    def test_contains_permissions(self, tmp_dir):
        result = format_long("alpha.txt", str(tmp_dir))
        # permissions are 9 chars after the type char
        assert len(result) > 10
        perm_part = result[1:10]
        assert all(c in 'rwx-' for c in perm_part)

    def test_contains_size(self, tmp_dir):
        content = "hello"
        (tmp_dir / "sized.txt").write_text(content)
        result = format_long("sized.txt", str(tmp_dir))
        size = str(os.lstat(tmp_dir / "sized.txt").st_size)
        assert size in result

    def test_contains_date(self, tmp_dir):
        result = format_long("alpha.txt", str(tmp_dir))
        import re
        assert re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}', result)

    def test_hidden_file(self, tmp_dir):
        result = format_long(".hidden", str(tmp_dir))
        assert ".hidden" in result

    def test_unknown_uid_falls_back_to_numeric(self, tmp_dir, monkeypatch):
        def raise_key(uid):
            raise KeyError(uid)

        monkeypatch.setattr("task1.pwd.getpwuid", raise_key)
        result = format_long("alpha.txt", str(tmp_dir))
        uid_str = str(os.lstat(tmp_dir / "alpha.txt").st_uid)
        assert uid_str in result

    def test_unknown_gid_falls_back_to_numeric(self, tmp_dir, monkeypatch):

        def raise_key(gid):
            raise KeyError(gid)

        monkeypatch.setattr("task1.grp.getgrgid", raise_key)
        result = format_long("alpha.txt", str(tmp_dir))
        gid_str = str(os.lstat(tmp_dir / "alpha.txt").st_gid)
        assert gid_str in result


# ---------------------------------------------------------------------------
# list_directory
# ---------------------------------------------------------------------------

class TestListDirectory:
    # --- basic listing (short format) ---

    def test_lists_visible_files(self, tmp_dir, capsys):
        list_directory(str(tmp_dir))
        out = capsys.readouterr().out
        assert "alpha.txt" in out
        assert "beta.py" in out
        assert "subdir" in out

    def test_hides_dotfiles_by_default(self, tmp_dir, capsys):
        list_directory(str(tmp_dir))
        out = capsys.readouterr().out
        assert ".hidden" not in out

    def test_show_all_reveals_dotfiles(self, tmp_dir, capsys):
        list_directory(str(tmp_dir), show_all=True)
        out = capsys.readouterr().out
        assert ".hidden" in out

    def test_entries_sorted(self, tmp_dir, capsys):
        list_directory(str(tmp_dir))
        out = capsys.readouterr().out.strip()
        names = [n.strip() for n in out.split('  ') if n.strip()]
        assert names == sorted(names)

    def test_short_format_single_line(self, tmp_dir, capsys):
        list_directory(str(tmp_dir))
        out = capsys.readouterr().out
        lines = [line for line in out.splitlines() if line]
        assert len(lines) == 1

    def test_separator_is_two_spaces(self, tmp_dir, capsys):
        list_directory(str(tmp_dir))
        out = capsys.readouterr().out.strip()
        assert '  ' in out   # entries separated by two spaces

    # --- long format ---

    def test_long_format_multiple_lines(self, tmp_dir, capsys):
        list_directory(str(tmp_dir), long=True)
        out = capsys.readouterr().out
        lines = [line for line in out.splitlines() if line]
        # alpha.txt, beta.py, subdir → at least 3 lines
        assert len(lines) >= 3

    def test_long_format_contains_filenames(self, tmp_dir, capsys):
        list_directory(str(tmp_dir), long=True)
        out = capsys.readouterr().out
        assert "alpha.txt" in out
        assert "beta.py" in out
        assert "subdir" in out

    def test_long_format_type_chars(self, tmp_dir, capsys):
        list_directory(str(tmp_dir), long=True)
        out = capsys.readouterr().out
        for line in out.splitlines():
            if line:
                assert line[0] in '-dlpscb'

    def test_long_format_hidden_excluded_by_default(self, tmp_dir, capsys):
        list_directory(str(tmp_dir), long=True)
        out = capsys.readouterr().out
        assert ".hidden" not in out

    def test_long_format_show_all(self, tmp_dir, capsys):
        list_directory(str(tmp_dir), long=True, show_all=True)
        out = capsys.readouterr().out
        assert ".hidden" in out

    # --- error handling ---

    def test_nonexistent_directory(self, capsys):
        list_directory("/nonexistent_path_xyz_12345")
        err = capsys.readouterr().out
        assert "No such file or directory" in err

    def test_not_a_directory(self, tmp_dir, capsys):
        f = str(tmp_dir / "alpha.txt")
        list_directory(f)
        err = capsys.readouterr().out
        assert "Not a directory" in err

    def test_empty_directory_no_output(self, tmp_path, capsys):
        list_directory(str(tmp_path))
        out = capsys.readouterr().out
        assert out == ""

    def test_empty_directory_all_dotfiles_hidden(self, tmp_path, capsys):
        (tmp_path / ".only_hidden").write_text("x")
        list_directory(str(tmp_path))
        out = capsys.readouterr().out
        # no visible files → no output
        assert out == ""

    def test_empty_directory_with_show_all(self, tmp_path, capsys):
        (tmp_path / ".only_hidden").write_text("x")
        list_directory(str(tmp_path), show_all=True)
        out = capsys.readouterr().out
        assert ".only_hidden" in out

    def test_no_output_for_empty_visible(self, tmp_path, capsys):
        (tmp_path / ".a").write_text("")
        (tmp_path / ".b").write_text("")
        list_directory(str(tmp_path), show_all=False)
        assert capsys.readouterr().out == ""


# ---------------------------------------------------------------------------
# Integration: run as a module (main) via subprocess
# ---------------------------------------------------------------------------

class TestMainIntegration:
    def test_main_default_lists_cwd(self, tmp_dir, monkeypatch, capsys):
        """main() with no args should list cwd."""
        import task1
        monkeypatch.chdir(tmp_dir)
        monkeypatch.setattr(sys, 'argv', ['dir'])
        task1.main()
        out = capsys.readouterr().out
        assert "alpha.txt" in out

    def test_main_with_path_arg(self, tmp_dir, monkeypatch, capsys):
        import task1
        monkeypatch.setattr(sys, 'argv', ['dir', str(tmp_dir)])
        task1.main()
        out = capsys.readouterr().out
        assert "alpha.txt" in out

    def test_main_long_flag(self, tmp_dir, monkeypatch, capsys):
        import task1
        monkeypatch.setattr(sys, 'argv', ['dir', '-l', str(tmp_dir)])
        task1.main()
        out = capsys.readouterr().out
        lines = [line for line in out.splitlines() if line]
        assert len(lines) >= 3

    def test_main_all_flag(self, tmp_dir, monkeypatch, capsys):
        import task1
        monkeypatch.setattr(sys, 'argv', ['dir', '-a', str(tmp_dir)])
        task1.main()
        out = capsys.readouterr().out
        assert ".hidden" in out

    def test_main_long_and_all_flags(self, tmp_dir, monkeypatch, capsys):
        import task1
        monkeypatch.setattr(sys, 'argv', ['dir', '-l', '-a', str(tmp_dir)])
        task1.main()
        out = capsys.readouterr().out
        assert ".hidden" in out
        lines = [line for line in out.splitlines() if line]
        assert len(lines) >= 4  # alpha, beta, subdir, .hidden

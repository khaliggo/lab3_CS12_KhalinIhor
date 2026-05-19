#!/usr/bin/env python3
"""dir — analog of the standard ls utility."""

import argparse
import os
import pwd
import grp
import stat
from datetime import datetime


def get_file_type_char(mode):
    """Return a single character representing the file type."""
    if stat.S_ISDIR(mode):
        return 'd'
    if stat.S_ISLNK(mode):
        return 'l'
    if stat.S_ISFIFO(mode):
        return 'p'
    if stat.S_ISSOCK(mode):
        return 's'
    if stat.S_ISBLK(mode):
        return 'b'
    if stat.S_ISCHR(mode):
        return 'c'
    return '-'


def get_permissions_string(mode):
    """Convert numeric mode to rwxrwxrwx string."""
    perms = ''
    for who in (stat.S_IRUSR, stat.S_IWUSR, stat.S_IXUSR,
                stat.S_IRGRP, stat.S_IWGRP, stat.S_IXGRP,
                stat.S_IROTH, stat.S_IWOTH, stat.S_IXOTH):
        perms += 'rwx'[
            (stat.S_IRUSR, stat.S_IWUSR, stat.S_IXUSR,
             stat.S_IRGRP, stat.S_IWGRP, stat.S_IXGRP,
             stat.S_IROTH, stat.S_IWOTH, stat.S_IXOTH).index(who) % 3
        ] if mode & who else '-'
    return perms


def format_long(entry, path):
    """Format a directory entry in long listing style."""
    full_path = os.path.join(path, entry)
    st = os.lstat(full_path)
    mode = st.st_mode

    type_char = get_file_type_char(mode)
    perms = get_permissions_string(mode)
    nlinks = st.st_nlink
    size = st.st_size
    mtime = datetime.fromtimestamp(st.st_mtime).strftime('%Y-%m-%d %H:%M')

    try:
        owner = pwd.getpwuid(st.st_uid).pw_name
    except KeyError:
        owner = str(st.st_uid)

    try:
        group = grp.getgrgid(st.st_gid).gr_name
    except KeyError:
        group = str(st.st_gid)

    return (
        f"{type_char}{perms}  {nlinks:>3}  {owner:<10} {group:<10}"
        f"  {size:>10}  {mtime}  {entry}"
    )


def list_directory(wd, long=False, show_all=False):
    """List directory contents according to the given options."""
    try:
        entries = os.listdir(wd)
    except PermissionError:
        print(f"dir: cannot open directory '{wd}': Permission denied")
        return
    except FileNotFoundError:
        print(f"dir: cannot access '{wd}': No such file or directory")
        return
    except NotADirectoryError:
        print(f"dir: '{wd}': Not a directory")
        return

    entries.sort()

    if not show_all:
        entries = [e for e in entries if not e.startswith('.')]

    if not entries:
        return

    if long:
        for entry in entries:
            print(format_long(entry, wd))
    else:
        print('  '.join(entries))


def main():
    parser = argparse.ArgumentParser(
        prog='dir',
        description='List directory contents (analog of ls).',
        add_help=False,
    )
    parser.add_argument(
        'wd',
        nargs='?',
        default='.',
        help='Working directory to list (default: current directory)',
    )
    parser.add_argument(
        '-h', '--help',
        action='help',
        default=argparse.SUPPRESS,
        help='Show this help message and exit',
    )
    parser.add_argument(
        '-l', '--long',
        action='store_true',
        help='Use long listing format',
    )
    parser.add_argument(
        '-a', '--all',
        action='store_true',
        dest='show_all',
        help='Show hidden entries (starting with .)',
    )

    args = parser.parse_args()
    list_directory(args.wd, long=args.long, show_all=args.show_all)


if __name__ == '__main__':
    main()

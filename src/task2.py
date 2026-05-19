#!/usr/bin/env python3
"""clean — find and optionally remove empty files and directories."""

import argparse
import os
import sys


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

def find_empty_files(root):
    """Recursively find all empty files under root."""
    empty = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for fname in filenames:
            fpath = os.path.join(dirpath, fname)
            try:
                if os.path.getsize(fpath) == 0:
                    empty.append(fpath)
            except OSError as exc:
                _warn(f"cannot stat '{fpath}': {exc.strerror}")
    return empty


def find_empty_dirs(root):
    """Recursively find all empty directories under root.

    Uses bottom-up walk and a set of confirmed-empty paths so that a
    directory whose only remaining children are themselves empty is also
    reported correctly.
    """
    empty = set()
    abs_root = os.path.abspath(root)

    for dirpath, dirnames, filenames in os.walk(root, topdown=False):
        if os.path.abspath(dirpath) == abs_root:
            continue
        if filenames:
            continue
        all_children_empty = all(
            os.path.abspath(os.path.join(dirpath, d)) in empty
            for d in dirnames
        )
        if not dirnames or all_children_empty:
            empty.add(os.path.abspath(dirpath))

    # Return sorted deepest-first so deletion order is safe
    return sorted(empty, key=len, reverse=True)


# ---------------------------------------------------------------------------
# Deletion
# ---------------------------------------------------------------------------

def delete_files(paths, dry_run=False):
    """Delete files; print an informational message for each."""
    for fpath in paths:
        if dry_run:
            print(f"  [dry-run] would delete file: {fpath}")
            continue
        try:
            os.remove(fpath)
            print(f"  Deleted file: {fpath}")
        except OSError as exc:
            _warn(f"cannot delete '{fpath}': {exc.strerror}")


def delete_dirs(paths, dry_run=False):
    """Delete directories; print an informational message for each."""
    for dpath in paths:
        if dry_run:
            print(f"  [dry-run] would delete directory: {dpath}")
            continue
        try:
            os.rmdir(dpath)
            print(f"  Deleted directory: {dpath}")
        except OSError as exc:
            _warn(f"cannot delete '{dpath}': {exc.strerror}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _warn(msg):
    print(f"clean: warning: {msg}", file=sys.stderr)


def _confirm(prompt):
    """Ask the user yes/no. Returns True if they confirm."""
    try:
        answer = input(f"{prompt} [y/N]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return False
    return answer in ('y', 'yes')


def _print_list(title, paths):
    print(f"\n{title}:")
    if paths:
        for p in paths:
            print(f"  {p}")
    else:
        print("  (none)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        prog='clean',
        description=(
            'Find and optionally remove empty files and directories.\n\n'
            'By default (no flags) the utility lists both empty files\n'
            'and empty directories found under the given directory.'
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            'Examples:\n'
            '  clean                        '
            '# list empty files & dirs in cwd\n'
            '  clean /some/path             '
            '# list empty files & dirs there\n'
            '  clean --files                '
            '# list empty files only\n'
            '  clean --dirs                 '
            '# list empty dirs only\n'
            '  clean --delete               '
            '# delete both (asks for confirmation)\n'
            '  clean --delete --files       '
            '# delete empty files only\n'
            '  clean --delete --dirs        '
            '# delete empty dirs only\n'
            '  clean --delete --yes         '
            '# delete without confirmation prompt\n'
            '  clean --delete --dry-run     '
            '# preview what would be deleted\n'
        ),
    )

    parser.add_argument(
        'directory',
        nargs='?',
        default='.',
        help='Root directory to scan (default: current directory)',
    )

    # --- scope flags --------------------------------------------------------
    scope = parser.add_argument_group(
        'scope (default: both files and dirs)'
    )
    scope.add_argument(
        '--files',
        action='store_true',
        help='Operate on empty files only',
    )
    scope.add_argument(
        '--dirs',
        action='store_true',
        help='Operate on empty directories only',
    )

    # --- action flags -------------------------------------------------------
    action = parser.add_argument_group('action (default: list only)')
    action.add_argument(
        '--delete',
        action='store_true',
        help='Delete the found empty files/directories',
    )
    action.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be deleted without actually deleting',
    )
    action.add_argument(
        '-y', '--yes',
        action='store_true',
        help='Skip confirmation prompt when deleting',
    )

    args = parser.parse_args()

    # Validate directory
    root = os.path.abspath(args.directory)
    if not os.path.isdir(root):
        print(f"clean: '{root}': no such directory", file=sys.stderr)
        sys.exit(1)

    # Resolve scope: if neither --files nor --dirs given, do both
    do_files = args.files or not args.dirs
    do_dirs = args.dirs or not args.files

    # --dry-run implies --delete (for display purposes)
    if args.dry_run and not args.delete:
        args.delete = True

    # -------------------------------------------------------------------------
    # Discover
    # -------------------------------------------------------------------------
    empty_files = find_empty_files(root) if do_files else []
    empty_dirs = find_empty_dirs(root) if do_dirs else []

    # -------------------------------------------------------------------------
    # Report
    # -------------------------------------------------------------------------
    if do_files:
        _print_list(f"Empty files in '{root}'", empty_files)
    if do_dirs:
        _print_list(f"Empty directories in '{root}'", empty_dirs)

    nothing_found = not empty_files and not empty_dirs
    if nothing_found:
        print("\nNothing to do.")
        sys.exit(0)

    if not args.delete:
        sys.exit(0)

    # -------------------------------------------------------------------------
    # Confirm deletion (unless --yes or --dry-run)
    # -------------------------------------------------------------------------
    print()
    if args.dry_run:
        print("Dry-run mode — no files will actually be deleted.\n")
    elif not args.yes:
        what = []
        if do_files and empty_files:
            what.append(f"{len(empty_files)} file(s)")
        if do_dirs and empty_dirs:
            what.append(f"{len(empty_dirs)} director(y/ies)")
        prompt = (
            f"About to permanently delete"
            f" {' and '.join(what)}. Continue?"
        )
        if not _confirm(prompt):
            print("Aborted.")
            sys.exit(0)
        print()

    # -------------------------------------------------------------------------
    # Delete
    # -------------------------------------------------------------------------
    if do_files and empty_files:
        print("Deleting empty files:")
        delete_files(empty_files, dry_run=args.dry_run)

    if do_dirs and empty_dirs:
        print("\nDeleting empty directories:")
        delete_dirs(empty_dirs, dry_run=args.dry_run)

    print("\nDone.")


if __name__ == '__main__':
    main()

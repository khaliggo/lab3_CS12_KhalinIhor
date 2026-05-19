# Operating Systems Lab 3 - File And Directory Utilities

## About Project

This project was created for Operating Systems Laboratory Work #3, "Basics of
Working with Files and Directories". The laboratory work focuses on practical
interaction with the Linux filesystem using Python.

The main topic of the lab is file and directory management in a Unix-like
environment. The assignment describes core filesystem concepts and operations:

- files and directories;
- paths and working directories;
- file descriptors;
- reading and writing;
- creating links;
- copying, moving, and deleting filesystem objects;
- changing owners and permissions;
- reading object metadata;
- determining file type, permissions, size, owner, group, and modification time.

The purpose of the lab is to gain practical skills in programmatic work with
files and directories in Linux and to better understand how the Linux filesystem
represents objects and their attributes.

The laboratory assignment contains two main tasks.

Task 1 asks to create a Python utility named `dir`. It is an analog of the
standard Linux `ls` command. The utility accepts one optional positional
argument:

```text
wd
```

`wd` means working directory. It is the directory whose contents should be
analyzed and printed. If the user does not provide this argument, the utility
uses the current directory.

The `dir` utility supports three options without parameters:

- `-h`, `--help`: print help information about how to use the utility;
- `-l`, `--long`: print additional information about every filesystem object,
  similar to `ls -l`;
- `-a`, `--all`: include hidden entries whose names start with a dot.

According to the assignment, hidden entries are not printed by default. The
simplified implementation also does not print `.` and `..`. This matches the
project behavior because Python `os.listdir()` returns real directory entries
but does not include the special `.` and `..` names.

Task 2 asks to create a Python utility named `clean`. This utility searches for
empty files and empty directories and can optionally delete them. The default
behavior is safe: when the user runs the utility without delete options, it only
prints lists of empty files and empty directories under the current working
directory.

The assignment warns that programmatic deletion is dangerous because it can
cause irreversible data loss. For that reason, this project includes several
safety mechanisms:

- listing mode is the default;
- deletion requires `--delete`;
- deletion asks for confirmation unless `--yes` is passed;
- `--dry-run` previews deletion without removing anything;
- delete functions print informational messages for every removed item;
- filesystem errors are printed as warnings instead of crashing the whole scan.

The project also includes automated tests with `pytest`. In the lab PDF,
pytest testing is described as optional extra work for this laboratory, while
manual testing is enough. This repository includes a large pytest suite anyway,
which gives stronger confidence that both utilities behave correctly.

The mandatory project requirements from the lab are also reflected here:

- the project is organized as a separate Git repository;
- source code is stored separately from tests;
- a README file explains the goal and behavior of the project;
- the code is intended to pass `flake8` with zero errors;
- tests can be run with `pytest`.

## About Code

The project contains two source files and two test files:

```text
lab3_CS12_KhalinIhor/
|-- README.md
|-- src/
|   |-- task1.py
|   `-- task2.py
`-- tests/
    |-- test_task1.py
    `-- test_task2.py
```

Runtime code uses only the Python standard library. No external package is
needed to run the utilities themselves.

Main standard library modules used in `src/task1.py`:

- `argparse`: parses command-line options for the `dir` utility;
- `os`: lists directories, joins paths, and reads filesystem entries;
- `pwd`: resolves numeric user IDs into user names;
- `grp`: resolves numeric group IDs into group names;
- `stat`: detects file type and permission bits;
- `datetime`: formats modification time for long listing output.

Main standard library modules used in `src/task2.py`:

- `argparse`: parses command-line options for the `clean` utility;
- `os`: walks directories, checks file sizes, removes files, and removes
  directories;
- `sys`: writes warnings to stderr and exits with explicit status codes.

The tests use:

- `pytest`;
- `tmp_path` for temporary filesystem trees;
- `monkeypatch` for replacing functions, changing `sys.argv`, and simulating
  user input;
- `capsys` for capturing stdout and stderr.

### Source File: `src/task1.py`

`src/task1.py` implements the `dir` utility, a simplified analog of `ls`.

The file contains these main functions:

```python
get_file_type_char(mode)
get_permissions_string(mode)
format_long(entry, path)
list_directory(wd, long=False, show_all=False)
main()
```

`get_file_type_char(mode)` receives a numeric mode value from `os.lstat()` and
returns a one-character file type marker. The marker is the first character used
in long listing output.

Supported markers:

```text
d  directory
l  symbolic link
p  FIFO / named pipe
s  socket
b  block device
c  character device
-  regular file or unknown ordinary object
```

`get_permissions_string(mode)` converts permission bits into a classic
nine-character permission string:

```text
rwxrwxrwx
```

The first three characters describe owner permissions, the next three describe
group permissions, and the final three describe permissions for others.

Examples:

```text
rwx------  owner can read, write, and execute
rw-r--r--  owner can read/write, group and others can read
---------  no read/write/execute permission bits are set
```

`format_long(entry, path)` builds one long-format output line for one directory
entry. It combines:

- file type character;
- permission string;
- number of hard links;
- owner name;
- group name;
- size in bytes;
- last modification time;
- entry name.

The function uses `os.lstat()` instead of `os.stat()`. This is important because
`os.lstat()` reads metadata about a symbolic link itself instead of following
the link to its target. Because of that, symbolic links can correctly receive
the `l` file type marker.

`list_directory(wd, long=False, show_all=False)` is the main directory listing
function. It reads directory entries, sorts them alphabetically, optionally
filters hidden files, and prints either short-format or long-format output.

Short-format output prints all visible entries on one line separated by two
spaces:

```text
alpha.txt  beta.py  subdir
```

Long-format output prints one entry per line:

```text
-rw-r--r--    1  ihor       ihor                5  2026-05-19 12:30  alpha.txt
drwxr-xr-x    2  ihor       ihor             4096  2026-05-19 12:30  subdir
```

Exact owners, groups, permissions, sizes, and timestamps depend on the local
machine and filesystem.

`main()` creates the command-line interface for the utility. It defines the
optional positional argument `wd`, the help flag, the long-listing flag, and the
hidden-file flag. After parsing arguments, it calls `list_directory()`.

Supported `dir` usage examples:

```bash
python3 src/task1.py
python3 src/task1.py /tmp
python3 src/task1.py -l
python3 src/task1.py -a
python3 src/task1.py -l -a /tmp
python3 src/task1.py --long --all /home/ihor
python3 src/task1.py --help
```

### Source File: `src/task2.py`

`src/task2.py` implements the `clean` utility. It can scan a directory tree,
find empty files, find empty directories, print the results, and optionally
delete the found objects.

The file contains these main functions:

```python
find_empty_files(root)
find_empty_dirs(root)
delete_files(paths, dry_run=False)
delete_dirs(paths, dry_run=False)
_warn(msg)
_confirm(prompt)
_print_list(title, paths)
main()
```

`find_empty_files(root)` recursively searches for empty files below `root`. It
uses `os.walk(root)` to visit every directory and subdirectory. For every file,
it calls `os.path.getsize(path)`. If the size is `0`, the file is added to the
result list.

`find_empty_dirs(root)` recursively searches for empty directories below `root`.
It uses `os.walk(root, topdown=False)`, which means it processes child
directories before their parents. This bottom-up order is important because a
directory whose children are all empty directories can also be considered empty
for cleanup purposes.

The function excludes the root directory itself from the result. This prevents
the utility from suggesting deletion of the scan root.

The function returns directories sorted deepest-first. This is important for
safe deletion: nested empty directories must be removed before their parent
directories.

`delete_files(paths, dry_run=False)` removes files with `os.remove()`. For every
file, it prints an informational message. If `dry_run=True`, it does not delete
the file and prints what would happen instead.

`delete_dirs(paths, dry_run=False)` removes directories with `os.rmdir()`. It
also supports dry-run mode. `os.rmdir()` removes only empty directories, so it
is safer than recursive deletion functions such as `shutil.rmtree()`.

`_warn(msg)` prints warning messages to stderr. The code uses it when file
metadata cannot be read or deletion fails.

`_confirm(prompt)` asks the user a yes/no question. It returns `True` only for
`y` and `yes`. Empty input, `n`, `no`, end-of-file, and keyboard interruption are
treated as cancellation.

`_print_list(title, paths)` prints a section title and either every path in the
list or `(none)` when the list is empty.

`main()` creates the command-line interface and connects all parts of the
utility. It validates the input directory, decides whether to work with files,
directories, or both, performs discovery, prints results, asks for confirmation
when needed, and performs deletion or dry-run preview.

Supported `clean` usage examples:

```bash
python3 src/task2.py
python3 src/task2.py /tmp/project
python3 src/task2.py --files
python3 src/task2.py --dirs
python3 src/task2.py --delete
python3 src/task2.py --delete --files
python3 src/task2.py --delete --dirs
python3 src/task2.py --delete --yes
python3 src/task2.py --dry-run
python3 src/task2.py /tmp/project --dry-run --files
```

### Test Files

`tests/test_task1.py` checks the `dir` utility.

The Task 1 tests cover:

- file type detection for regular files, directories, symbolic links, and FIFOs;
- permission string length and allowed characters;
- permission conversion for owner, group, and others;
- long-format output generation;
- owner and group fallback to numeric IDs;
- short listing output;
- hidden file filtering;
- `--all` behavior;
- alphabetical sorting;
- long listing mode;
- error messages for nonexistent paths;
- error messages for paths that are not directories;
- empty directory behavior;
- integration behavior through `main()` and simulated `sys.argv`.

`tests/test_task2.py` checks the `clean` utility.

The Task 2 tests cover:

- finding empty files;
- ignoring non-empty files;
- recursive file discovery;
- warnings when file metadata cannot be read;
- finding empty directories;
- excluding the root directory from empty directory results;
- nested empty directory detection;
- deepest-first directory ordering;
- file deletion;
- directory deletion;
- dry-run behavior;
- warning output on deletion errors;
- confirmation handling;
- formatted list output;
- invalid directory handling;
- default list mode;
- files-only mode;
- directories-only mode;
- default current-directory behavior;
- deletion with `--yes`;
- deletion with confirmation;
- aborted deletion.

To run all tests:

```bash
PYTHONPATH=src pytest
```

To run style checking, if `flake8` is installed:

```bash
flake8 src tests
```

## How Code Works Detailed

### Task 1 Detailed Flow: `dir` Utility

The `dir` utility starts from the command-line interface in `main()`.

The parser is created like this:

```python
parser = argparse.ArgumentParser(
    prog='dir',
    description='List directory contents (analog of ls).',
    add_help=False,
)
```

The program name is set to `dir`, so help output looks like help for a real
utility with that name. `add_help=False` disables the default help option so the
code can explicitly define `-h` and `--help` as required by the laboratory
assignment.

The optional positional argument is defined as:

```python
parser.add_argument(
    'wd',
    nargs='?',
    default='.',
    help='Working directory to list (default: current directory)',
)
```

`nargs='?'` means the argument is optional. If it is missing, the value becomes
`.`. In Linux paths, `.` means the current working directory.

The help option is defined as:

```python
parser.add_argument(
    '-h', '--help',
    action='help',
    default=argparse.SUPPRESS,
    help='Show this help message and exit',
)
```

`action='help'` tells `argparse` to print usage information and exit.

The long output option is defined as:

```python
parser.add_argument(
    '-l', '--long',
    action='store_true',
    help='Use long listing format',
)
```

When the user passes `-l` or `--long`, `args.long` becomes `True`. Without this
option, it is `False`.

The hidden file option is defined as:

```python
parser.add_argument(
    '-a', '--all',
    action='store_true',
    dest='show_all',
    help='Show hidden entries (starting with .)',
)
```

The destination is named `show_all`, so the parsed value is stored in
`args.show_all`.

After parsing, `main()` calls:

```python
list_directory(args.wd, long=args.long, show_all=args.show_all)
```

This transfers all user choices to the main listing function.

Inside `list_directory()`, the first step is reading the directory:

```python
entries = os.listdir(wd)
```

`os.listdir()` returns a list of names inside the directory. It returns only
names, not full paths. The code later joins each name with the directory path
when it needs metadata.

The call is wrapped in exception handling:

```python
except PermissionError:
    print(f"dir: cannot open directory '{wd}': Permission denied")
except FileNotFoundError:
    print(f"dir: cannot access '{wd}': No such file or directory")
except NotADirectoryError:
    print(f"dir: '{wd}': Not a directory")
```

These errors make the utility friendlier. Instead of showing a Python traceback,
the program prints a message similar to command-line tools.

After reading entries, the code sorts them:

```python
entries.sort()
```

Sorting makes output deterministic and easier to read. It also makes tests more
stable because the filesystem may not return names in alphabetical order.

Next, hidden files are filtered unless `show_all=True`:

```python
if not show_all:
    entries = [e for e in entries if not e.startswith('.')]
```

Any entry whose name starts with `.` is hidden by default. Passing `-a` or
`--all` disables this filter.

If the resulting list is empty, the function returns without printing:

```python
if not entries:
    return
```

This is why an empty directory produces no output.

If long mode is disabled, short output is printed:

```python
print('  '.join(entries))
```

All names are printed on one line, separated by two spaces.

If long mode is enabled, the function prints one formatted line per entry:

```python
for entry in entries:
    print(format_long(entry, wd))
```

`format_long()` starts by building the full path:

```python
full_path = os.path.join(path, entry)
```

Then it reads metadata:

```python
st = os.lstat(full_path)
mode = st.st_mode
```

The `st` object contains filesystem metadata:

- `st.st_mode`: file type and permissions;
- `st.st_nlink`: number of hard links;
- `st.st_uid`: owner user ID;
- `st.st_gid`: group ID;
- `st.st_size`: size in bytes;
- `st.st_mtime`: last modification timestamp.

The file type character is calculated by `get_file_type_char(mode)`.

That function checks the mode using helpers from `stat`:

```python
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
```

The order matters because every check asks whether the mode belongs to a
particular filesystem object type. If none of the special types match, the code
uses `-`, which is the usual marker for a regular file.

The permission string is calculated by `get_permissions_string(mode)`.

The function checks these permission bits:

```python
stat.S_IRUSR  owner read
stat.S_IWUSR  owner write
stat.S_IXUSR  owner execute
stat.S_IRGRP  group read
stat.S_IWGRP  group write
stat.S_IXGRP  group execute
stat.S_IROTH  others read
stat.S_IWOTH  others write
stat.S_IXOTH  others execute
```

For every bit, it adds `r`, `w`, or `x` if the bit is present. If the bit is not
present, it adds `-`. The result is exactly nine characters.

Owner and group names are resolved with:

```python
owner = pwd.getpwuid(st.st_uid).pw_name
group = grp.getgrgid(st.st_gid).gr_name
```

If the numeric user ID or group ID is unknown on the system, the code falls back
to the numeric value:

```python
owner = str(st.st_uid)
group = str(st.st_gid)
```

This prevents the utility from failing when metadata refers to a user or group
that is not present in the local account database.

Modification time is formatted with:

```python
datetime.fromtimestamp(st.st_mtime).strftime('%Y-%m-%d %H:%M')
```

This converts the Unix timestamp into a readable date and time.

Finally, `format_long()` returns one formatted string:

```python
return (
    f"{type_char}{perms}  {nlinks:>3}  {owner:<10} {group:<10}"
    f"  {size:>10}  {mtime}  {entry}"
)
```

This line is designed to be human-readable. It aligns the number of links,
owner, group, and size fields so long output looks similar to `ls -l`.

Complete `dir` behavior table:

| Command | Meaning |
| --- | --- |
| `python3 src/task1.py` | list visible entries in current directory |
| `python3 src/task1.py /tmp` | list visible entries in `/tmp` |
| `python3 src/task1.py -a` | include hidden entries |
| `python3 src/task1.py -l` | print long information for visible entries |
| `python3 src/task1.py -l -a` | print long information including hidden entries |
| `python3 src/task1.py --help` | show help text |

### Task 2 Detailed Flow: `clean` Utility

The `clean` utility starts in `main()`, where `argparse` defines all supported
arguments.

The optional positional directory argument is:

```python
parser.add_argument(
    'directory',
    nargs='?',
    default='.',
    help='Root directory to scan (default: current directory)',
)
```

If no directory is given, the current working directory is scanned.

The scope options are:

```python
--files
--dirs
```

They decide what kind of empty objects the utility should work with.

The action options are:

```python
--delete
--dry-run
-y, --yes
```

`--delete` changes the program from list-only mode to deletion mode.
`--dry-run` previews deletion but does not remove anything.
`--yes` skips the confirmation prompt.

After parsing arguments, the program converts the input directory into an
absolute path:

```python
root = os.path.abspath(args.directory)
```

Then it validates that the path is a directory:

```python
if not os.path.isdir(root):
    print(f"clean: '{root}': no such directory", file=sys.stderr)
    sys.exit(1)
```

Invalid input exits with status code `1`.

Next, the code resolves the scope:

```python
do_files = args.files or not args.dirs
do_dirs = args.dirs or not args.files
```

This logic creates three useful modes:

| Options | `do_files` | `do_dirs` | Meaning |
| --- | --- | --- | --- |
| no `--files`, no `--dirs` | true | true | work with both |
| `--files` | true | false | work with files only |
| `--dirs` | false | true | work with directories only |
| `--files --dirs` | true | true | work with both |

Then the code treats dry-run as a deletion preview:

```python
if args.dry_run and not args.delete:
    args.delete = True
```

This means the user can write:

```bash
python3 src/task2.py --dry-run
```

instead of:

```bash
python3 src/task2.py --delete --dry-run
```

Discovery happens next:

```python
empty_files = find_empty_files(root) if do_files else []
empty_dirs = find_empty_dirs(root) if do_dirs else []
```

If the selected scope includes files, empty files are found. If it does not,
the file list stays empty. The same logic is used for directories.

`find_empty_files(root)` works recursively:

```python
for dirpath, _dirnames, filenames in os.walk(root):
    for fname in filenames:
        fpath = os.path.join(dirpath, fname)
        if os.path.getsize(fpath) == 0:
            empty.append(fpath)
```

`os.walk(root)` visits every directory below `root`. For each file, the code
checks its size. A size of zero bytes means the file is empty.

If the size cannot be read, the exception is caught:

```python
except OSError as exc:
    _warn(f"cannot stat '{fpath}': {exc.strerror}")
```

The scan continues even if one file causes an error.

`find_empty_dirs(root)` uses bottom-up walking:

```python
for dirpath, dirnames, filenames in os.walk(root, topdown=False):
```

Bottom-up walking means child directories are processed before parent
directories. This lets the function detect parent directories that contain only
empty child directories.

The root directory is skipped:

```python
if os.path.abspath(dirpath) == abs_root:
    continue
```

If a directory contains files, it is not empty:

```python
if filenames:
    continue
```

If a directory has no child directories, it is empty. If it has child
directories, the code checks whether all child directories are already known to
be empty:

```python
all_children_empty = all(
    os.path.abspath(os.path.join(dirpath, d)) in empty
    for d in dirnames
)
```

Then the directory is added to the empty set:

```python
if not dirnames or all_children_empty:
    empty.add(os.path.abspath(dirpath))
```

Finally, paths are returned in deepest-first order:

```python
return sorted(empty, key=len, reverse=True)
```

This is useful for deletion. If `a/b` and `a` are both empty, `a/b` should be
removed before `a`.

After discovery, `main()` prints the results:

```python
if do_files:
    _print_list(f"Empty files in '{root}'", empty_files)
if do_dirs:
    _print_list(f"Empty directories in '{root}'", empty_dirs)
```

`_print_list()` prints the section title and every path. If there are no paths,
it prints `(none)`.

Then the program checks whether anything was found:

```python
nothing_found = not empty_files and not empty_dirs
if nothing_found:
    print("\nNothing to do.")
    sys.exit(0)
```

If there are no empty files or directories in the selected scope, the program
exits successfully with status code `0`.

If the user did not request deletion, the program exits after listing:

```python
if not args.delete:
    sys.exit(0)
```

This is the safe default behavior.

If deletion was requested and dry-run mode is active, the program prints:

```text
Dry-run mode - no files will actually be deleted.
```

No files or directories are removed in this mode.

If deletion was requested without `--yes`, the program builds a confirmation
prompt. It counts how many files and directories are about to be removed and
asks:

```text
About to permanently delete ... Continue? [y/N]:
```

The confirmation helper accepts only `y` and `yes`:

```python
return answer in ('y', 'yes')
```

Anything else cancels the operation.

When deletion proceeds, files are deleted first:

```python
if do_files and empty_files:
    print("Deleting empty files:")
    delete_files(empty_files, dry_run=args.dry_run)
```

Then directories are deleted:

```python
if do_dirs and empty_dirs:
    print("\nDeleting empty directories:")
    delete_dirs(empty_dirs, dry_run=args.dry_run)
```

Deleting files before directories is useful because some directories may become
empty after empty files are removed. Directory deletion still uses the list
calculated during discovery, so the utility keeps behavior predictable.

`delete_files()` handles every path individually:

```python
os.remove(fpath)
print(f"  Deleted file: {fpath}")
```

If dry-run mode is enabled:

```python
print(f"  [dry-run] would delete file: {fpath}")
```

`delete_dirs()` is similar but uses:

```python
os.rmdir(dpath)
```

`os.rmdir()` only removes empty directories. This avoids recursive deletion and
helps protect non-empty directories from accidental removal.

Complete `clean` behavior table:

| Command | Meaning |
| --- | --- |
| `python3 src/task2.py` | list empty files and directories in current directory |
| `python3 src/task2.py /tmp/project` | list empty files and directories under `/tmp/project` |
| `python3 src/task2.py --files` | list empty files only |
| `python3 src/task2.py --dirs` | list empty directories only |
| `python3 src/task2.py --delete` | ask confirmation, then delete found empty files and directories |
| `python3 src/task2.py --delete --files` | ask confirmation, then delete empty files only |
| `python3 src/task2.py --delete --dirs` | ask confirmation, then delete empty directories only |
| `python3 src/task2.py --delete --yes` | delete without confirmation prompt |
| `python3 src/task2.py --dry-run` | show what would be deleted without deleting |

### How The Tests Work

The tests build temporary files and directories with `tmp_path`. This makes the
test suite safe because it does not need to touch real project files.

For Task 1, the tests create a temporary directory containing:

```text
alpha.txt
beta.py
.hidden
subdir/
```

Then they call functions such as `list_directory()` and `format_long()` and
capture output with `capsys`.

The tests also create special filesystem objects when needed. For example, a
FIFO is created with:

```python
os.mkfifo(fifo)
```

This verifies that `get_file_type_char()` can recognize a named pipe.

For integration-style checks, tests patch `sys.argv`:

```python
monkeypatch.setattr(sys, 'argv', ['dir', '-l', '-a', str(tmp_dir)])
task1.main()
```

This simulates running the utility from the command line without launching a
separate process.

For Task 2, the tests create directory trees with a known structure:

```text
tmp_path/
|-- empty_file.txt
|-- nonempty_file.txt
|-- empty_dir/
|-- nonempty_dir/
|   `-- child.txt
`-- nested/
    `-- inner_empty/
```

This structure allows the tests to check whether empty and non-empty objects are
classified correctly.

Tests for deletion use only temporary files and directories. They check both
actual deletion and dry-run behavior. Dry-run tests confirm that files and
directories still exist after the function call.

Confirmation tests replace `input()` with fake answers:

```python
monkeypatch.setattr("builtins.input", lambda _: "y")
monkeypatch.setattr("builtins.input", lambda _: "n")
```

This checks both confirmed deletion and aborted deletion.

Warning tests replace filesystem functions with fake functions that raise
`OSError`. This proves that the program reports errors through `_warn()` and
continues safely.

### Expected Usage Workflow

1. Use `dir` to inspect a directory:

```bash
python3 src/task1.py
python3 src/task1.py -l
python3 src/task1.py -a
python3 src/task1.py -l -a /some/path
```

2. Use `clean` first in listing mode:

```bash
python3 src/task2.py /some/path
```

3. Preview cleanup before deleting:

```bash
python3 src/task2.py /some/path --dry-run
```

4. Delete only after checking the preview:

```bash
python3 src/task2.py /some/path --delete
```

or, when confirmation is not needed:

```bash
python3 src/task2.py /some/path --delete --yes
```

5. Run tests:

```bash
PYTHONPATH=src pytest
```

6. Run linting:

```bash
flake8 src tests
```

### Summary Of Program Logic

Task 1 demonstrates reading directory contents and filesystem metadata. It
shows how Python can reproduce important parts of the `ls` command: short
listing, hidden-file filtering, long listing, file type detection, permissions,
owner, group, size, and modification time.

Task 2 demonstrates recursive filesystem scanning and controlled deletion. It
shows how to walk a directory tree, detect empty files by size, detect empty
directories bottom-up, report results, ask for user confirmation, perform a
dry-run, and delete selected filesystem objects safely.

Together, both utilities demonstrate the central idea of Laboratory Work #3:
Linux filesystem objects can be inspected and managed programmatically, but code
that reads and especially deletes filesystem data must be written carefully,
tested thoroughly, and used with attention.

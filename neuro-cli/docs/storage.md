# storage

Storage operations

## Usage

```bash
neuro storage [OPTIONS] COMMAND [ARGS]...
```

Storage operations.

## Commands

* [neuro storage cp](storage.md#cp): Copy files and directories
* [neuro storage ls](storage.md#ls): List directory contents
* [neuro storage glob](storage.md#glob): List resources that match PATTERNS
* [neuro storage rm](storage.md#rm): Remove files or directories
* [neuro storage mkdir](storage.md#mkdir): Make directories
* [neuro storage mv](storage.md#mv): Move or rename files and directories
* [neuro storage tree](storage.md#tree): List contents of directories in a tree-like...

### cp

Copy files and directories

#### Usage

```bash
neuro storage cp [OPTIONS] [SOURCES]... [DESTINATION]
```

Copy files and directories.

Either `SOURCES` or `DESTINATION` should have
storage:// scheme.
If scheme is omitted, file:// scheme is assumed.

Use
/dev/stdin and /dev/stdout file names to copy a file from terminal
and print
the content of file on the storage to console.

Any number of --exclude and
--include options can be passed.  The
filters that appear later in the command
take precedence over filters
that appear earlier in the command.  If neither
--exclude nor
--include options are specified the default can be changed using
the
storage.cp-exclude configuration variable documented in
"neuro help user-
config".

#### Examples

```bash

# copy local files into remote storage root
$ neuro cp foo.txt bar/baz.dat storage:
$ neuro cp foo.txt bar/baz.dat -t storage:

# copy local directory `foo` into existing remote directory `bar`
$ neuro cp -r foo -t storage:bar

# copy the content of local directory `foo` into existing remote
# directory `bar`
$ neuro cp -r -T storage:foo storage:bar

# download remote file `foo.txt` into local file `/tmp/foo.txt` with
# explicit file:// scheme set
$ neuro cp storage:foo.txt file:///tmp/foo.txt
$ neuro cp -T storage:foo.txt file:///tmp/foo.txt
$ neuro cp storage:foo.txt file:///tmp
$ neuro cp storage:foo.txt -t file:///tmp

# download other user's remote file into the current directory
$ neuro cp storage://{username}/foo.txt .

# download only files with extension `.out` into the current directory
$ neuro cp storage:results/*.out .
```

#### Options

| Name                                       | Description                                                                                                                                                                                                                               |
| ------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--help`                                   | Show this message and exit.                                                                                                                                                                                                               |
| `--continue`                               | Continue copying partially-copied files.                                                                                                                                                                                                  |
| `--exclude-from-files FILES`               | A list of file names that contain patterns for exclusion files and directories. Used only for uploading. The default can be changed using the storage.cp-exclude-from-files configuration variable documented in "neuro help user-config" |
| `--exclude`                                | Exclude files and directories that match the specified pattern.                                                                                                                                                                           |
| `--include`                                | Don't exclude files and directories that match the specified pattern.                                                                                                                                                                     |
| `--glob` / `--no-glob`                     | Expand glob patterns in SOURCES with explicit scheme.  _[default: True]_                                                                                                                                                                  |
| `-T`, `--no-target-directory`              | Treat DESTINATION as a normal file.                                                                                                                                                                                                       |
| `-p`, `--progress` / `-P`, `--no-progress` | Show progress, on by default in TTY mode, off otherwise.                                                                                                                                                                                  |
| `-r`, `--recursive`                        | Recursive copy, off by default                                                                                                                                                                                                            |
| `-t`, `--target-directory DIRECTORY`       | Copy all SOURCES into DIRECTORY.                                                                                                                                                                                                          |
| `-u`, `--update`                           | Copy only when the SOURCE file is newer than the destination file or when the destination file is missing.                                                                                                                                |

### ls

List directory contents

#### Usage

```bash
neuro storage ls [OPTIONS] [PATHS]...
```

List directory contents.

By default `PATH` is equal user's home dir
(storage:)

#### Options

| Name                      | Description                                          |
| ------------------------- | ---------------------------------------------------- |
| `--help`                  | Show this message and exit.                          |
| `-d`, `--directory`       | list directories themselves, not their contents.     |
| `-l`                      | use a long listing format.                           |
| `-h`, `--human-readable`  | with -l print human readable sizes (e.g., 2K, 540M). |
| `-a`, `--all`             | do not ignore entries starting with .                |
| `--sort [name|size|time]` | sort by given field, default is name.                |

### glob

List resources that match PATTERNS

#### Usage

```bash
neuro storage glob [OPTIONS] [PATTERNS]...
```

List resources that match `PATTERNS`.

#### Options

| Name     | Description                 |
| -------- | --------------------------- |
| `--help` | Show this message and exit. |

### rm

Remove files or directories

#### Usage

```bash
neuro storage rm [OPTIONS] PATHS...
```

Remove files or directories.

#### Examples

```bash

$ neuro rm storage:foo/bar
$ neuro rm storage://{username}/foo/bar
$ neuro rm --recursive storage://{username}/foo/
$ neuro rm storage:foo/**/*.tmp
```

#### Options

| Name                                       | Description                                              |
| ------------------------------------------ | -------------------------------------------------------- |
| `--help`                                   | Show this message and exit.                              |
| `--glob` / `--no-glob`                     | Expand glob patterns in PATHS  _[default: True]_         |
| `-p`, `--progress` / `-P`, `--no-progress` | Show progress, on by default in TTY mode, off otherwise. |
| `-r`, `--recursive`                        | remove directories and their contents recursively        |

### mkdir

Make directories

#### Usage

```bash
neuro storage mkdir [OPTIONS] PATHS...
```

Make directories.

#### Options

| Name              | Description                                             |
| ----------------- | ------------------------------------------------------- |
| `--help`          | Show this message and exit.                             |
| `-p`, `--parents` | No error if existing, make parent directories as needed |

### mv

Move or rename files and directories

#### Usage

```bash
neuro storage mv [OPTIONS] [SOURCES]... [DESTINATION]
```

Move or rename files and directories.

`SOURCE` must contain path to the
file
or directory existing on the storage, and `DESTINATION` must contain
the full
path to the target file or directory.

#### Examples

```bash

# move and rename remote file
$ neuro mv storage:foo.txt storage:bar/baz.dat
$ neuro mv -T storage:foo.txt storage:bar/baz.dat

# move remote files into existing remote directory
$ neuro mv storage:foo.txt storage:bar/baz.dat storage:dst
$ neuro mv storage:foo.txt storage:bar/baz.dat -t storage:dst

# move the content of remote directory into other existing
# remote directory
$ neuro mv -T storage:foo storage:bar

# move remote file into other user's directory
$ neuro mv storage:foo.txt storage://{username}/bar.dat

# move remote file from other user's directory
$ neuro mv storage://{username}/foo.txt storage:bar.dat
```

#### Options

| Name                                 | Description                                        |
| ------------------------------------ | -------------------------------------------------- |
| `--help`                             | Show this message and exit.                        |
| `--glob` / `--no-glob`               | Expand glob patterns in SOURCES  _[default: True]_ |
| `-T`, `--no-target-directory`        | Treat DESTINATION as a normal file                 |
| `-t`, `--target-directory DIRECTORY` | Copy all SOURCES into DIRECTORY                    |

### tree

List contents of directories in a tree-like...

#### Usage

```bash
neuro storage tree [OPTIONS] [PATH]
```

List contents of directories in a tree-like format.

Tree is a recursive
directory listing program that produces a depth indented listing
of files,
which is colorized ala dircolors if the LS_`COLORS` environment variable is
set and output is to tty.  With no arguments, tree lists the files in the
storage:
directory.  When directory arguments are given, tree lists all the
files and/or
directories found in the given directories each in turn.  Upon
completion of listing
all files/directories found, tree returns the total
number of files and/or
directories listed.

By default `PATH` is equal user's
home dir (storage:)

#### Options

| Name                      | Description                                  |
| ------------------------- | -------------------------------------------- |
| `--help`                  | Show this message and exit.                  |
| `-h`, `--human-readable`  | Print the size in a more human readable way. |
| `-a`, `--all`             | do not ignore entries starting with .        |
| `-s`, `--size`            | Print the size in bytes of each file.        |
| `--sort [name|size|time]` | sort by given field, default is name         |

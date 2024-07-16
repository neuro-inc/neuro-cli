# storage

Storage operations

## Usage

```bash
apolo storage [OPTIONS] COMMAND [ARGS]...
```

Storage operations.

**Commands:**

| Usage | Description |
| :--- | :--- |
| [_cp_](storage.md#cp) | Copy files and directories |
| [_ls_](storage.md#ls) | List directory contents |
| [_glob_](storage.md#glob) | List resources that match PATTERNS |
| [_rm_](storage.md#rm) | Remove files or directories |
| [_mkdir_](storage.md#mkdir) | Make directories |
| [_mv_](storage.md#mv) | Move or rename files and directories |
| [_tree_](storage.md#tree) | List contents of directories in a tree-like... |

### cp

Copy files and directories

#### Usage

```bash
apolo storage cp [OPTIONS] [SOURCES]... [DESTINATION]
```

Copy files and directories.

Either `SOURCES` or `DESTINATION` should have storage:// scheme. If scheme is omitted, file:// scheme is assumed.

Use /dev/stdin and /dev/stdout file names to copy a file from terminal and print the content of file on the storage to console.

Any number of --exclude and --include options can be passed. The filters that appear later in the command take precedence over filters that appear earlier in the command. If neither --exclude nor --include options are specified the default can be changed using the storage.cp-exclude configuration variable documented in "apolo help user- config".

#### Examples

```bash
# copy local files into remote storage root
$ apolo cp foo.txt bar/baz.dat storage:
$ apolo cp foo.txt bar/baz.dat -t storage:

# copy local directory `foo` into existing remote directory `bar`
$ apolo cp -r foo -t storage:bar

# copy the content of local directory `foo` into existing remote
# directory `bar`
$ apolo cp -r -T storage:foo storage:bar

# download remote file `foo.txt` into local file `/tmp/foo.txt` with
# explicit file:// scheme set
$ apolo cp storage:foo.txt file:///tmp/foo.txt
$ apolo cp -T storage:foo.txt file:///tmp/foo.txt
$ apolo cp storage:foo.txt file:///tmp
$ apolo cp storage:foo.txt -t file:///tmp

# download other user's remote file into the current directory
$ apolo cp storage://{username}/foo.txt .

# download only files with extension `.out` into the current directory
$ apolo cp storage:results/*.out .
```

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--continue_ | Continue copying partially-copied files. |
| _--exclude-from-files FILES_ | A list of file names that contain patterns for exclusion files and directories. Used only for uploading. The default can be changed using the storage.cp-exclude-from-files configuration variable documented in "apolo help user-config" |
| _--exclude_ | Exclude files and directories that match the specified pattern. |
| _--include_ | Don't exclude files and directories that match the specified pattern. |
| _--glob / --no-glob_ | Expand glob patterns in SOURCES with explicit scheme.  _\[default: True\]_ |
| _-T, --no-target-directory_ | Treat DESTINATION as a normal file. |
| _-p, --progress / -P, --no-progress_ | Show progress, on by default in TTY mode, off otherwise. |
| _-r, --recursive_ | Recursive copy, off by default |
| _-t, --target-directory DIRECTORY_ | Copy all SOURCES into DIRECTORY. |
| _-u, --update_ | Copy only when the SOURCE file is newer than the destination file or when the destination file is missing. |

### ls

List directory contents

#### Usage

```bash
apolo storage ls [OPTIONS] [PATHS]...
```

List directory contents.

By default `PATH` is equal user's home dir \(storage:\)

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _-d, --directory_ | list directories themselves, not their contents. |
| _-l_ | use a long listing format. |
| _-h, --human-readable_ | with -l print human readable sizes \(e.g., 2K, 540M\). |
| _-a, --all_ | do not ignore entries starting with . |
| _--sort \[name \| size \| time\]_ | sort by given field, default is name. |

### glob

List resources that match PATTERNS

#### Usage

```bash
apolo storage glob [OPTIONS] [PATTERNS]...
```

List resources that match `PATTERNS`.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

### rm

Remove files or directories

#### Usage

```bash
apolo storage rm [OPTIONS] PATHS...
```

Remove files or directories.

#### Examples

```bash
$ apolo rm storage:foo/bar
$ apolo rm storage://{username}/foo/bar
$ apolo rm --recursive storage://{username}/foo/
$ apolo rm storage:foo/**/*.tmp
```

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--glob / --no-glob_ | Expand glob patterns in PATHS  _\[default: True\]_ |
| _-p, --progress / -P, --no-progress_ | Show progress, on by default in TTY mode, off otherwise. |
| _-r, --recursive_ | remove directories and their contents recursively |

### mkdir

Make directories

#### Usage

```bash
apolo storage mkdir [OPTIONS] PATHS...
```

Make directories.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _-p, --parents_ | No error if existing, make parent directories as needed |

### mv

Move or rename files and directories

#### Usage

```bash
apolo storage mv [OPTIONS] [SOURCES]... [DESTINATION]
```

Move or rename files and directories.

`SOURCE` must contain path to the file or directory existing on the storage, and `DESTINATION` must contain the full path to the target file or directory.

#### Examples

```bash
# move and rename remote file
$ apolo mv storage:foo.txt storage:bar/baz.dat
$ apolo mv -T storage:foo.txt storage:bar/baz.dat

# move remote files into existing remote directory
$ apolo mv storage:foo.txt storage:bar/baz.dat storage:dst
$ apolo mv storage:foo.txt storage:bar/baz.dat -t storage:dst

# move the content of remote directory into other existing
# remote directory
$ apolo mv -T storage:foo storage:bar

# move remote file into other user's directory
$ apolo mv storage:foo.txt storage://{username}/bar.dat

# move remote file from other user's directory
$ apolo mv storage://{username}/foo.txt storage:bar.dat
```

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--glob / --no-glob_ | Expand glob patterns in SOURCES  _\[default: True\]_ |
| _-T, --no-target-directory_ | Treat DESTINATION as a normal file |
| _-t, --target-directory DIRECTORY_ | Copy all SOURCES into DIRECTORY |

### tree

List contents of directories in a tree-like...

#### Usage

```bash
apolo storage tree [OPTIONS] [PATH]
```

List contents of directories in a tree-like format.

Tree is a recursive directory listing program that produces a depth indented listing of files, which is colorized ala dircolors if the LS\_`COLORS` environment variable is set and output is to tty. With no arguments, tree lists the files in the storage: directory. When directory arguments are given, tree lists all the files and/or directories found in the given directories each in turn. Upon completion of listing all files/directories found, tree returns the total number of files and/or directories listed.

By default `PATH` is equal user's home dir \(storage:\)

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _-h, --human-readable_ | Print the size in a more human readable way. |
| _-a, --all_ | do not ignore entries starting with . |
| _-s, --size_ | Print the size in bytes of each file. |
| _--sort \[name \| size \| time\]_ | sort by given field, default is name |


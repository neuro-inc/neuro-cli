# blob

Blob storage operations

## Usage

```bash
neuro blob [OPTIONS] COMMAND [ARGS]...
```

Blob storage operations.

## Commands

* [neuro blob cp](blob.md#cp): Simple utility to copy files and directories...
* [neuro blob ls](blob.md#ls): List buckets or bucket contents
* [neuro blob glob](blob.md#glob): List resources that match PATTERNS

### cp

Simple utility to copy files and directories...

#### Usage

```bash
neuro blob cp [OPTIONS] [SOURCES]... [DESTINATION]
```

Simple utility to copy files and directories into and from Blob Storage.
Either `SOURCES` or `DESTINATION` should have `blob://` scheme.
If scheme is
omitted, file:// scheme is assumed. It is currently not possible to
copy files
between Blob Storage (`blob://`) destination, nor with `storage://`
scheme
paths.

Use `/dev/stdin` and `/dev/stdout` file names to upload a file from
standard input
or output to stdout.

Any number of --exclude and --include
options can be passed.  The
filters that appear later in the command take
precedence over filters
that appear earlier in the command.  If neither
--exclude nor
--include options are specified the default can be changed using
the
storage.cp-exclude configuration variable documented in
"neuro help user-
config".

File permissions, modification times and other attributes will not
be passed to
Blob Storage metadata during upload.

#### Options

| Name                                       | Description                                                                                                                                                                                                                               |
| ------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--help`                                   | Show this message and exit.                                                                                                                                                                                                               |
| `--continue`                               | Continue copying partially-copied files. Only for copying from Blob Storage.                                                                                                                                                              |
| `--exclude-from-files FILES`               | A list of file names that contain patterns for exclusion files and directories. Used only for uploading. The default can be changed using the storage.cp-exclude-from-files configuration variable documented in "neuro help user-config" |
| `--exclude`                                | Exclude files and directories that match the specified pattern.                                                                                                                                                                           |
| `--include`                                | Don't exclude files and directories that match the specified pattern.                                                                                                                                                                     |
| `--glob` / `--no-glob`                     | Expand glob patterns in SOURCES with explicit scheme.  _[default: True]_                                                                                                                                                                  |
| `-T`, `--no-target-directory`              | Treat DESTINATION as a normal file.                                                                                                                                                                                                       |
| `-p`, `--progress` / `-P`, `--no-progress` | Show progress, on by default.                                                                                                                                                                                                             |
| `-r`, `--recursive`                        | Recursive copy, off by default                                                                                                                                                                                                            |
| `-t`, `--target-directory DIRECTORY`       | Copy all SOURCES into DIRECTORY.                                                                                                                                                                                                          |
| `-u`, `--update`                           | Copy only when the SOURCE file is newer than the destination file or when the destination file is missing.                                                                                                                                |

### ls

List buckets or bucket contents

#### Usage

```bash
neuro blob ls [OPTIONS] [PATHS]...
```

List buckets or bucket contents.

#### Options

| Name                      | Description                                                         |
| ------------------------- | ------------------------------------------------------------------- |
| `--help`                  | Show this message and exit.                                         |
| `-l`                      | use a long listing format.                                          |
| `-h`, `--human-readable`  | with -l print human readable sizes (e.g., 2K, 540M).                |
| `-r`, `--recursive`       | List all keys under the URL path provided, not just 1 level depths. |
| `--sort [name|size|time]` | sort by given field, default is name.                               |

### glob

List resources that match PATTERNS

#### Usage

```bash
neuro blob glob [OPTIONS] [PATTERNS]...
```

List resources that match `PATTERNS`.

#### Options

| Name     | Description                 |
| -------- | --------------------------- |
| `--help` | Show this message and exit. |

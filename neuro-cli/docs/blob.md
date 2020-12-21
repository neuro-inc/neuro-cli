# blob

Blob storage operations

## Usage

```bash
neuro blob [OPTIONS] COMMAND [ARGS]...
```

Blob storage operations.

**Commands:**


| Usage | Description |

| :--- | :--- |

| [_cp_](blob.md#cp) | Simple utility to copy files and directories... |

| [_ls_](blob.md#ls) | List buckets or bucket contents |

| [_glob_](blob.md#glob) | List resources that match PATTERNS |



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


| Name | Description |

| :--- | :--- |

| _`--help`_ | Show this message and exit. |

| _`--continue`_ | Continue copying partially-copied files. Only for copying from Blob Storage. |

| _`--exclude-from-files FILES`_ | A list of file names that contain patterns for exclusion files and directories. Used only for uploading. The default can be changed using the storage.cp-exclude-from-files configuration variable documented in "neuro help user-config" |

| _`--exclude`_ | Exclude files and directories that match the specified pattern. |

| _`--include`_ | Don't exclude files and directories that match the specified pattern. |

| _`--glob` / `--no-glob`_ | Expand glob patterns in SOURCES with explicit scheme.  \_\[default: True\]\_ |

| _`-T`, `--no-target-directory`_ | Treat DESTINATION as a normal file. |

| _`-p`, `--progress` / `-P`, `--no-progress`_ | Show progress, on by default. |

| _`-r`, `--recursive`_ | Recursive copy, off by default |

| _`-t`, `--target-directory DIRECTORY`_ | Copy all SOURCES into DIRECTORY. |

| _`-u`, `--update`_ | Copy only when the SOURCE file is newer than the destination file or when the destination file is missing. |




### ls



List buckets or bucket contents



#### Usage

```bash
neuro blob ls [OPTIONS] [PATHS]...
```

List buckets or bucket contents.

#### Options


| Name | Description |

| :--- | :--- |

| _`--help`_ | Show this message and exit. |

| _`-l`_ | use a long listing format. |

| _`-h`, `--human-readable`_ | with -l print human readable sizes \(e.g., 2K, 540M\). |

| _`-r`, `--recursive`_ | List all keys under the URL path provided, not just 1 level depths. |

| _`--sort \[name &#124; size &#124; time\]`_ | sort by given field, default is name. |




### glob



List resources that match PATTERNS



#### Usage

```bash
neuro blob glob [OPTIONS] [PATTERNS]...
```

List resources that match `PATTERNS`.

#### Options


| Name | Description |

| :--- | :--- |

| _`--help`_ | Show this message and exit. |




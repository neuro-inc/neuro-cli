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
| [_lsbucket_](blob.md#lsbucket) | List buckets |
| [_mkbucket_](blob.md#mkbucket) | Create a new bucket |
| [_statbucket_](blob.md#statbucket) | Get bucket BUCKET\_ID |
| [_rmbucket_](blob.md#rmbucket) | Remove bucket DISK\_ID |
| [_cp_](blob.md#cp) | Simple utility to copy files and... |
| [_ls_](blob.md#ls) | List buckets or bucket contents |
| [_glob_](blob.md#glob) | List resources that match PATTERNS |
| [_rm_](blob.md#rm) | Remove blobs from bucket |


### lsbucket

List buckets


#### Usage

```bash
neuro blob lsbucket [OPTIONS]
```

List buckets.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--cluster CLUSTER_ | Look on a specified cluster \(the current cluster by default\). |
| _--full-uri_ | Output full bucket URI. |
| _--long-format_ | Output all info about bucket. |



### mkbucket

Create a new bucket


#### Usage

```bash
neuro blob mkbucket [OPTIONS]
```

Create a new bucket.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--cluster CLUSTER_ | Perform in a specified cluster \(the current cluster by default\). |
| _--name NAME_ | Optional bucket name |



### statbucket

Get bucket BUCKET_ID


#### Usage

```bash
neuro blob statbucket [OPTIONS] BUCKET
```

Get bucket `BUCKET`_ID.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--cluster CLUSTER_ | Look on a specified cluster \(the current cluster by default\). |
| _--full-uri_ | Output full bucket URI. |



### rmbucket

Remove bucket DISK_ID


#### Usage

```bash
neuro blob rmbucket [OPTIONS] BUCKETS...
```

Remove bucket `DISK`_ID.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--cluster CLUSTER_ | Perform on a specified cluster \(the current cluster by default\). |



### cp

Simple utility to copy files and...


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
| _--help_ | Show this message and exit. |
| _--continue_ | Continue copying partially-copied files. Only for copying from Blob Storage. |
| _--exclude-from-files FILES_ | A list of file names that contain patterns for exclusion files and directories. Used only for uploading. The default can be changed using the storage.cp-exclude-from-files configuration variable documented in "neuro help user-config" |
| _--exclude_ | Exclude files and directories that match the specified pattern. |
| _--include_ | Don't exclude files and directories that match the specified pattern. |
| _--glob / --no-glob_ | Expand glob patterns in SOURCES with explicit scheme.  _\[default: glob\]_ |
| _-T, --no-target-directory_ | Treat DESTINATION as a normal file. |
| _-p, --progress / -P, --no-progress_ | Show progress, on by default. |
| _-r, --recursive_ | Recursive copy, off by default |
| _-t, --target-directory DIRECTORY_ | Copy all SOURCES into DIRECTORY. |
| _-u, --update_ | Copy only when the SOURCE file is newer than the destination file or when the destination file is missing. |



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
| _--help_ | Show this message and exit. |
| _-l_ | use a long listing format. |
| _--full-uri_ | Output full bucket URI. |
| _-h, --human-readable_ | with -l print human readable sizes \(e.g., 2K, 540M\). |
| _-r, --recursive_ | List all keys under the URL path provided, not just 1 level depths. |



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
| _--help_ | Show this message and exit. |
| _--full-uri_ | Output full bucket URI. |



### rm

Remove blobs from bucket


#### Usage

```bash
neuro blob rm [OPTIONS] PATHS...
```

Remove blobs from bucket.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--glob / --no-glob_ | Expand glob patterns in PATHS  _\[default: glob\]_ |
| _-p, --progress / -P, --no-progress_ | Show progress, on by default in TTY mode, off otherwise. |
| _-r, --recursive_ | remove directories and their contents recursively |



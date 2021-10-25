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
| [_importbucket_](blob.md#importbucket) | Import an existing bucket |
| [_statbucket_](blob.md#statbucket) | Get bucket BUCKET |
| [_rmbucket_](blob.md#rmbucket) | Remove bucket BUCKET |
| [_set-bucket-publicity_](blob.md#set-bucket-publicity) | Change public access settings for bucket... |
| [_lscredentials_](blob.md#lscredentials) | List bucket credentials |
| [_mkcredentials_](blob.md#mkcredentials) | Create a new bucket credential |
| [_statcredentials_](blob.md#statcredentials) | Get bucket credential BUCKET\_CREDENTIAL |
| [_rmcredentials_](blob.md#rmcredentials) | Remove bucket credential BUCKET\_CREDENTIAL |
| [_cp_](blob.md#cp) | Simple utility to copy files and... |
| [_ls_](blob.md#ls) | List buckets or bucket contents |
| [_glob_](blob.md#glob) | List resources that match PATTERNS |
| [_rm_](blob.md#rm) | Remove blobs from bucket |
| [_sign-url_](blob.md#sign-url) | Make signed url for blob in bucket |
| [_du_](blob.md#du) | Get storage usage for BUCKET |


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



### importbucket

Import an existing bucket


#### Usage

```bash
neuro blob importbucket [OPTIONS]
```

Import an existing bucket.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--aws-access-key-id AWS\_ACCESS\_KEY\_ID_ | AWS access\_key\_id to use to access the bucket.  Required when PROVIDER is 'aws' |
| _--aws-endpoint-url AWS\_ENDPOINT_ | AWS endpoint to use to access the bucket. Usually you need to set this if you use non-AWS S3 compatible provider |
| _--aws-region-name AWS\_REGION_ | AWS region to use to access the bucket. |
| _--aws-secret-access-key AWS\_SECRET\_ACCESS\_KEY_ | AWS secret\_access\_key to use to access the bucket. Required when PROVIDER is 'aws' |
| _--azure-storage-account-url AZURE\_STORAGE\_ACCOUNT\_URL_ | Azure account url. Usually it has following format: https://&lt;account\_id&gt;.blob.core.windows.net Required when PROVIDER is 'azure' |
| _--azure-storage-credential AZURE\_STORAGE\_CREDENTIAL_ | Azure storage credential that grants access to imported bucket. Either this or AZURE\_SAS is required when PROVIDER is 'azure' |
| _--azure-storage-sas-token AZURE\_SAS_ | Azure shared access signature token that grants access to imported bucket. Either this or AZURE\_STORAGE\_CREDENTIAL is required when PROVIDER is 'azure' |
| _--cluster CLUSTER_ | Perform in a specified cluster \(the current cluster by default\). |
| _--gcp-sa-credential GCP\_SA\_CREDNETIAL_ | GCP service account credential in form of base64 encoded json string that grants access to imported bucket. Required when PROVIDER is 'gcp' |
| _--name NAME_ | Optional bucket name |
| _--provider PROVIDER_ | Bucket provider that hosts bucket  _\[required\]_ |
| _--provider-bucket-name EXTERNAL\_NAME_ | Name of bucket \(or container in case of Azure\) inside the provider  _\[required\]_ |



### statbucket

Get bucket BUCKET


#### Usage

```bash
neuro blob statbucket [OPTIONS] BUCKET
```

Get bucket `BUCKET`.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--cluster CLUSTER_ | Look on a specified cluster \(the current cluster by default\). |
| _--full-uri_ | Output full bucket URI. |



### rmbucket

Remove bucket BUCKET


#### Usage

```bash
neuro blob rmbucket [OPTIONS] BUCKETS...
```

Remove bucket `BUCKET`.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--cluster CLUSTER_ | Perform on a specified cluster \(the current cluster by default\). |



### set-bucket-publicity

Change public access settings for bucket...


#### Usage

```bash
neuro blob set-bucket-publicity [OPTIONS] BUCKET {public|private}
```

Change public access settings for bucket `BUCKET`.

#### Examples

```bash

$ neuro blob set-bucket-publicity my-bucket public
$ neuro blob set-bucket-publicity my-bucket private
```

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--cluster CLUSTER_ | Perform on a specified cluster \(the current cluster by default\). |



### lscredentials

List bucket credentials


#### Usage

```bash
neuro blob lscredentials [OPTIONS]
```

List bucket credentials.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--cluster CLUSTER_ | Look on a specified cluster \(the current cluster by default\). |



### mkcredentials

Create a new bucket credential


#### Usage

```bash
neuro blob mkcredentials [OPTIONS] BUCKETS...
```

Create a new bucket credential.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--cluster CLUSTER_ | Perform in a specified cluster \(the current cluster by default\). |
| _--name NAME_ | Optional bucket credential name |
| _--read-only_ | Make read-only credential |



### statcredentials

Get bucket credential BUCKET_CREDENTIAL


#### Usage

```bash
neuro blob statcredentials [OPTIONS] BUCKET_CREDENTIAL
```

Get bucket credential `BUCKET`_`CREDENTIAL`.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--cluster CLUSTER_ | Look on a specified cluster \(the current cluster by default\). |



### rmcredentials

Remove bucket credential BUCKET_CREDENTIAL


#### Usage

```bash
neuro blob rmcredentials [OPTIONS] CREDENTIALS...
```

Remove bucket credential `BUCKET`_`CREDENTIAL`.

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



### sign-url

Make signed url for blob in bucket


#### Usage

```bash
neuro blob sign-url [OPTIONS] PATH
```

Make signed url for blob in bucket.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--expires TIMEDELTA_ | Duration this signature will be valid in the format '1h2m3s'  _\[default: 1h\]_ |



### du

Get storage usage for BUCKET


#### Usage

```bash
neuro blob du [OPTIONS] BUCKET
```

Get storage usage for `BUCKET`.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--cluster CLUSTER_ | Look on a specified cluster \(the current cluster by default\). |



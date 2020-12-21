
## neuro

**Usage:**

```bash
neuro [OPTIONS] COMMAND [ARGS]...
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--color \[yes &#124; no &#124; auto\]_ | Color mode. |
| _--disable-pypi-version-check_ | Don't periodically check PyPI to determine whether a new version of Neuro Platform CLI is available for download. |
| _--hide-token / --no-hide-token_ | Prevent user's token sent in HTTP headers from being printed out to stderr during HTTP tracing. Can be used only together with option '--trace'. On by default. |
| _--network-timeout FLOAT_ | Network read timeout, seconds. |
| _--neuromation-config PATH_ | Path to config directory. |
| _-q, --quiet_ | Give less output. Option is additive, and can be used up to 2 times. |
| _--show-traceback_ | Show python traceback on error, useful for debugging the tool. |
| _--skip-stats / --no-skip-stats_ | Skip sending usage statistics to Neuro servers. Note: the statistics has no sensitive data, e.g. file, job, image, or user names, executed command lines, environment variables, etc. |
| _--trace_ | Trace sent HTTP requests and received replies to stderr. |
| _-v, --verbose_ | Give more output. Option is additive, and can be used up to 2 times. |
| _--version_ | Show the version and exit. |

**Command Groups:**

| Usage | Description |
| :--- | :--- |
| [_neuro admin_](CLI.md#neuro-admin) | Cluster administration commands |
| [_neuro job_](CLI.md#neuro-job) | Job operations |
| [_neuro project_](CLI.md#neuro-project) | Project operations |
| [_neuro storage_](CLI.md#neuro-storage) | Storage operations |
| [_neuro image_](CLI.md#neuro-image) | Container image operations |
| [_neuro config_](CLI.md#neuro-config) | Client configuration |
| [_neuro completion_](CLI.md#neuro-completion) | Output shell completion code |
| [_neuro acl_](CLI.md#neuro-acl) | Access Control List management |
| [_neuro blob_](CLI.md#neuro-blob) | Blob storage operations |
| [_neuro secret_](CLI.md#neuro-secret) | Operations with secrets |
| [_neuro disk_](CLI.md#neuro-disk) | Operations with disks |

**Commands:**

| Usage | Description |
| :--- | :--- |
| [_neuro help_](CLI.md#neuro-help) | Get help on a command |
| [_neuro run_](CLI.md#neuro-run) | Run a job with predefined resources configuration |
| [_neuro ps_](CLI.md#neuro-ps) | List all jobs |
| [_neuro status_](CLI.md#neuro-status) | Display status of a job |
| [_neuro exec_](CLI.md#neuro-exec) | Execute command in a running job |
| [_neuro port-forward_](CLI.md#neuro-port-forward) | Forward port\(s\) of a running job to local port\(s\) |
| [_neuro attach_](CLI.md#neuro-attach) | Attach local standard input, output, and error streams to a running job |
| [_neuro logs_](CLI.md#neuro-logs) | Print the logs for a job |
| [_neuro kill_](CLI.md#neuro-kill) | Kill job\(s\) |
| [_neuro top_](CLI.md#neuro-top) | Display GPU/CPU/Memory usage |
| [_neuro save_](CLI.md#neuro-save) | Save job's state to an image |
| [_neuro login_](CLI.md#neuro-login) | Log into Neuro Platform |
| [_neuro logout_](CLI.md#neuro-logout) | Log out |
| [_neuro cp_](CLI.md#neuro-cp) | Copy files and directories |
| [_neuro ls_](CLI.md#neuro-ls) | List directory contents |
| [_neuro rm_](CLI.md#neuro-rm) | Remove files or directories |
| [_neuro mkdir_](CLI.md#neuro-mkdir) | Make directories |
| [_neuro mv_](CLI.md#neuro-mv) | Move or rename files and directories |
| [_neuro images_](CLI.md#neuro-images) | List images |
| [_neuro push_](CLI.md#neuro-push) | Push an image to platform registry |
| [_neuro pull_](CLI.md#neuro-pull) | Pull an image from platform registry |
| [_neuro share_](CLI.md#neuro-share) | Shares resource with another user |

### neuro admin

Cluster administration commands.

**Usage:**

```bash
neuro admin [OPTIONS] COMMAND [ARGS]...
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

**Commands:**

| Usage | Description |
| :--- | :--- |
| [_neuro admin get-clusters_](CLI.md#neuro-admin-get-clusters) | Print the list of available clusters |
| [_neuro admin generate-cluster-config_](CLI.md#neuro-admin-generate-cluster-config) | Create a cluster configuration file |
| [_neuro admin add-cluster_](CLI.md#neuro-admin-add-cluster) | Create a new cluster and start its provisioning |
| [_neuro admin show-cluster-options_](CLI.md#neuro-admin-show-cluster-options) | Create a cluster configuration file |
| [_neuro admin get-cluster-users_](CLI.md#neuro-admin-get-cluster-users) | Print the list of all users in the cluster with their assigned role |
| [_neuro admin add-cluster-user_](CLI.md#neuro-admin-add-cluster-user) | Add user access to specified cluster |
| [_neuro admin remove-cluster-user_](CLI.md#neuro-admin-remove-cluster-user) | Remove user access from the cluster |
| [_neuro admin set-user-quota_](CLI.md#neuro-admin-set-user-quota) | Set user quota to given values |
| [_neuro admin add-user-quota_](CLI.md#neuro-admin-add-user-quota) | Add given values to user quota |
| [_neuro admin update-resource-preset_](CLI.md#neuro-admin-update-resource-preset) | Add/update resource preset |
| [_neuro admin remove-resource-preset_](CLI.md#neuro-admin-remove-resource-preset) | Remove resource preset |

#### neuro admin get-clusters

Print the list of available clusters.

**Usage:**

```bash
neuro admin get-clusters [OPTIONS]
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

#### neuro admin generate-cluster-config

Create a cluster configuration file.

**Usage:**

```bash
neuro admin generate-cluster-config [OPTIONS] [CONFIG]
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--type \[aws &#124; gcp &#124; azure\]_ |  |

#### neuro admin add-cluster

Create a new cluster and start its provisioning.

**Usage:**

```bash
neuro admin add-cluster [OPTIONS] CLUSTER_NAME CONFIG
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

#### neuro admin show-cluster-options

Create a cluster configuration file.

**Usage:**

```bash
neuro admin show-cluster-options [OPTIONS]
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--type \[aws &#124; gcp &#124; azure\]_ |  |

#### neuro admin get-cluster-users

Print the list of all users in the cluster with their assigned role.

**Usage:**

```bash
neuro admin get-cluster-users [OPTIONS] [CLUSTER_NAME]
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

#### neuro admin add-cluster-user

Add user access to specified cluster.

The command supports one of 3 user roles: admin, manager or user.

**Usage:**

```bash
neuro admin add-cluster-user [OPTIONS] CLUSTER_NAME USER_NAME [ROLE]
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

#### neuro admin remove-cluster-user

Remove user access from the cluster.

**Usage:**

```bash
neuro admin remove-cluster-user [OPTIONS] CLUSTER_NAME USER_NAME
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

#### neuro admin set-user-quota

Set user quota to given values

**Usage:**

```bash
neuro admin set-user-quota [OPTIONS] CLUSTER_NAME USER_NAME
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _-g, --gpu AMOUNT_ | GPU quota value in hours \(h\) or minutes \(m\). |
| _-j, --jobs AMOUNT_ | Maximum running jobs quota |
| _-n, --non-gpu AMOUNT_ | Non-GPU quota value in hours \(h\) or minutes \(m\). |

#### neuro admin add-user-quota

Add given values to user quota

**Usage:**

```bash
neuro admin add-user-quota [OPTIONS] CLUSTER_NAME USER_NAME
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _-g, --gpu AMOUNT_ | Additional GPU quota value in hours \(h\) or minutes \(m\). |
| _-n, --non-gpu AMOUNT_ | Additional non-GPU quota value in hours \(h\) or minutes \(m\). |

#### neuro admin update-resource-preset

Add/update resource preset

**Usage:**

```bash
neuro admin update-resource-preset [OPTIONS] CLUSTER_NAME PRESET_NAME
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _-c, --cpu NUMBER_ | Number of CPUs  \[default: 0.1\] |
| _-g, --gpu NUMBER_ | Number of GPUs |
| _--gpu-model MODEL_ | GPU model |
| _-m, --memory AMOUNT_ | Memory amount  \[default: 1G\] |
| _-p, --preemptible / -P, --non-preemptible_ | Job preemptability support  \[default: False\] |
| _--preemptible-node / --non-preemptible-node_ | Use a lower-cost preemptible instance  \[default: False\] |
| _--tpu-sw-version VERSION_ | TPU software version |
| _--tpu-type TYPE_ | TPU type |

#### neuro admin remove-resource-preset

Remove resource preset

**Usage:**

```bash
neuro admin remove-resource-preset [OPTIONS] CLUSTER_NAME PRESET_NAME
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

### neuro job

Job operations.

**Usage:**

```bash
neuro job [OPTIONS] COMMAND [ARGS]...
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

**Commands:**

| Usage | Description |
| :--- | :--- |
| [_neuro job run_](CLI.md#neuro-job-run) | Run a job with predefined resources configuration |
| [_neuro job ls_](CLI.md#neuro-job-ls) | List all jobs |
| [_neuro job status_](CLI.md#neuro-job-status) | Display status of a job |
| [_neuro job tags_](CLI.md#neuro-job-tags) | List all tags submitted by the user |
| [_neuro job exec_](CLI.md#neuro-job-exec) | Execute command in a running job |
| [_neuro job port-forward_](CLI.md#neuro-job-port-forward) | Forward port\(s\) of a running job to local port\(s\) |
| [_neuro job logs_](CLI.md#neuro-job-logs) | Print the logs for a job |
| [_neuro job kill_](CLI.md#neuro-job-kill) | Kill job\(s\) |
| [_neuro job top_](CLI.md#neuro-job-top) | Display GPU/CPU/Memory usage |
| [_neuro job save_](CLI.md#neuro-job-save) | Save job's state to an image |
| [_neuro job browse_](CLI.md#neuro-job-browse) | Opens a job's URL in a web browser |
| [_neuro job attach_](CLI.md#neuro-job-attach) | Attach local standard input, output, and error streams to a running job |

#### neuro job run

Run a job with predefined resources configuration.

IMAGE docker image name to run in a job.

CMD list will be passed as arguments to the executed job's image.

**Usage:**

```bash
neuro job run [OPTIONS] IMAGE [CMD]...
```

**Examples:**

```bash

# Starts a container pytorch:latest on a machine with smaller GPU resources
# (see exact values in `neuro config show`) and with two volumes mounted:
#   storage:/<home-directory>   --> /var/storage/home (in read-write mode),
#   storage:/neuromation/public --> /var/storage/neuromation (in read-only mode).
neuro run --preset=gpu-small --volume=storage::/var/storage/home:rw \
--volume=storage:/neuromation/public:/var/storage/home:ro pytorch:latest

# Starts a container using the custom image my-ubuntu:latest stored in neuro
# registry, run /script.sh and pass arg1 and arg2 as its arguments:
neuro run -s cpu-small image:my-ubuntu:latest --entrypoint=/script.sh arg1 arg2

```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--browse_ | Open a job's URL in a web browser |
| _-d, --description DESC_ | Optional job description in free format |
| _--detach_ | Don't attach to job logs and don't wait for exit code |
| _--entrypoint TEXT_ | Executable entrypoint in the container \(note that it overwrites `ENTRYPOINT` and `CMD` instructions of the docker image\) |
| _-e, --env VAR=VAL_ | Set environment variable in container. Use multiple options to define more than one variable. See `neuro help secrets` for information about passing secrets as environment variables. |
| _--env-file PATH_ | File with environment variables to pass |
| _-x, --extshm / -X, --no-extshm_ | Request extended '/dev/shm' space  \[default: True\] |
| _--http PORT_ | Enable HTTP port forwarding to container  \[default: 80\] |
| _--http-auth / --no-http-auth_ | Enable HTTP authentication for forwarded HTTP port  \[default: True\] |
| _--life-span TIMEDELTA_ | Optional job run-time limit in the format '1d2h3m4s' \(some parts may be missing\). Set '0' to disable. Default value '1d' can be changed in the user config. |
| _-n, --name NAME_ | Optional job name |
| _--pass-config / --no-pass-config_ | Upload neuro config to the job  \[default: False\] |
| _--port-forward LOCAL\_PORT:REMOTE\_RORT_ | Forward port\(s\) of a running job to local port\(s\) \(use multiple times for forwarding several ports\) |
| _-s, --preset PRESET_ | Predefined resource configuration \(to see available values, run `neuro config show`\) |
| _--privileged TEXT_ | Run job in privileged mode, if it is supported by cluster.  \[default: False\] |
| _-q, --quiet_ | Run command in quiet mode \(DEPRECATED\) |
| _--restart \[never &#124; on-failure &#124; always\]_ | Restart policy to apply when a job exits  \[default: never\] |
| _--schedule-timeout TIMEDELTA_ | Optional job schedule timeout in the format '3m4s' \(some parts may be missing\). |
| _--tag TAG_ | Optional job tag, multiple values allowed |
| _-t, --tty / -T, --no-tty_ | Allocate a TTY, can be useful for interactive jobs. By default is on if the command is executed from a terminal, non-tty mode is used if executed from a script. |
| _-v, --volume MOUNT_ | Mounts directory from vault into container. Use multiple options to mount more than one volume. See `neuro help secrets` for information about passing secrets as mounted files. |
| _--wait-for-seat / --no-wait-for-seat_ | Wait for total running jobs quota  \[default: False\] |
| _--wait-start / --no-wait-start_ | Wait for a job start or failure  \[default: True\] |
| _-w, --workdir TEXT_ | Working directory inside the container |

#### neuro job ls

List all jobs.

**Usage:**

```bash
neuro job ls [OPTIONS]
```

**Examples:**

```bash

neuro ps -a
neuro ps -a --owner=user-1 --owner=user-2
neuro ps --name my-experiments-v1 -s failed -s succeeded
neuro ps --description=my favourite job
neuro ps -s failed -s succeeded -q
neuro ps -t tag1 -t tag2

```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _-a, --all_ | Show all jobs regardless the status. |
| _-d, --description DESCRIPTION_ | Filter out jobs by description \(exact match\). |
| _--format COLUMNS_ | Output table format, see "neuro help ps-format" for more info about the format specification. The default can be changed using the job.ps-format configuration variable documented in "neuro help user-config" |
| _--full-uri_ | Output full image URI. |
| _-n, --name NAME_ | Filter out jobs by name. |
| _-o, --owner TEXT_ | Filter out jobs by owner \(multiple option\). Supports `ME` option to filter by the current user. |
| _-q, --quiet_ | Run command in quiet mode \(DEPRECATED\) |
| _--since DATE_ | Show jobs created after a specific date \(including\). |
| _-s, --status \[pending &#124; suspended &#124; running &#124; succeeded &#124; failed &#124; cancelled\]_ | Filter out jobs by status \(multiple option\). |
| _-t, --tag TAG_ | Filter out jobs by tag \(multiple option\) |
| _--until DATE_ | Show jobs created before a specific date \(including\). |
| _-w, --wide_ | Do not cut long lines for terminal width. |

#### neuro job status

Display status of a job.

**Usage:**

```bash
neuro job status [OPTIONS] JOB
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--full-uri_ | Output full URI. |

#### neuro job tags

List all tags submitted by the user.

**Usage:**

```bash
neuro job tags [OPTIONS]
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

#### neuro job exec

Execute command in a running job.

**Usage:**

```bash
neuro job exec [OPTIONS] JOB CMD...
```

**Examples:**

```bash

# Provides a shell to the container:
neuro exec my-job /bin/bash

# Executes a single command in the container and returns the control:
neuro exec --no-tty my-job ls -l

```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _-t, --tty / -T, --no-tty_ | Allocate a TTY, can be useful for interactive jobs. By default is on if the command is executed from a terminal, non-tty mode is used if executed from a script. |

#### neuro job port-forward

Forward port(s) of a running job to local port(s).

**Usage:**

```bash
neuro job port-forward [OPTIONS] JOB LOCAL_PORT:REMOTE_RORT...
```

**Examples:**

```bash

# Forward local port 2080 to port 80 of job's container.
# You can use http://localhost:2080 in browser to access job's served http
neuro job port-forward my-fastai-job 2080:80

# Forward local port 2222 to job's port 22
# Then copy all data from container's folder '/data' to current folder
# (please run second command in other terminal)
neuro job port-forward my-job-with-ssh-server 2222:22
rsync -avxzhe ssh -p 2222 root@localhost:/data .

# Forward few ports at once
neuro job port-forward my-job 2080:80 2222:22 2000:100

```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

#### neuro job logs

Print the logs for a job.

**Usage:**

```bash
neuro job logs [OPTIONS] JOB
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

#### neuro job kill

Kill job(s).

**Usage:**

```bash
neuro job kill [OPTIONS] JOBS...
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

#### neuro job top

Display GPU/CPU/Memory usage.

**Usage:**

```bash
neuro job top [OPTIONS] JOB
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--timeout FLOAT_ | Maximum allowed time for executing the command, 0 for no timeout  \[default: 0\] |

#### neuro job save

Save job's state to an image.

**Usage:**

```bash
neuro job save [OPTIONS] JOB IMAGE
```

**Examples:**

```bash

neuro job save job-id image:ubuntu-patched
neuro job save my-favourite-job image:ubuntu-patched:v1
neuro job save my-favourite-job image://bob/ubuntu-patched

```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

#### neuro job browse

Opens a job's URL in a web browser.

**Usage:**

```bash
neuro job browse [OPTIONS] JOB
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

#### neuro job attach

Attach local standard input, output, and error streams to a running job.

**Usage:**

```bash
neuro job attach [OPTIONS] JOB
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--port-forward LOCAL\_PORT:REMOTE\_RORT_ | Forward port\(s\) of a running job to local port\(s\) \(use multiple times for forwarding several ports\) |

### neuro project

Project operations.

**Usage:**

```bash
neuro project [OPTIONS] COMMAND [ARGS]...
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

**Commands:**

| Usage | Description |
| :--- | :--- |
| [_neuro project init_](CLI.md#neuro-project-init) | Initialize an empty project |

#### neuro project init

Initialize an empty project.

**Usage:**

```bash
neuro project init [OPTIONS] [SLUG]
```

**Examples:**

```bash

# Initializes a scaffolding for the new project with the recommended project
# structure (see http://github.com/neuro-inc/cookiecutter-neuro-project)
neuro project init

# Initializes a scaffolding for the new project with the recommended project
# structure and sets default project folder name to "example"
neuro project init my-project-id

```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

### neuro storage

Storage operations.

**Usage:**

```bash
neuro storage [OPTIONS] COMMAND [ARGS]...
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

**Commands:**

| Usage | Description |
| :--- | :--- |
| [_neuro storage cp_](CLI.md#neuro-storage-cp) | Copy files and directories |
| [_neuro storage ls_](CLI.md#neuro-storage-ls) | List directory contents |
| [_neuro storage glob_](CLI.md#neuro-storage-glob) | List resources that match PATTERNS |
| [_neuro storage rm_](CLI.md#neuro-storage-rm) | Remove files or directories |
| [_neuro storage mkdir_](CLI.md#neuro-storage-mkdir) | Make directories |
| [_neuro storage mv_](CLI.md#neuro-storage-mv) | Move or rename files and directories |
| [_neuro storage tree_](CLI.md#neuro-storage-tree) | List contents of directories in a tree-like format |

#### neuro storage cp

Copy files and directories.

Either SOURCES or DESTINATION should have storage:// scheme. If scheme is omitted, file:// scheme is assumed.

Use /dev/stdin and /dev/stdout file names to copy a file from terminal and print the content of file on the storage to console.

Any number of --exclude and --include options can be passed.  The filters that appear later in the command take precedence over filters that appear earlier in the command.  If neither --exclude nor --include options are specified the default can be changed using the storage.cp-exclude configuration variable documented in "neuro help user-config".

**Usage:**

```bash
neuro storage cp [OPTIONS] [SOURCES]... [DESTINATION]
```

**Examples:**

```bash

# copy local files into remote storage root
neuro cp foo.txt bar/baz.dat storage:
neuro cp foo.txt bar/baz.dat -t storage:

# copy local directory `foo` into existing remote directory `bar`
neuro cp -r foo -t storage:bar

# copy the content of local directory `foo` into existing remote
# directory `bar`
neuro cp -r -T storage:foo storage:bar

# download remote file `foo.txt` into local file `/tmp/foo.txt` with
# explicit file:// scheme set
neuro cp storage:foo.txt file:///tmp/foo.txt
neuro cp -T storage:foo.txt file:///tmp/foo.txt
neuro cp storage:foo.txt file:///tmp
neuro cp storage:foo.txt -t file:///tmp

# download other user's remote file into the current directory
neuro cp storage://{username}/foo.txt .

# download only files with extension `.out` into the current directory
neuro cp storage:results/*.out .

```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--continue_ | Continue copying partially-copied files. |
| _--exclude-from-files FILES_ | A list of file names that contain patterns for exclusion files and directories. Used only for uploading. The default can be changed using the storage.cp-exclude-from-files configuration variable documented in "neuro help user-config" |
| _--exclude_ | Exclude files and directories that match the specified pattern. |
| _--include_ | Don't exclude files and directories that match the specified pattern. |
| _--glob / --no-glob_ | Expand glob patterns in SOURCES with explicit scheme.  \[default: True\] |
| _-T, --no-target-directory_ | Treat DESTINATION as a normal file. |
| _-p, --progress / -P, --no-progress_ | Show progress, on by default in TTY mode, off otherwise. |
| _-r, --recursive_ | Recursive copy, off by default |
| _-t, --target-directory DIRECTORY_ | Copy all SOURCES into DIRECTORY. |
| _-u, --update_ | Copy only when the SOURCE file is newer than the destination file or when the destination file is missing. |

#### neuro storage ls

List directory contents.

By default PATH is equal user's home dir (storage:)

**Usage:**

```bash
neuro storage ls [OPTIONS] [PATHS]...
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _-d, --directory_ | list directories themselves, not their contents. |
| _-l_ | use a long listing format. |
| _-h, --human-readable_ | with -l print human readable sizes \(e.g., 2K, 540M\). |
| _-a, --all_ | do not ignore entries starting with . |
| _--sort \[name &#124; size &#124; time\]_ | sort by given field, default is name. |

#### neuro storage glob

List resources that match PATTERNS.

**Usage:**

```bash
neuro storage glob [OPTIONS] [PATTERNS]...
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

#### neuro storage rm

Remove files or directories.

**Usage:**

```bash
neuro storage rm [OPTIONS] PATHS...
```

**Examples:**

```bash

neuro rm storage:foo/bar
neuro rm storage://{username}/foo/bar
neuro rm --recursive storage://{username}/foo/
neuro rm storage:foo/**/*.tmp

```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--glob / --no-glob_ | Expand glob patterns in PATHS  \[default: True\] |
| _-p, --progress / -P, --no-progress_ | Show progress, on by default in TTY mode, off otherwise. |
| _-r, --recursive_ | remove directories and their contents recursively |

#### neuro storage mkdir

Make directories.

**Usage:**

```bash
neuro storage mkdir [OPTIONS] PATHS...
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _-p, --parents_ | No error if existing, make parent directories as needed |

#### neuro storage mv

Move or rename files and directories.

SOURCE must contain path to the file or directory existing on the storage, and DESTINATION must contain the full path to the target file or directory.

**Usage:**

```bash
neuro storage mv [OPTIONS] [SOURCES]... [DESTINATION]
```

**Examples:**

```bash

# move and rename remote file
neuro mv storage:foo.txt storage:bar/baz.dat
neuro mv -T storage:foo.txt storage:bar/baz.dat

# move remote files into existing remote directory
neuro mv storage:foo.txt storage:bar/baz.dat storage:dst
neuro mv storage:foo.txt storage:bar/baz.dat -t storage:dst

# move the content of remote directory into other existing
# remote directory
neuro mv -T storage:foo storage:bar

# move remote file into other user's directory
neuro mv storage:foo.txt storage://{username}/bar.dat

# move remote file from other user's directory
neuro mv storage://{username}/foo.txt storage:bar.dat

```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--glob / --no-glob_ | Expand glob patterns in SOURCES  \[default: True\] |
| _-T, --no-target-directory_ | Treat DESTINATION as a normal file |
| _-t, --target-directory DIRECTORY_ | Copy all SOURCES into DIRECTORY |

#### neuro storage tree

List contents of directories in a tree-like format.

Tree is a recursive directory listing program that produces a depth indented listing of files, which is colorized ala dircolors if the LS_COLORS environment variable is set and output is to tty.  With no arguments, tree lists the files in the storage: directory.  When directory arguments are given, tree lists all the files and/or directories found in the given directories each in turn.  Upon completion of listing all files/directories found, tree returns the total number of files and/or directories listed.

By default PATH is equal user's home dir (storage:)

**Usage:**

```bash
neuro storage tree [OPTIONS] [PATH]
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _-h, --human-readable_ | Print the size in a more human readable way. |
| _-a, --all_ | do not ignore entries starting with . |
| _-s, --size_ | Print the size in bytes of each file. |
| _--sort \[name &#124; size &#124; time\]_ | sort by given field, default is name |

### neuro image

Container image operations.

**Usage:**

```bash
neuro image [OPTIONS] COMMAND [ARGS]...
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

**Commands:**

| Usage | Description |
| :--- | :--- |
| [_neuro image ls_](CLI.md#neuro-image-ls) | List images |
| [_neuro image push_](CLI.md#neuro-image-push) | Push an image to platform registry |
| [_neuro image pull_](CLI.md#neuro-image-pull) | Pull an image from platform registry |
| [_neuro image rm_](CLI.md#neuro-image-rm) | Remove image from platform registry |
| [_neuro image size_](CLI.md#neuro-image-size) | Get image size Image name must be URL with image:// scheme |
| [_neuro image digest_](CLI.md#neuro-image-digest) | Get digest of an image from remote registry Image name must be URL with image://... |
| [_neuro image tags_](CLI.md#neuro-image-tags) | List tags for image in platform registry |

#### neuro image ls

List images.

**Usage:**

```bash
neuro image ls [OPTIONS]
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _-l_ | List in long format. |
| _--full-uri_ | Output full image URI. |

#### neuro image push

Push an image to platform registry.

Remote image must be URL with image:// scheme. Image names can contain tag. If tags not specified 'latest' will be used as value.

**Usage:**

```bash
neuro image push [OPTIONS] LOCAL_IMAGE [REMOTE_IMAGE]
```

**Examples:**

```bash

neuro push myimage
neuro push alpine:latest image:my-alpine:production
neuro push alpine image://myfriend/alpine:shared

```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _-q, --quiet_ | Run command in quiet mode \(DEPRECATED\) |

#### neuro image pull

Pull an image from platform registry.

Remote image name must be URL with image:// scheme. Image names can contain tag.

**Usage:**

```bash
neuro image pull [OPTIONS] REMOTE_IMAGE [LOCAL_IMAGE]
```

**Examples:**

```bash

neuro pull image:myimage
neuro pull image://myfriend/alpine:shared
neuro pull image://username/my-alpine:production alpine:from-registry

```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _-q, --quiet_ | Run command in quiet mode \(DEPRECATED\) |

#### neuro image rm

Remove image from platform registry.

Image name must be URL with image:// scheme. Image name must contain tag.

**Usage:**

```bash
neuro image rm [OPTIONS] IMAGE
```

**Examples:**

```bash

neuro image rm image://myfriend/alpine:shared
neuro image rm image:myimage:latest

```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _-f_ | Force deletion of all tags referencing the image. |

#### neuro image size

Get image size

Image name must be URL with image:// scheme. Image name must contain tag.

**Usage:**

```bash
neuro image size [OPTIONS] IMAGE
```

**Examples:**

```bash

neuro image size image://myfriend/alpine:shared
neuro image size image:myimage:latest

```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

#### neuro image digest

Get digest of an image from remote registry

Image name must be URL with image:// scheme. Image name must contain tag.

**Usage:**

```bash
neuro image digest [OPTIONS] IMAGE
```

**Examples:**

```bash

neuro image digest image://myfriend/alpine:shared
neuro image digest image:myimage:latest

```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

#### neuro image tags

List tags for image in platform registry.

Image name must be URL with image:// scheme.

**Usage:**

```bash
neuro image tags [OPTIONS] IMAGE
```

**Examples:**

```bash

neuro image tags image://myfriend/alpine
neuro image tags -l image:myimage

```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _-l_ | List in long format, with image sizes. |

### neuro config

Client configuration.

**Usage:**

```bash
neuro config [OPTIONS] COMMAND [ARGS]...
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

**Commands:**

| Usage | Description |
| :--- | :--- |
| [_neuro config login_](CLI.md#neuro-config-login) | Log into Neuro Platform |
| [_neuro config login-with-token_](CLI.md#neuro-config-login-with-token) | Log into Neuro Platform with token |
| [_neuro config login-headless_](CLI.md#neuro-config-login-headless) | Log into Neuro Platform from non-GUI server environment |
| [_neuro config show_](CLI.md#neuro-config-show) | Print current settings |
| [_neuro config show-token_](CLI.md#neuro-config-show-token) | Print current authorization token |
| [_neuro config show-quota_](CLI.md#neuro-config-show-quota) | Print quota and remaining computation time for active cluster |
| [_neuro config aliases_](CLI.md#neuro-config-aliases) | List available command aliases |
| [_neuro config get-clusters_](CLI.md#neuro-config-get-clusters) | Fetch and display the list of available clusters |
| [_neuro config switch-cluster_](CLI.md#neuro-config-switch-cluster) | Switch the active cluster |
| [_neuro config docker_](CLI.md#neuro-config-docker) | Configure docker client to fit the Neuro Platform |
| [_neuro config logout_](CLI.md#neuro-config-logout) | Log out |

#### neuro config login

Log into Neuro Platform.

URL is a platform entrypoint URL.

**Usage:**

```bash
neuro config login [OPTIONS] [URL]
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

#### neuro config login-with-token

Log into Neuro Platform with token.

TOKEN is authentication token provided by administration team. URL is a platform entrypoint URL.

**Usage:**

```bash
neuro config login-with-token [OPTIONS] TOKEN [URL]
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

#### neuro config login-headless

Log into Neuro Platform from non-GUI server environment.

URL is a platform entrypoint URL.

The command works similar to "neuro login" but instead of opening a browser for performing OAuth registration prints an URL that should be open on guest host.

Then user inputs a code displayed in a browser after successful login back in neuro command to finish the login process.

**Usage:**

```bash
neuro config login-headless [OPTIONS] [URL]
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

#### neuro config show

Print current settings.

**Usage:**

```bash
neuro config show [OPTIONS]
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

#### neuro config show-token

Print current authorization token.

**Usage:**

```bash
neuro config show-token [OPTIONS]
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

#### neuro config show-quota

Print quota and remaining computation time for active cluster.

**Usage:**

```bash
neuro config show-quota [OPTIONS] [USER]
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

#### neuro config aliases

List available command aliases.

**Usage:**

```bash
neuro config aliases [OPTIONS]
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

#### neuro config get-clusters

Fetch and display the list of available clusters.

**Usage:**

```bash
neuro config get-clusters [OPTIONS]
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

#### neuro config switch-cluster

Switch the active cluster.

CLUSTER_NAME is the cluster name to select.  The interactive prompt is used if the name is omitted (default).

**Usage:**

```bash
neuro config switch-cluster [OPTIONS] [CLUSTER_NAME]
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

#### neuro config docker

Configure docker client to fit the Neuro Platform.

**Usage:**

```bash
neuro config docker [OPTIONS]
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--docker-config PATH_ | Specifies the location of the Docker client configuration files |

#### neuro config logout

Log out.

**Usage:**

```bash
neuro config logout [OPTIONS]
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

### neuro completion

Output shell completion code.

**Usage:**

```bash
neuro completion [OPTIONS] COMMAND [ARGS]...
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

**Commands:**

| Usage | Description |
| :--- | :--- |
| [_neuro completion generate_](CLI.md#neuro-completion-generate) | Provide an instruction for shell completion generation |
| [_neuro completion patch_](CLI.md#neuro-completion-patch) | Automatically patch shell configuration profile to enable completion |

#### neuro completion generate

Provide an instruction for shell completion generation.

**Usage:**

```bash
neuro completion generate [OPTIONS] [bash|zsh]
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

#### neuro completion patch

Automatically patch shell configuration profile to enable completion

**Usage:**

```bash
neuro completion patch [OPTIONS] [bash|zsh]
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

### neuro acl

Access Control List management.

**Usage:**

```bash
neuro acl [OPTIONS] COMMAND [ARGS]...
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

**Commands:**

| Usage | Description |
| :--- | :--- |
| [_neuro acl grant_](CLI.md#neuro-acl-grant) | Shares resource with another user |
| [_neuro acl revoke_](CLI.md#neuro-acl-revoke) | Revoke user access from another user |
| [_neuro acl list_](CLI.md#neuro-acl-list) | List shared resources |
| [_neuro acl add-role_](CLI.md#neuro-acl-add-role) | Add new role |
| [_neuro acl remove-role_](CLI.md#neuro-acl-remove-role) | Remove existing role |

#### neuro acl grant

Shares resource with another user.

URI shared resource.

USER username to share resource with.

PERMISSION sharing access right: read, write, or manage.

**Usage:**

```bash
neuro acl grant [OPTIONS] URI USER [read|write|manage]
```

**Examples:**

```bash

neuro acl grant storage:///sample_data/ alice manage
neuro acl grant image:resnet50 bob read
neuro acl grant job:///my_job_id alice write

```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

#### neuro acl revoke

Revoke user access from another user.

URI previously shared resource to revoke.

USER to revoke URI resource from.

**Usage:**

```bash
neuro acl revoke [OPTIONS] URI USER
```

**Examples:**

```bash

neuro acl revoke storage:///sample_data/ alice
neuro acl revoke image:resnet50 bob
neuro acl revoke job:///my_job_id alice

```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

#### neuro acl list

List shared resources.

The command displays a list of resources shared BY current user (default).

To display a list of resources shared WITH current user apply --shared option.

**Usage:**

```bash
neuro acl list [OPTIONS] [URI]
```

**Examples:**

```bash

neuro acl list
neuro acl list storage://
neuro acl list --shared
neuro acl list --shared image://

```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--full-uri_ | Output full URI. |
| _-s, --scheme TEXT_ | Filter resources by scheme, e.g. job, storage, image or user. Deprecated, use the uri argument instead. |
| _--shared_ | Output the resources shared by the user. |
| _-u TEXT_ | Use specified user or role. |

#### neuro acl add-role

Add new role.

**Usage:**

```bash
neuro acl add-role [OPTIONS] ROLE_NAME
```

**Examples:**

```bash

neuro acl add-role mycompany/subdivision

```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

#### neuro acl remove-role

Remove existing role.

**Usage:**

```bash
neuro acl remove-role [OPTIONS] ROLE_NAME
```

**Examples:**

```bash

neuro acl remove-role mycompany/subdivision

```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

### neuro blob

Blob storage operations.

**Usage:**

```bash
neuro blob [OPTIONS] COMMAND [ARGS]...
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

**Commands:**

| Usage | Description |
| :--- | :--- |
| [_neuro blob cp_](CLI.md#neuro-blob-cp) | Simple utility to copy files and directories into and from Blob Storage |
| [_neuro blob ls_](CLI.md#neuro-blob-ls) | List buckets or bucket contents |
| [_neuro blob glob_](CLI.md#neuro-blob-glob) | List resources that match PATTERNS |

#### neuro blob cp

Simple utility to copy files and directories into and from Blob Storage.

Either SOURCES or DESTINATION should have `blob://` scheme. If scheme is omitted, file:// scheme is assumed. It is currently not possible to copy files between Blob Storage (`blob://`) destination, nor with `storage://` scheme paths.

Use `/dev/stdin` and `/dev/stdout` file names to upload a file from standard input or output to stdout.

Any number of --exclude and --include options can be passed.  The filters that appear later in the command take precedence over filters that appear earlier in the command.  If neither --exclude nor --include options are specified the default can be changed using the storage.cp-exclude configuration variable documented in "neuro help user-config".

File permissions, modification times and other attributes will not be passed to Blob Storage metadata during upload.

**Usage:**

```bash
neuro blob cp [OPTIONS] [SOURCES]... [DESTINATION]
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--continue_ | Continue copying partially-copied files. Only for copying from Blob Storage. |
| _--exclude-from-files FILES_ | A list of file names that contain patterns for exclusion files and directories. Used only for uploading. The default can be changed using the storage.cp-exclude-from-files configuration variable documented in "neuro help user-config" |
| _--exclude_ | Exclude files and directories that match the specified pattern. |
| _--include_ | Don't exclude files and directories that match the specified pattern. |
| _--glob / --no-glob_ | Expand glob patterns in SOURCES with explicit scheme.  \[default: True\] |
| _-T, --no-target-directory_ | Treat DESTINATION as a normal file. |
| _-p, --progress / -P, --no-progress_ | Show progress, on by default. |
| _-r, --recursive_ | Recursive copy, off by default |
| _-t, --target-directory DIRECTORY_ | Copy all SOURCES into DIRECTORY. |
| _-u, --update_ | Copy only when the SOURCE file is newer than the destination file or when the destination file is missing. |

#### neuro blob ls

List buckets or bucket contents.

**Usage:**

```bash
neuro blob ls [OPTIONS] [PATHS]...
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _-l_ | use a long listing format. |
| _-h, --human-readable_ | with -l print human readable sizes \(e.g., 2K, 540M\). |
| _-r, --recursive_ | List all keys under the URL path provided, not just 1 level depths. |
| _--sort \[name &#124; size &#124; time\]_ | sort by given field, default is name. |

#### neuro blob glob

List resources that match PATTERNS.

**Usage:**

```bash
neuro blob glob [OPTIONS] [PATTERNS]...
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

### neuro secret

Operations with secrets.

**Usage:**

```bash
neuro secret [OPTIONS] COMMAND [ARGS]...
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

**Commands:**

| Usage | Description |
| :--- | :--- |
| [_neuro secret ls_](CLI.md#neuro-secret-ls) | List secrets |
| [_neuro secret add_](CLI.md#neuro-secret-add) | Add secret KEY with data VALUE |
| [_neuro secret rm_](CLI.md#neuro-secret-rm) | Remove secret KEY |

#### neuro secret ls

List secrets.

**Usage:**

```bash
neuro secret ls [OPTIONS]
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

#### neuro secret add

Add secret KEY with data VALUE.

If VALUE starts with @ it points to a file with secrets content.

**Usage:**

```bash
neuro secret add [OPTIONS] KEY VALUE
```

**Examples:**

```bash

neuro secret add KEY_NAME VALUE
neuro secret add KEY_NAME @path/to/file.txt

```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

#### neuro secret rm

Remove secret KEY.

**Usage:**

```bash
neuro secret rm [OPTIONS] KEY
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

### neuro disk

Operations with disks.

**Usage:**

```bash
neuro disk [OPTIONS] COMMAND [ARGS]...
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

**Commands:**

| Usage | Description |
| :--- | :--- |
| [_neuro disk ls_](CLI.md#neuro-disk-ls) | List disks |
| [_neuro disk create_](CLI.md#neuro-disk-create) | Create a disk with at least storage amount STORAGE |
| [_neuro disk get_](CLI.md#neuro-disk-get) | Get disk DISK\_ID |
| [_neuro disk rm_](CLI.md#neuro-disk-rm) | Remove disk DISK\_ID |

#### neuro disk ls

List disks.

**Usage:**

```bash
neuro disk ls [OPTIONS]
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--full-uri_ | Output full disk URI. |
| _--long-format_ | Output all info about disk. |

#### neuro disk create

Create a disk with at least storage amount STORAGE.

To specify the amount, you can use the following suffixes: "kKMGTPEZY" To use decimal quantities, append "b" or "B". For example: - 1K or 1k is 1024 bytes - 1Kb or 1KB is 1000 bytes - 20G is 20 * 2 ^ 30 bytes - 20Gb or 20GB is 20.000.000.000 bytes

Note that server can have big granularity (for example, 1G) so it will possibly round-up the amount you requested.

**Usage:**

```bash
neuro disk create [OPTIONS] STORAGE
```

**Examples:**

```bash

neuro disk create 10G
neuro disk create 500M

```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--life-span TIMEDELTA_ | Optional disk lifetime limit after last usage in the format '1d2h3m4s' \(some parts may be missing\). Set '0' to disable. Default value '1d' can be changed in the user config. |

#### neuro disk get

Get disk DISK_ID.

**Usage:**

```bash
neuro disk get [OPTIONS] DISK_ID
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--full-uri_ | Output full disk URI. |

#### neuro disk rm

Remove disk DISK_ID.

**Usage:**

```bash
neuro disk rm [OPTIONS] DISK_IDS...
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

### neuro help

Get help on a command.

**Usage:**

```bash
neuro help [OPTIONS] [COMMAND]...
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

### neuro run

Run a job with predefined resources configuration.

IMAGE docker image name to run in a job.

CMD list will be passed as arguments to the executed job's image.

**Usage:**

```bash
neuro run [OPTIONS] IMAGE [CMD]...
```

**Examples:**

```bash

# Starts a container pytorch:latest on a machine with smaller GPU resources
# (see exact values in `neuro config show`) and with two volumes mounted:
#   storage:/<home-directory>   --> /var/storage/home (in read-write mode),
#   storage:/neuromation/public --> /var/storage/neuromation (in read-only mode).
neuro run --preset=gpu-small --volume=storage::/var/storage/home:rw \
--volume=storage:/neuromation/public:/var/storage/home:ro pytorch:latest

# Starts a container using the custom image my-ubuntu:latest stored in neuro
# registry, run /script.sh and pass arg1 and arg2 as its arguments:
neuro run -s cpu-small image:my-ubuntu:latest --entrypoint=/script.sh arg1 arg2

```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--browse_ | Open a job's URL in a web browser |
| _-d, --description DESC_ | Optional job description in free format |
| _--detach_ | Don't attach to job logs and don't wait for exit code |
| _--entrypoint TEXT_ | Executable entrypoint in the container \(note that it overwrites `ENTRYPOINT` and `CMD` instructions of the docker image\) |
| _-e, --env VAR=VAL_ | Set environment variable in container. Use multiple options to define more than one variable. See `neuro help secrets` for information about passing secrets as environment variables. |
| _--env-file PATH_ | File with environment variables to pass |
| _-x, --extshm / -X, --no-extshm_ | Request extended '/dev/shm' space  \[default: True\] |
| _--http PORT_ | Enable HTTP port forwarding to container  \[default: 80\] |
| _--http-auth / --no-http-auth_ | Enable HTTP authentication for forwarded HTTP port  \[default: True\] |
| _--life-span TIMEDELTA_ | Optional job run-time limit in the format '1d2h3m4s' \(some parts may be missing\). Set '0' to disable. Default value '1d' can be changed in the user config. |
| _-n, --name NAME_ | Optional job name |
| _--pass-config / --no-pass-config_ | Upload neuro config to the job  \[default: False\] |
| _--port-forward LOCAL\_PORT:REMOTE\_RORT_ | Forward port\(s\) of a running job to local port\(s\) \(use multiple times for forwarding several ports\) |
| _-s, --preset PRESET_ | Predefined resource configuration \(to see available values, run `neuro config show`\) |
| _--privileged TEXT_ | Run job in privileged mode, if it is supported by cluster.  \[default: False\] |
| _-q, --quiet_ | Run command in quiet mode \(DEPRECATED\) |
| _--restart \[never &#124; on-failure &#124; always\]_ | Restart policy to apply when a job exits  \[default: never\] |
| _--schedule-timeout TIMEDELTA_ | Optional job schedule timeout in the format '3m4s' \(some parts may be missing\). |
| _--tag TAG_ | Optional job tag, multiple values allowed |
| _-t, --tty / -T, --no-tty_ | Allocate a TTY, can be useful for interactive jobs. By default is on if the command is executed from a terminal, non-tty mode is used if executed from a script. |
| _-v, --volume MOUNT_ | Mounts directory from vault into container. Use multiple options to mount more than one volume. See `neuro help secrets` for information about passing secrets as mounted files. |
| _--wait-for-seat / --no-wait-for-seat_ | Wait for total running jobs quota  \[default: False\] |
| _--wait-start / --no-wait-start_ | Wait for a job start or failure  \[default: True\] |
| _-w, --workdir TEXT_ | Working directory inside the container |

### neuro ps

List all jobs.

**Usage:**

```bash
neuro ps [OPTIONS]
```

**Examples:**

```bash

neuro ps -a
neuro ps -a --owner=user-1 --owner=user-2
neuro ps --name my-experiments-v1 -s failed -s succeeded
neuro ps --description=my favourite job
neuro ps -s failed -s succeeded -q
neuro ps -t tag1 -t tag2

```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _-a, --all_ | Show all jobs regardless the status. |
| _-d, --description DESCRIPTION_ | Filter out jobs by description \(exact match\). |
| _--format COLUMNS_ | Output table format, see "neuro help ps-format" for more info about the format specification. The default can be changed using the job.ps-format configuration variable documented in "neuro help user-config" |
| _--full-uri_ | Output full image URI. |
| _-n, --name NAME_ | Filter out jobs by name. |
| _-o, --owner TEXT_ | Filter out jobs by owner \(multiple option\). Supports `ME` option to filter by the current user. |
| _-q, --quiet_ | Run command in quiet mode \(DEPRECATED\) |
| _--since DATE_ | Show jobs created after a specific date \(including\). |
| _-s, --status \[pending &#124; suspended &#124; running &#124; succeeded &#124; failed &#124; cancelled\]_ | Filter out jobs by status \(multiple option\). |
| _-t, --tag TAG_ | Filter out jobs by tag \(multiple option\) |
| _--until DATE_ | Show jobs created before a specific date \(including\). |
| _-w, --wide_ | Do not cut long lines for terminal width. |

### neuro status

Display status of a job.

**Usage:**

```bash
neuro status [OPTIONS] JOB
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--full-uri_ | Output full URI. |

### neuro exec

Execute command in a running job.

**Usage:**

```bash
neuro exec [OPTIONS] JOB CMD...
```

**Examples:**

```bash

# Provides a shell to the container:
neuro exec my-job /bin/bash

# Executes a single command in the container and returns the control:
neuro exec --no-tty my-job ls -l

```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _-t, --tty / -T, --no-tty_ | Allocate a TTY, can be useful for interactive jobs. By default is on if the command is executed from a terminal, non-tty mode is used if executed from a script. |

### neuro port-forward

Forward port(s) of a running job to local port(s).

**Usage:**

```bash
neuro port-forward [OPTIONS] JOB LOCAL_PORT:REMOTE_RORT...
```

**Examples:**

```bash

# Forward local port 2080 to port 80 of job's container.
# You can use http://localhost:2080 in browser to access job's served http
neuro job port-forward my-fastai-job 2080:80

# Forward local port 2222 to job's port 22
# Then copy all data from container's folder '/data' to current folder
# (please run second command in other terminal)
neuro job port-forward my-job-with-ssh-server 2222:22
rsync -avxzhe ssh -p 2222 root@localhost:/data .

# Forward few ports at once
neuro job port-forward my-job 2080:80 2222:22 2000:100

```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

### neuro attach

Attach local standard input, output, and error streams to a running job.

**Usage:**

```bash
neuro attach [OPTIONS] JOB
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--port-forward LOCAL\_PORT:REMOTE\_RORT_ | Forward port\(s\) of a running job to local port\(s\) \(use multiple times for forwarding several ports\) |

### neuro logs

Print the logs for a job.

**Usage:**

```bash
neuro logs [OPTIONS] JOB
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

### neuro kill

Kill job(s).

**Usage:**

```bash
neuro kill [OPTIONS] JOBS...
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

### neuro top

Display GPU/CPU/Memory usage.

**Usage:**

```bash
neuro top [OPTIONS] JOB
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--timeout FLOAT_ | Maximum allowed time for executing the command, 0 for no timeout  \[default: 0\] |

### neuro save

Save job's state to an image.

**Usage:**

```bash
neuro save [OPTIONS] JOB IMAGE
```

**Examples:**

```bash

neuro job save job-id image:ubuntu-patched
neuro job save my-favourite-job image:ubuntu-patched:v1
neuro job save my-favourite-job image://bob/ubuntu-patched

```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

### neuro login

Log into Neuro Platform.

URL is a platform entrypoint URL.

**Usage:**

```bash
neuro login [OPTIONS] [URL]
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

### neuro logout

Log out.

**Usage:**

```bash
neuro logout [OPTIONS]
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

### neuro cp

Copy files and directories.

Either SOURCES or DESTINATION should have storage:// scheme. If scheme is omitted, file:// scheme is assumed.

Use /dev/stdin and /dev/stdout file names to copy a file from terminal and print the content of file on the storage to console.

Any number of --exclude and --include options can be passed.  The filters that appear later in the command take precedence over filters that appear earlier in the command.  If neither --exclude nor --include options are specified the default can be changed using the storage.cp-exclude configuration variable documented in "neuro help user-config".

**Usage:**

```bash
neuro cp [OPTIONS] [SOURCES]... [DESTINATION]
```

**Examples:**

```bash

# copy local files into remote storage root
neuro cp foo.txt bar/baz.dat storage:
neuro cp foo.txt bar/baz.dat -t storage:

# copy local directory `foo` into existing remote directory `bar`
neuro cp -r foo -t storage:bar

# copy the content of local directory `foo` into existing remote
# directory `bar`
neuro cp -r -T storage:foo storage:bar

# download remote file `foo.txt` into local file `/tmp/foo.txt` with
# explicit file:// scheme set
neuro cp storage:foo.txt file:///tmp/foo.txt
neuro cp -T storage:foo.txt file:///tmp/foo.txt
neuro cp storage:foo.txt file:///tmp
neuro cp storage:foo.txt -t file:///tmp

# download other user's remote file into the current directory
neuro cp storage://{username}/foo.txt .

# download only files with extension `.out` into the current directory
neuro cp storage:results/*.out .

```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--continue_ | Continue copying partially-copied files. |
| _--exclude-from-files FILES_ | A list of file names that contain patterns for exclusion files and directories. Used only for uploading. The default can be changed using the storage.cp-exclude-from-files configuration variable documented in "neuro help user-config" |
| _--exclude_ | Exclude files and directories that match the specified pattern. |
| _--include_ | Don't exclude files and directories that match the specified pattern. |
| _--glob / --no-glob_ | Expand glob patterns in SOURCES with explicit scheme.  \[default: True\] |
| _-T, --no-target-directory_ | Treat DESTINATION as a normal file. |
| _-p, --progress / -P, --no-progress_ | Show progress, on by default in TTY mode, off otherwise. |
| _-r, --recursive_ | Recursive copy, off by default |
| _-t, --target-directory DIRECTORY_ | Copy all SOURCES into DIRECTORY. |
| _-u, --update_ | Copy only when the SOURCE file is newer than the destination file or when the destination file is missing. |

### neuro ls

List directory contents.

By default PATH is equal user's home dir (storage:)

**Usage:**

```bash
neuro ls [OPTIONS] [PATHS]...
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _-d, --directory_ | list directories themselves, not their contents. |
| _-l_ | use a long listing format. |
| _-h, --human-readable_ | with -l print human readable sizes \(e.g., 2K, 540M\). |
| _-a, --all_ | do not ignore entries starting with . |
| _--sort \[name &#124; size &#124; time\]_ | sort by given field, default is name. |

### neuro rm

Remove files or directories.

**Usage:**

```bash
neuro rm [OPTIONS] PATHS...
```

**Examples:**

```bash

neuro rm storage:foo/bar
neuro rm storage://{username}/foo/bar
neuro rm --recursive storage://{username}/foo/
neuro rm storage:foo/**/*.tmp

```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--glob / --no-glob_ | Expand glob patterns in PATHS  \[default: True\] |
| _-p, --progress / -P, --no-progress_ | Show progress, on by default in TTY mode, off otherwise. |
| _-r, --recursive_ | remove directories and their contents recursively |

### neuro mkdir

Make directories.

**Usage:**

```bash
neuro mkdir [OPTIONS] PATHS...
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _-p, --parents_ | No error if existing, make parent directories as needed |

### neuro mv

Move or rename files and directories.

SOURCE must contain path to the file or directory existing on the storage, and DESTINATION must contain the full path to the target file or directory.

**Usage:**

```bash
neuro mv [OPTIONS] [SOURCES]... [DESTINATION]
```

**Examples:**

```bash

# move and rename remote file
neuro mv storage:foo.txt storage:bar/baz.dat
neuro mv -T storage:foo.txt storage:bar/baz.dat

# move remote files into existing remote directory
neuro mv storage:foo.txt storage:bar/baz.dat storage:dst
neuro mv storage:foo.txt storage:bar/baz.dat -t storage:dst

# move the content of remote directory into other existing
# remote directory
neuro mv -T storage:foo storage:bar

# move remote file into other user's directory
neuro mv storage:foo.txt storage://{username}/bar.dat

# move remote file from other user's directory
neuro mv storage://{username}/foo.txt storage:bar.dat

```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--glob / --no-glob_ | Expand glob patterns in SOURCES  \[default: True\] |
| _-T, --no-target-directory_ | Treat DESTINATION as a normal file |
| _-t, --target-directory DIRECTORY_ | Copy all SOURCES into DIRECTORY |

### neuro images

List images.

**Usage:**

```bash
neuro images [OPTIONS]
```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _-l_ | List in long format. |
| _--full-uri_ | Output full image URI. |

### neuro push

Push an image to platform registry.

Remote image must be URL with image:// scheme. Image names can contain tag. If tags not specified 'latest' will be used as value.

**Usage:**

```bash
neuro push [OPTIONS] LOCAL_IMAGE [REMOTE_IMAGE]
```

**Examples:**

```bash

neuro push myimage
neuro push alpine:latest image:my-alpine:production
neuro push alpine image://myfriend/alpine:shared

```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _-q, --quiet_ | Run command in quiet mode \(DEPRECATED\) |

### neuro pull

Pull an image from platform registry.

Remote image name must be URL with image:// scheme. Image names can contain tag.

**Usage:**

```bash
neuro pull [OPTIONS] REMOTE_IMAGE [LOCAL_IMAGE]
```

**Examples:**

```bash

neuro pull image:myimage
neuro pull image://myfriend/alpine:shared
neuro pull image://username/my-alpine:production alpine:from-registry

```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _-q, --quiet_ | Run command in quiet mode \(DEPRECATED\) |

### neuro share

Shares resource with another user.

URI shared resource.

USER username to share resource with.

PERMISSION sharing access right: read, write, or manage.

**Usage:**

```bash
neuro share [OPTIONS] URI USER [read|write|manage]
```

**Examples:**

```bash

neuro acl grant storage:///sample_data/ alice manage
neuro acl grant image:resnet50 bob read
neuro acl grant job:///my_job_id alice write

```

**Options:**

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |



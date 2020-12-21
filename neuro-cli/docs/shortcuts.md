# Shortcuts

## Commands

* [neuro run](shortcuts.md#run): Run a job with predefined resources...
* [neuro ps](shortcuts.md#ps): List all jobs
* [neuro status](shortcuts.md#status): Display status of a job
* [neuro exec](shortcuts.md#exec): Execute command in a running job
* [neuro port-forward](shortcuts.md#port-forward): Forward port(s) of a running job to local...
* [neuro attach](shortcuts.md#attach): Attach local standard input, output, and...
* [neuro logs](shortcuts.md#logs): Print the logs for a job
* [neuro kill](shortcuts.md#kill): Kill job(s)
* [neuro top](shortcuts.md#top): Display GPU/CPU/Memory usage
* [neuro save](shortcuts.md#save): Save job's state to an image
* [neuro login](shortcuts.md#login): Log into Neuro Platform
* [neuro logout](shortcuts.md#logout): Log out
* [neuro cp](shortcuts.md#cp): Copy files and directories
* [neuro ls](shortcuts.md#ls): List directory contents
* [neuro rm](shortcuts.md#rm): Remove files or directories
* [neuro mkdir](shortcuts.md#mkdir): Make directories
* [neuro mv](shortcuts.md#mv): Move or rename files and directories
* [neuro images](shortcuts.md#images): List images
* [neuro push](shortcuts.md#push): Push an image to platform registry
* [neuro pull](shortcuts.md#pull): Pull an image from platform registry
* [neuro share](shortcuts.md#share): Shares resource with another user

### run

Run a job with predefined resources...

#### Usage

```bash
neuro run [OPTIONS] IMAGE [CMD]...
```

Run a job with predefined resources configuration.

`IMAGE` docker image name
to run in a job.

`CMD` list will be passed as arguments to the executed job's
image.

#### Examples

```bash

# Starts a container pytorch:latest on a machine with smaller GPU resources
# (see exact values in `neuro config show`) and with two volumes mounted:
#   storage:/<home-directory>   --> /var/storage/home (in read-write mode),
#   storage:/neuromation/public --> /var/storage/neuromation (in read-only mode).
$ neuro run --preset=gpu-small --volume=storage::/var/storage/home:rw \
$ --volume=storage:/neuromation/public:/var/storage/home:ro pytorch:latest

# Starts a container using the custom image my-ubuntu:latest stored in neuro
# registry, run /script.sh and pass arg1 and arg2 as its arguments:
$ neuro run -s cpu-small image:my-ubuntu:latest --entrypoint=/script.sh arg1 arg2
```

#### Options

| Name                                     | Description                                                                                                                                                                            |
| ---------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--help`                                 | Show this message and exit.                                                                                                                                                            |
| `--browse`                               | Open a job's URL in a web browser                                                                                                                                                      |
| `-d`, `--description DESC`               | Optional job description in free format                                                                                                                                                |
| `--detach`                               | Don't attach to job logs and don't wait for exit code                                                                                                                                  |
| `--entrypoint TEXT`                      | Executable entrypoint in the container (note that it overwrites `ENTRYPOINT` and `CMD` instructions of the docker image)                                                               |
| `-e`, `--env VAR=VAL`                    | Set environment variable in container. Use multiple options to define more than one variable. See `neuro help secrets` for information about passing secrets as environment variables. |
| `--env-file PATH`                        | File with environment variables to pass                                                                                                                                                |
| `-x`, `--extshm` / `-X`, `--no-extshm`   | Request extended '/dev/shm' space  _[default: True]_                                                                                                                                   |
| `--http PORT`                            | Enable HTTP port forwarding to container  _[default: 80]_                                                                                                                              |
| `--http-auth` / `--no-http-auth`         | Enable HTTP authentication for forwarded HTTP port  _[default: True]_                                                                                                                  |
| `--life-span TIMEDELTA`                  | Optional job run-time limit in the format '1d2h3m4s' (some parts may be missing). Set '0' to disable. Default value '1d' can be changed in the user config.                            |
| `-n`, `--name NAME`                      | Optional job name                                                                                                                                                                      |
| `--pass-config` / `--no-pass-config`     | Upload neuro config to the job  _[default: False]_                                                                                                                                     |
| `--port-forward LOCAL_PORT:REMOTE_RORT`  | Forward port(s) of a running job to local port(s) (use multiple times for forwarding several ports)                                                                                    |
| `-s`, `--preset PRESET`                  | Predefined resource configuration (to see available values, run `neuro config show`)                                                                                                   |
| `--privileged TEXT`                      | Run job in privileged mode, if it is supported by cluster.  _[default: False]_                                                                                                         |
| `-q`, `--quiet`                          | Run command in quiet mode (DEPRECATED)                                                                                                                                                 |
| `--restart [never|on-failure|always]`    | Restart policy to apply when a job exits  _[default: never]_                                                                                                                           |
| `--schedule-timeout TIMEDELTA`           | Optional job schedule timeout in the format '3m4s' (some parts may be missing).                                                                                                        |
| `--tag TAG`                              | Optional job tag, multiple values allowed                                                                                                                                              |
| `-t`, `--tty` / `-T`, `--no-tty`         | Allocate a TTY, can be useful for interactive jobs. By default is on if the command is executed from a terminal, non-tty mode is used if executed from a script.                       |
| `-v`, `--volume MOUNT`                   | Mounts directory from vault into container. Use multiple options to mount more than one volume. See `neuro help secrets` for information about passing secrets as mounted files.       |
| `--wait-for-seat` / `--no-wait-for-seat` | Wait for total running jobs quota  _[default: False]_                                                                                                                                  |
| `--wait-start` / `--no-wait-start`       | Wait for a job start or failure  _[default: True]_                                                                                                                                     |
| `-w`, `--workdir TEXT`                   | Working directory inside the container                                                                                                                                                 |

### ps

List all jobs

#### Usage

```bash
neuro ps [OPTIONS]
```

List all jobs.

#### Examples

```bash

$ neuro ps -a
$ neuro ps -a --owner=user-1 --owner=user-2
$ neuro ps --name my-experiments-v1 -s failed -s succeeded
$ neuro ps --description=my favourite job
$ neuro ps -s failed -s succeeded -q
$ neuro ps -t tag1 -t tag2
```

#### Options

| Name                                                                    | Description                                                                                                                                                                                                    |
| ----------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--help`                                                                | Show this message and exit.                                                                                                                                                                                    |
| `-a`, `--all`                                                           | Show all jobs regardless the status.                                                                                                                                                                           |
| `-d`, `--description DESCRIPTION`                                       | Filter out jobs by description (exact match).                                                                                                                                                                  |
| `--format COLUMNS`                                                      | Output table format, see "neuro help ps-format" for more info about the format specification. The default can be changed using the job.ps-format configuration variable documented in "neuro help user-config" |
| `--full-uri`                                                            | Output full image URI.                                                                                                                                                                                         |
| `-n`, `--name NAME`                                                     | Filter out jobs by name.                                                                                                                                                                                       |
| `-o`, `--owner TEXT`                                                    | Filter out jobs by owner (multiple option). Supports `ME` option to filter by the current user.                                                                                                                |
| `-q`, `--quiet`                                                         | Run command in quiet mode (DEPRECATED)                                                                                                                                                                         |
| `--since DATE`                                                          | Show jobs created after a specific date (including).                                                                                                                                                           |
| `-s`, `--status [pending|suspended|running|succeeded|failed|cancelled]` | Filter out jobs by status (multiple option).                                                                                                                                                                   |
| `-t`, `--tag TAG`                                                       | Filter out jobs by tag (multiple option)                                                                                                                                                                       |
| `--until DATE`                                                          | Show jobs created before a specific date (including).                                                                                                                                                          |
| `-w`, `--wide`                                                          | Do not cut long lines for terminal width.                                                                                                                                                                      |

### status

Display status of a job

#### Usage

```bash
neuro status [OPTIONS] JOB
```

Display status of a job.

#### Options

| Name         | Description                 |
| ------------ | --------------------------- |
| `--help`     | Show this message and exit. |
| `--full-uri` | Output full URI.            |

### exec

Execute command in a running job

#### Usage

```bash
neuro exec [OPTIONS] JOB CMD...
```

Execute command in a running job.

#### Examples

```bash

# Provides a shell to the container:
$ neuro exec my-job /bin/bash

# Executes a single command in the container and returns the control:
$ neuro exec --no-tty my-job ls -l
```

#### Options

| Name                             | Description                                                                                                                                                      |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--help`                         | Show this message and exit.                                                                                                                                      |
| `-t`, `--tty` / `-T`, `--no-tty` | Allocate a TTY, can be useful for interactive jobs. By default is on if the command is executed from a terminal, non-tty mode is used if executed from a script. |

### port-forward

Forward port(s) of a running job to local...

#### Usage

```bash
neuro port-forward [OPTIONS] JOB LOCAL_PORT:REMOTE_RORT...
```

Forward port(s) of a running job to local port(s).

#### Examples

```bash

# Forward local port 2080 to port 80 of job's container.
# You can use http://localhost:2080 in browser to access job's served http
$ neuro job port-forward my-fastai-job 2080:80

# Forward local port 2222 to job's port 22
# Then copy all data from container's folder '/data' to current folder
# (please run second command in other terminal)
$ neuro job port-forward my-job-with-ssh-server 2222:22
$ rsync -avxzhe ssh -p 2222 root@localhost:/data .

# Forward few ports at once
$ neuro job port-forward my-job 2080:80 2222:22 2000:100
```

#### Options

| Name     | Description                 |
| -------- | --------------------------- |
| `--help` | Show this message and exit. |

### attach

Attach local standard input, output, and...

#### Usage

```bash
neuro attach [OPTIONS] JOB
```

Attach local standard input, output, and error streams to a running job.

#### Options

| Name                                    | Description                                                                                         |
| --------------------------------------- | --------------------------------------------------------------------------------------------------- |
| `--help`                                | Show this message and exit.                                                                         |
| `--port-forward LOCAL_PORT:REMOTE_RORT` | Forward port(s) of a running job to local port(s) (use multiple times for forwarding several ports) |

### logs

Print the logs for a job

#### Usage

```bash
neuro logs [OPTIONS] JOB
```

Print the logs for a job.

#### Options

| Name     | Description                 |
| -------- | --------------------------- |
| `--help` | Show this message and exit. |

### kill

Kill job(s)

#### Usage

```bash
neuro kill [OPTIONS] JOBS...
```

Kill job(s).

#### Options

| Name     | Description                 |
| -------- | --------------------------- |
| `--help` | Show this message and exit. |

### top

Display GPU/CPU/Memory usage

#### Usage

```bash
neuro top [OPTIONS] JOB
```

Display `GPU`/`CPU`/Memory usage.

#### Options

| Name              | Description                                                                      |
| ----------------- | -------------------------------------------------------------------------------- |
| `--help`          | Show this message and exit.                                                      |
| `--timeout FLOAT` | Maximum allowed time for executing the command, 0 for no timeout  _[default: 0]_ |

### save

Save job's state to an image

#### Usage

```bash
neuro save [OPTIONS] JOB IMAGE
```

Save job's state to an image.

#### Examples

```bash
$ neuro job save job-id image:ubuntu-patched
$ neuro job save my-favourite-job image:ubuntu-patched:v1
$ neuro job save my-favourite-job image://bob/ubuntu-patched
```

#### Options

| Name     | Description                 |
| -------- | --------------------------- |
| `--help` | Show this message and exit. |

### login

Log into Neuro Platform

#### Usage

```bash
neuro login [OPTIONS] [URL]
```

Log into Neuro Platform.

`URL` is a platform entrypoint `URL`.

#### Options

| Name     | Description                 |
| -------- | --------------------------- |
| `--help` | Show this message and exit. |

### logout

Log out

#### Usage

```bash
neuro logout [OPTIONS]
```

Log out.

#### Options

| Name     | Description                 |
| -------- | --------------------------- |
| `--help` | Show this message and exit. |

### cp

Copy files and directories

#### Usage

```bash
neuro cp [OPTIONS] [SOURCES]... [DESTINATION]
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
neuro ls [OPTIONS] [PATHS]...
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

### rm

Remove files or directories

#### Usage

```bash
neuro rm [OPTIONS] PATHS...
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
neuro mkdir [OPTIONS] PATHS...
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
neuro mv [OPTIONS] [SOURCES]... [DESTINATION]
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

### images

List images

#### Usage

```bash
neuro images [OPTIONS]
```

List images.

#### Options

| Name         | Description                 |
| ------------ | --------------------------- |
| `--help`     | Show this message and exit. |
| `-l`         | List in long format.        |
| `--full-uri` | Output full image URI.      |

### push

Push an image to platform registry

#### Usage

```bash
neuro push [OPTIONS] LOCAL_IMAGE [REMOTE_IMAGE]
```

Push an image to platform registry.

Remote image must be `URL` with image://
scheme.
Image names can contain tag. If tags not specified 'latest' will
be
used as value.

#### Examples

```bash

$ neuro push myimage
$ neuro push alpine:latest image:my-alpine:production
$ neuro push alpine image://myfriend/alpine:shared
```

#### Options

| Name            | Description                            |
| --------------- | -------------------------------------- |
| `--help`        | Show this message and exit.            |
| `-q`, `--quiet` | Run command in quiet mode (DEPRECATED) |

### pull

Pull an image from platform registry

#### Usage

```bash
neuro pull [OPTIONS] REMOTE_IMAGE [LOCAL_IMAGE]
```

Pull an image from platform registry.

Remote image name must be `URL` with
image:// scheme.
Image names can contain tag.

#### Examples

```bash

$ neuro pull image:myimage
$ neuro pull image://myfriend/alpine:shared
$ neuro pull image://username/my-alpine:production alpine:from-registry
```

#### Options

| Name            | Description                            |
| --------------- | -------------------------------------- |
| `--help`        | Show this message and exit.            |
| `-q`, `--quiet` | Run command in quiet mode (DEPRECATED) |

### share

Shares resource with another user

#### Usage

```bash
neuro share [OPTIONS] URI USER [read|write|manage]
```

Shares resource with another user.

`URI` shared resource.

`USER` username to
share resource with.

`PERMISSION` sharing access right: read, write, or
manage.

#### Examples

```bash
$ neuro acl grant storage:///sample_data/ alice manage
$ neuro acl grant image:resnet50 bob read
$ neuro acl grant job:///my_job_id alice write
```

#### Options

| Name     | Description                 |
| -------- | --------------------------- |
| `--help` | Show this message and exit. |

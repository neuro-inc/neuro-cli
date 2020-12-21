# job

Job operations

## Usage

```bash
neuro job [OPTIONS] COMMAND [ARGS]...
```

Job operations.

**Commands:**


| Usage | Description |

| :--- | :--- |

| [_run_](job.md#run) | Run a job with predefined resources... |

| [_ls_](job.md#ls) | List all jobs |

| [_status_](job.md#status) | Display status of a job |

| [_tags_](job.md#tags) | List all tags submitted by the user |

| [_exec_](job.md#exec) | Execute command in a running job |

| [_port-forward_](job.md#port-forward) | Forward port\(s\) of a running job to local... |

| [_logs_](job.md#logs) | Print the logs for a job |

| [_kill_](job.md#kill) | Kill job\(s\) |

| [_top_](job.md#top) | Display GPU/CPU/Memory usage |

| [_save_](job.md#save) | Save job's state to an image |

| [_browse_](job.md#browse) | Opens a job's URL in a web browser |

| [_attach_](job.md#attach) | Attach local standard input, output, and... |



### run



Run a job with predefined resources...



#### Usage

```bash
neuro job run [OPTIONS] IMAGE [CMD]...
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


| Name | Description |

| :--- | :--- |

| _`--help`_ | Show this message and exit. |

| _`--browse`_ | Open a job's URL in a web browser |

| _`-d`, `--description DESC`_ | Optional job description in free format |

| _`--detach`_ | Don't attach to job logs and don't wait for exit code |

| _`--entrypoint TEXT`_ | Executable entrypoint in the container \(note that it overwrites `ENTRYPOINT` and `CMD` instructions of the docker image\) |

| _`-e`, `--env VAR=VAL`_ | Set environment variable in container. Use multiple options to define more than one variable. See `neuro help secrets` for information about passing secrets as environment variables. |

| _`--env-file PATH`_ | File with environment variables to pass |

| _`-x`, `--extshm` / `-X`, `--no-extshm`_ | Request extended '/dev/shm' space  \_\[default: True\]\_ |

| _`--http PORT`_ | Enable HTTP port forwarding to container  \_\[default: 80\]\_ |

| _`--http-auth` / `--no-http-auth`_ | Enable HTTP authentication for forwarded HTTP port  \_\[default: True\]\_ |

| _`--life-span TIMEDELTA`_ | Optional job run-time limit in the format '1d2h3m4s' \(some parts may be missing\). Set '0' to disable. Default value '1d' can be changed in the user config. |

| _`-n`, `--name NAME`_ | Optional job name |

| _`--pass-config` / `--no-pass-config`_ | Upload neuro config to the job  \_\[default: False\]\_ |

| _`--port-forward LOCAL\_PORT:REMOTE\_RORT`_ | Forward port\(s\) of a running job to local port\(s\) \(use multiple times for forwarding several ports\) |

| _`-s`, `--preset PRESET`_ | Predefined resource configuration \(to see available values, run `neuro config show`\) |

| _`--privileged TEXT`_ | Run job in privileged mode, if it is supported by cluster.  \_\[default: False\]\_ |

| _`-q`, `--quiet`_ | Run command in quiet mode \(DEPRECATED\) |

| _`--restart \[never &#124; on-failure &#124; always\]`_ | Restart policy to apply when a job exits  \_\[default: never\]\_ |

| _`--schedule-timeout TIMEDELTA`_ | Optional job schedule timeout in the format '3m4s' \(some parts may be missing\). |

| _`--tag TAG`_ | Optional job tag, multiple values allowed |

| _`-t`, `--tty` / `-T`, `--no-tty`_ | Allocate a TTY, can be useful for interactive jobs. By default is on if the command is executed from a terminal, non-tty mode is used if executed from a script. |

| _`-v`, `--volume MOUNT`_ | Mounts directory from vault into container. Use multiple options to mount more than one volume. See `neuro help secrets` for information about passing secrets as mounted files. |

| _`--wait-for-seat` / `--no-wait-for-seat`_ | Wait for total running jobs quota  \_\[default: False\]\_ |

| _`--wait-start` / `--no-wait-start`_ | Wait for a job start or failure  \_\[default: True\]\_ |

| _`-w`, `--workdir TEXT`_ | Working directory inside the container |




### ls



List all jobs



#### Usage

```bash
neuro job ls [OPTIONS]
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


| Name | Description |

| :--- | :--- |

| _`--help`_ | Show this message and exit. |

| _`-a`, `--all`_ | Show all jobs regardless the status. |

| _`-d`, `--description DESCRIPTION`_ | Filter out jobs by description \(exact match\). |

| _`--format COLUMNS`_ | Output table format, see "neuro help ps-format" for more info about the format specification. The default can be changed using the job.ps-format configuration variable documented in "neuro help user-config" |

| _`--full-uri`_ | Output full image URI. |

| _`-n`, `--name NAME`_ | Filter out jobs by name. |

| _`-o`, `--owner TEXT`_ | Filter out jobs by owner \(multiple option\). Supports `ME` option to filter by the current user. |

| _`-q`, `--quiet`_ | Run command in quiet mode \(DEPRECATED\) |

| _`--since DATE`_ | Show jobs created after a specific date \(including\). |

| _`-s`, `--status \[pending &#124; suspended &#124; running &#124; succeeded &#124; failed &#124; cancelled\]`_ | Filter out jobs by status \(multiple option\). |

| _`-t`, `--tag TAG`_ | Filter out jobs by tag \(multiple option\) |

| _`--until DATE`_ | Show jobs created before a specific date \(including\). |

| _`-w`, `--wide`_ | Do not cut long lines for terminal width. |




### status



Display status of a job



#### Usage

```bash
neuro job status [OPTIONS] JOB
```

Display status of a job.

#### Options


| Name | Description |

| :--- | :--- |

| _`--help`_ | Show this message and exit. |

| _`--full-uri`_ | Output full URI. |




### tags



List all tags submitted by the user



#### Usage

```bash
neuro job tags [OPTIONS]
```

List all tags submitted by the user.

#### Options


| Name | Description |

| :--- | :--- |

| _`--help`_ | Show this message and exit. |




### exec



Execute command in a running job



#### Usage

```bash
neuro job exec [OPTIONS] JOB CMD...
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


| Name | Description |

| :--- | :--- |

| _`--help`_ | Show this message and exit. |

| _`-t`, `--tty` / `-T`, `--no-tty`_ | Allocate a TTY, can be useful for interactive jobs. By default is on if the command is executed from a terminal, non-tty mode is used if executed from a script. |




### port-forward



Forward port(s) of a running job to local...



#### Usage

```bash
neuro job port-forward [OPTIONS] JOB LOCAL_PORT:REMOTE_RORT...
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


| Name | Description |

| :--- | :--- |

| _`--help`_ | Show this message and exit. |




### logs



Print the logs for a job



#### Usage

```bash
neuro job logs [OPTIONS] JOB
```

Print the logs for a job.

#### Options


| Name | Description |

| :--- | :--- |

| _`--help`_ | Show this message and exit. |




### kill



Kill job(s)



#### Usage

```bash
neuro job kill [OPTIONS] JOBS...
```

Kill job(s).

#### Options


| Name | Description |

| :--- | :--- |

| _`--help`_ | Show this message and exit. |




### top



Display GPU/CPU/Memory usage



#### Usage

```bash
neuro job top [OPTIONS] JOB
```

Display `GPU`/`CPU`/Memory usage.

#### Options


| Name | Description |

| :--- | :--- |

| _`--help`_ | Show this message and exit. |

| _`--timeout FLOAT`_ | Maximum allowed time for executing the command, 0 for no timeout  \_\[default: 0\]\_ |




### save



Save job's state to an image



#### Usage

```bash
neuro job save [OPTIONS] JOB IMAGE
```

Save job's state to an image.

#### Examples

```bash
$ neuro job save job-id image:ubuntu-patched
$ neuro job save my-favourite-job image:ubuntu-patched:v1
$ neuro job save my-favourite-job image://bob/ubuntu-patched
```

#### Options


| Name | Description |

| :--- | :--- |

| _`--help`_ | Show this message and exit. |




### browse



Opens a job's URL in a web browser



#### Usage

```bash
neuro job browse [OPTIONS] JOB
```

Opens a job's `URL` in a web browser.

#### Options


| Name | Description |

| :--- | :--- |

| _`--help`_ | Show this message and exit. |




### attach



Attach local standard input, output, and...



#### Usage

```bash
neuro job attach [OPTIONS] JOB
```

Attach local standard input, output, and error streams to a running job.

#### Options


| Name | Description |

| :--- | :--- |

| _`--help`_ | Show this message and exit. |

| _`--port-forward LOCAL\_PORT:REMOTE\_RORT`_ | Forward port\(s\) of a running job to local port\(s\) \(use multiple times for forwarding several ports\) |




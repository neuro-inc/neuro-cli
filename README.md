[![codecov](https://codecov.io/gh/neuromation/platform-api-clients/branch/master/graph/badge.svg?token=FwM6ZV3gDj)](https://codecov.io/gh/neuromation/platform-api-clients)

# Table of Contents
* [Preface](#Preface)
* [neuro](#neuro)
	* [neuro admin](#neuro-admin)
		* [neuro admin get-clusters](#neuro-admin-get-clusters)
		* [neuro admin generate-cluster-config](#neuro-admin-generate-cluster-config)
		* [neuro admin add-cluster](#neuro-admin-add-cluster)
		* [neuro admin get-cluster-users](#neuro-admin-get-cluster-users)
		* [neuro admin add-cluster-user](#neuro-admin-add-cluster-user)
		* [neuro admin remove-cluster-user](#neuro-admin-remove-cluster-user)
		* [neuro admin set-user-quota](#neuro-admin-set-user-quota)
		* [neuro admin add-user-quota](#neuro-admin-add-user-quota)
	* [neuro job](#neuro-job)
		* [neuro job run](#neuro-job-run)
		* [neuro job submit](#neuro-job-submit)
		* [neuro job ls](#neuro-job-ls)
		* [neuro job status](#neuro-job-status)
		* [neuro job tags](#neuro-job-tags)
		* [neuro job exec](#neuro-job-exec)
		* [neuro job port-forward](#neuro-job-port-forward)
		* [neuro job logs](#neuro-job-logs)
		* [neuro job kill](#neuro-job-kill)
		* [neuro job top](#neuro-job-top)
		* [neuro job save](#neuro-job-save)
		* [neuro job browse](#neuro-job-browse)
	* [neuro project](#neuro-project)
		* [neuro project init](#neuro-project-init)
	* [neuro storage](#neuro-storage)
		* [neuro storage cp](#neuro-storage-cp)
		* [neuro storage ls](#neuro-storage-ls)
		* [neuro storage glob](#neuro-storage-glob)
		* [neuro storage rm](#neuro-storage-rm)
		* [neuro storage mkdir](#neuro-storage-mkdir)
		* [neuro storage mv](#neuro-storage-mv)
		* [neuro storage tree](#neuro-storage-tree)
		* [neuro storage load](#neuro-storage-load)
	* [neuro image](#neuro-image)
		* [neuro image ls](#neuro-image-ls)
		* [neuro image push](#neuro-image-push)
		* [neuro image pull](#neuro-image-pull)
		* [neuro image tags](#neuro-image-tags)
	* [neuro config](#neuro-config)
		* [neuro config login](#neuro-config-login)
		* [neuro config login-with-token](#neuro-config-login-with-token)
		* [neuro config login-headless](#neuro-config-login-headless)
		* [neuro config show](#neuro-config-show)
		* [neuro config show-token](#neuro-config-show-token)
		* [neuro config show-quota](#neuro-config-show-quota)
		* [neuro config aliases](#neuro-config-aliases)
		* [neuro config get-clusters](#neuro-config-get-clusters)
		* [neuro config switch-cluster](#neuro-config-switch-cluster)
		* [neuro config docker](#neuro-config-docker)
		* [neuro config logout](#neuro-config-logout)
	* [neuro completion](#neuro-completion)
		* [neuro completion generate](#neuro-completion-generate)
		* [neuro completion patch](#neuro-completion-patch)
	* [neuro acl](#neuro-acl)
		* [neuro acl grant](#neuro-acl-grant)
		* [neuro acl revoke](#neuro-acl-revoke)
		* [neuro acl list](#neuro-acl-list)
	* [neuro help](#neuro-help)
	* [neuro run](#neuro-run)
	* [neuro submit](#neuro-submit)
	* [neuro ps](#neuro-ps)
	* [neuro status](#neuro-status)
	* [neuro exec](#neuro-exec)
	* [neuro port-forward](#neuro-port-forward)
	* [neuro logs](#neuro-logs)
	* [neuro kill](#neuro-kill)
	* [neuro top](#neuro-top)
	* [neuro save](#neuro-save)
	* [neuro login](#neuro-login)
	* [neuro logout](#neuro-logout)
	* [neuro cp](#neuro-cp)
	* [neuro ls](#neuro-ls)
	* [neuro rm](#neuro-rm)
	* [neuro mkdir](#neuro-mkdir)
	* [neuro mv](#neuro-mv)
	* [neuro images](#neuro-images)
	* [neuro push](#neuro-push)
	* [neuro pull](#neuro-pull)
	* [neuro share](#neuro-share)
* [Api](#Api)
* [Contributing](#Contributing)


# Preface

Welcome to Neuromation API Python client.
Package ship command line tool called [_neuro_](#neuro). With [_neuro_](#neuro) you can:
* [Execute and debug jobs](#neuro-job)
* [Manipulate Data](#neuro-storage)
* Make some fun

# neuro

**Usage:**

```bash
neuro [OPTIONS] COMMAND [ARGS]...
```

**Options:**

Name | Description|
|----|------------|
|_\-v, --verbose_|Give more output. Option is additive, and can be used up to 2 times.|
|_\-q, --quiet_|Give less output. Option is additive, and can be used up to 2 times.|
|_\--neuromation-config PATH_|Path to config directory.|
|_\--show-traceback_|Show python traceback on error, useful for debugging the tool.|
|_--color \[yes &#124; no &#124; auto]_|Color mode.|
|_\--disable-pypi-version-check_|Don't periodically check PyPI to determine whether a new version of Neuro Platform CLI is available for download.|
|_\--network-timeout FLOAT_|Network read timeout, seconds.|
|_--version_|Show the version and exit.|
|_--trace_|Trace sent HTTP requests and received replies to stderr.|
|_\--hide-token / --no-hide-token_|Prevent user's token sent in HTTP headers from being printed out to stderr during HTTP tracing. Can be used only together with option '--trace'. On by default.|
|_\--skip-stats / --no-skip-stats_|Skip sending usage statistics to Neuro servers. Note: the statistics has no sensitive data, e.g. file, job, image, or user names, executed command lines, environment variables, etc.|
|_--help_|Show this message and exit.|


**Command Groups:**

|Usage|Description|
|---|---|
| _[neuro admin](#neuro-admin)_| Cluster administration commands |
| _[neuro job](#neuro-job)_| Job operations |
| _[neuro project](#neuro-project)_| Project operations |
| _[neuro storage](#neuro-storage)_| Storage operations |
| _[neuro image](#neuro-image)_| Container image operations |
| _[neuro config](#neuro-config)_| Client configuration |
| _[neuro completion](#neuro-completion)_| Output shell completion code |
| _[neuro acl](#neuro-acl)_| Access Control List management |


**Commands:**

|Usage|Description|
|---|---|
| _[neuro help](#neuro-help)_| Get help on a command |
| _[neuro run](#neuro-run)_| Run a job with predefined resources configuration |
| _[neuro submit](#neuro-submit)_| Submit an image to run on the cluster |
| _[neuro ps](#neuro-ps)_| List all jobs |
| _[neuro status](#neuro-status)_| Display status of a job |
| _[neuro exec](#neuro-exec)_| Execute command in a running job |
| _[neuro port-forward](#neuro-port-forward)_| Forward port\(s) of a running job to local port\(s) |
| _[neuro logs](#neuro-logs)_| Print the logs for a container |
| _[neuro kill](#neuro-kill)_| Kill job\(s) |
| _[neuro top](#neuro-top)_| Display GPU/CPU/Memory usage |
| _[neuro save](#neuro-save)_| Save job's state to an image |
| _[neuro login](#neuro-login)_| Log into Neuro Platform |
| _[neuro logout](#neuro-logout)_| Log out |
| _[neuro cp](#neuro-cp)_| Copy files and directories |
| _[neuro ls](#neuro-ls)_| List directory contents |
| _[neuro rm](#neuro-rm)_| Remove files or directories |
| _[neuro mkdir](#neuro-mkdir)_| Make directories |
| _[neuro mv](#neuro-mv)_| Move or rename files and directories |
| _[neuro images](#neuro-images)_| List images |
| _[neuro push](#neuro-push)_| Push an image to platform registry |
| _[neuro pull](#neuro-pull)_| Pull an image from platform registry |
| _[neuro share](#neuro-share)_| Shares resource with another user |




## neuro admin

Cluster administration commands.

**Usage:**

```bash
neuro admin [OPTIONS] COMMAND [ARGS]...
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|


**Commands:**

|Usage|Description|
|---|---|
| _[neuro admin get-clusters](#neuro-admin-get-clusters)_| Print the list of available clusters |
| _[neuro admin generate\-cluster-config](#neuro-admin-generate-cluster-config)_| Create a cluster configuration file |
| _[neuro admin add-cluster](#neuro-admin-add-cluster)_| Create a new cluster and start its provisioning |
| _[neuro admin get\-cluster-users](#neuro-admin-get-cluster-users)_| Print the list of all users in the cluster with their assigned role |
| _[neuro admin add\-cluster-user](#neuro-admin-add-cluster-user)_| Add user access to specified cluster |
| _[neuro admin remove\-cluster-user](#neuro-admin-remove-cluster-user)_| Remove user access from the cluster |
| _[neuro admin set\-user-quota](#neuro-admin-set-user-quota)_| Set user quota to given values |
| _[neuro admin add\-user-quota](#neuro-admin-add-user-quota)_| Add given values to user quota |




### neuro admin get-clusters

Print the list of available clusters.

**Usage:**

```bash
neuro admin get-clusters [OPTIONS]
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro admin generate-cluster-config

Create a cluster configuration file.

**Usage:**

```bash
neuro admin generate-cluster-config [OPTIONS] [CONFIG]
```

**Options:**

Name | Description|
|----|------------|
|_--type \[aws &#124; gcp]_||
|_--help_|Show this message and exit.|




### neuro admin add-cluster

Create a new cluster and start its provisioning.

**Usage:**

```bash
neuro admin add-cluster [OPTIONS] CLUSTER_NAME CONFIG
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro admin get-cluster-users

Print the list of all users in the cluster with their assigned role.

**Usage:**

```bash
neuro admin get-cluster-users [OPTIONS] [CLUSTER_NAME]
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro admin add-cluster-user

Add user access to specified cluster.<br/><br/>The command supports one of 3 user roles: admin, manager or user.

**Usage:**

```bash
neuro admin add-cluster-user [OPTIONS] CLUSTER_NAME USER_NAME [ROLE]
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro admin remove-cluster-user

Remove user access from the cluster.

**Usage:**

```bash
neuro admin remove-cluster-user [OPTIONS] CLUSTER_NAME USER_NAME
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro admin set-user-quota

Set user quota to given values

**Usage:**

```bash
neuro admin set-user-quota [OPTIONS] CLUSTER_NAME USER_NAME
```

**Options:**

Name | Description|
|----|------------|
|_\-g, --gpu AMOUNT_|GPU quota value in hours \(h) or minutes \(m).|
|_\-n, --non-gpu AMOUNT_|Non-GPU quota value in hours \(h) or minutes \(m).|
|_--help_|Show this message and exit.|




### neuro admin add-user-quota

Add given values to user quota

**Usage:**

```bash
neuro admin add-user-quota [OPTIONS] CLUSTER_NAME USER_NAME
```

**Options:**

Name | Description|
|----|------------|
|_\-g, --gpu AMOUNT_|Additional GPU quota value in hours \(h) or minutes \(m).|
|_\-n, --non-gpu AMOUNT_|Additional non-GPU quota value in hours \(h) or minutes \(m).|
|_--help_|Show this message and exit.|




## neuro job

Job operations.

**Usage:**

```bash
neuro job [OPTIONS] COMMAND [ARGS]...
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|


**Commands:**

|Usage|Description|
|---|---|
| _[neuro job run](#neuro-job-run)_| Run a job with predefined resources configuration |
| _[neuro job submit](#neuro-job-submit)_| Submit an image to run on the cluster |
| _[neuro job ls](#neuro-job-ls)_| List all jobs |
| _[neuro job status](#neuro-job-status)_| Display status of a job |
| _[neuro job tags](#neuro-job-tags)_| List all tags submitted by the user |
| _[neuro job exec](#neuro-job-exec)_| Execute command in a running job |
| _[neuro job port-forward](#neuro-job-port-forward)_| Forward port\(s) of a running job to local port\(s) |
| _[neuro job logs](#neuro-job-logs)_| Print the logs for a container |
| _[neuro job kill](#neuro-job-kill)_| Kill job\(s) |
| _[neuro job top](#neuro-job-top)_| Display GPU/CPU/Memory usage |
| _[neuro job save](#neuro-job-save)_| Save job's state to an image |
| _[neuro job browse](#neuro-job-browse)_| Opens a job's URL in a web browser |




### neuro job run

Run a job with predefined resources configuration.<br/><br/>IMAGE container image name.<br/><br/>CMD list will be passed as commands to model container.<br/>

**Usage:**

```bash
neuro job run [OPTIONS] IMAGE [CMD]...
```

**Examples:**

```bash

# Starts a container pytorch:latest on a machine with smaller GPU resources
# (see exact values in `neuro config show`) and with two volumes mounted:
#   storage://<home-directory>   --> /var/storage/home (in read-write mode),
#   storage://neuromation/public --> /var/storage/neuromation (in read-only mode).
neuro run --preset=gpu-small --volume=HOME pytorch:latest

# Starts a container using the custom image my-ubuntu:latest stored in neuromation
# registry, run /script.sh and pass arg1 and arg2 as its arguments:
neuro run -s cpu-small image:my-ubuntu:latest --entrypoint=/script.sh arg1 arg2

```

**Options:**

Name | Description|
|----|------------|
|_\-s, --preset PRESET_|Predefined resource configuration \(to see available values, run `neuro config show`)|
|_\-x, --extshm / -X, --no-extshm_|Request extended '/dev/shm' space  \[default: True]|
|_--http PORT_|Enable HTTP port forwarding to container  \[default: 80]|
|_\--http-auth / --no-http-auth_|Enable HTTP authentication for forwarded HTTP port  \[default: True]|
|_\-n, --name NAME_|Optional job name|
|_--tag TAG_|Optional job tag, multiple values allowed|
|_\-d, --description DESC_|Optional job description in free format|
|_\-q, --quiet_|Run command in quiet mode \(DEPRECATED)|
|_\-v, --volume MOUNT_|Mounts directory from vault into container. Use multiple options to mount more than one volume. --volume=HOME is an alias for storage::/var/storage/home:rw and storage://neuromation/public:/var/storage/neuromation:ro|
|_--entrypoint TEXT_|Executable entrypoint in the container \(note that it overwrites `ENTRYPOINT` and `CMD` instructions of the docker image)|
|_\-e, --env VAR=VAL_|Set environment variable in container Use multiple options to define more than one variable|
|_\--env-file PATH_|File with environment variables to pass|
|_\--life-span TIMEDELTA_|Optional job run-time limit in the format '1d2h3m4s' \(some parts may be missing). Set '0' to disable. Default value '1d' can be changed in the user config.|
|_\--wait-start / --no-wait-start_|Wait for a job start or failure  \[default: True]|
|_\--pass-config / --no-pass-config_|Upload neuro config to the job  \[default: False]|
|_--browse_|Open a job's URL in a web browser|
|_--detach_|Don't attach to job logs and don't wait for exit code|
|_\-t, --tty_|Allocate a TTY|
|_--help_|Show this message and exit.|




### neuro job submit

Submit an image to run on the cluster.<br/><br/>IMAGE container image name.<br/><br/>CMD list will be passed as commands to model container.<br/>

**Usage:**

```bash
neuro job submit [OPTIONS] IMAGE [CMD]...
```

**Examples:**

```bash

# Starts a container pytorch:latest with two paths mounted. Directory /q1/
# is mounted in read only mode to /qm directory within container.
# Directory /mod mounted to /mod directory in read-write mode.
neuro submit --volume storage:/q1:/qm:ro --volume storage:/mod:/mod:rw pytorch:latest

# Starts a container using the custom image my-ubuntu:latest stored in neuromation
# registry, run /script.sh and pass arg1 arg2 arg3 as its arguments:
neuro submit image:my-ubuntu:latest --entrypoint=/script.sh arg1 arg2 arg3

```

**Options:**

Name | Description|
|----|------------|
|_\-g, --gpu NUMBER_|Number of GPUs to request  \[default: 0]|
|_\--gpu-model MODEL_|GPU to use  \[default: nvidia\-tesla-k80]|
|_\--tpu-type TYPE_|TPU type to use|
|_\--tpu-sw-version VERSION_|Requested TPU software version|
|_\-c, --cpu NUMBER_|Number of CPUs to request  \[default: 0.1]|
|_\-m, --memory AMOUNT_|Memory amount to request  \[default: 1G]|
|_\-x, --extshm / -X, --no-extshm_|Request extended '/dev/shm' space  \[default: True]|
|_--http PORT_|Enable HTTP port forwarding to container|
|_\--http-auth / --no-http-auth_|Enable HTTP authentication for forwarded HTTP port  \[default: True]|
|_\-p, --preemptible / -P, --non-preemptible_|Run job on a lower-cost preemptible instance  \[default: False]|
|_\-n, --name NAME_|Optional job name|
|_--tag TAG_|Optional job tag, multiple values allowed|
|_\-d, --description DESC_|Optional job description in free format|
|_\-q, --quiet_|Run command in quiet mode \(DEPRECATED)|
|_\-v, --volume MOUNT_|Mounts directory from vault into container. Use multiple options to mount more than one volume. --volume=HOME is an alias for storage::/var/storage/home:rw and storage://neuromation/public:/var/storage/neuromation:ro|
|_--entrypoint TEXT_|Executable entrypoint in the container \(note that it overwrites `ENTRYPOINT` and `CMD` instructions of the docker image)|
|_\-e, --env VAR=VAL_|Set environment variable in container Use multiple options to define more than one variable|
|_\--env-file PATH_|File with environment variables to pass|
|_\--life-span TIMEDELTA_|Optional job run-time limit in the format '1d2h3m4s' \(some parts may be missing). Set '0' to disable. Default value '1d' can be changed in the user config.|
|_\--wait-start / --no-wait-start_|Wait for a job start or failure  \[default: True]|
|_\--pass-config / --no-pass-config_|Upload neuro config to the job  \[default: False]|
|_--browse_|Open a job's URL in a web browser|
|_--detach_|Don't attach to job logs and don't wait for exit code|
|_\-t, --tty_|Allocate a TTY|
|_--help_|Show this message and exit.|




### neuro job ls

List all jobs.<br/>

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

Name | Description|
|----|------------|
|_\-s, --status \[pending &#124; running &#124; succeeded &#124; failed &#124; all]_|Filter out jobs by status \(multiple option). Note: option `all` is deprecated, use `neuro ps -a` instead.|
|_\-o, --owner TEXT_|Filter out jobs by owner \(multiple option).|
|_\-a, --all_|Show all jobs regardless the status \(equivalent to `\-s pending -s running -s succeeded -s failed`).|
|_\-n, --name NAME_|Filter out jobs by name.|
|_\-t, --tag TAG_|Filter out jobs by tag \(multiple option)|
|_\-d, --description DESCRIPTION_|Filter out jobs by description \(exact match).|
|_\-q, --quiet_|Run command in quiet mode \(DEPRECATED)|
|_\-w, --wide_|Do not cut long lines for terminal width.|
|_--format COLUMNS_|Output table format, see "neuro help ps\-format" for more info about the format specification. The default can be changed using the job.ps-format configuration variable documented in "neuro help user-config"|
|_\--full-uri_|Output full image URI.|
|_--help_|Show this message and exit.|




### neuro job status

Display status of a job.

**Usage:**

```bash
neuro job status [OPTIONS] JOB
```

**Options:**

Name | Description|
|----|------------|
|_\--full-uri_|Output full URI.|
|_--help_|Show this message and exit.|




### neuro job tags

List all tags submitted by the user.

**Usage:**

```bash
neuro job tags [OPTIONS]
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro job exec

Execute command in a running job.<br/>

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

Name | Description|
|----|------------|
|_\-t, --tty / -T, --no-tty_|Allocate virtual tty. Useful for interactive jobs.|
|_\--no-key-check_|Disable host key checks. Should be used with caution.|
|_--timeout FLOAT_|Maximum allowed time for executing the command, 0 for no timeout  \[default: 0]|
|_--help_|Show this message and exit.|




### neuro job port-forward

Forward port\(s) of a running job to local port\(s).<br/>

**Usage:**

```bash
neuro job port-forward [OPTIONS] JOB LOCAL_REMOTE_PORT...
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
neuro job port-forward my-job- 2080:80 2222:22 2000:100

```

**Options:**

Name | Description|
|----|------------|
|_\--no-key-check_|Disable host key checks. Should be used with caution.|
|_--help_|Show this message and exit.|




### neuro job logs

Print the logs for a container.

**Usage:**

```bash
neuro job logs [OPTIONS] JOB
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro job kill

Kill job\(s).

**Usage:**

```bash
neuro job kill [OPTIONS] JOBS...
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro job top

Display GPU/CPU/Memory usage.

**Usage:**

```bash
neuro job top [OPTIONS] JOB
```

**Options:**

Name | Description|
|----|------------|
|_--timeout FLOAT_|Maximum allowed time for executing the command, 0 for no timeout  \[default: 0]|
|_--help_|Show this message and exit.|




### neuro job save

Save job's state to an image.<br/>

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

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro job browse

Opens a job's URL in a web browser.

**Usage:**

```bash
neuro job browse [OPTIONS] JOB
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




## neuro project

Project operations.

**Usage:**

```bash
neuro project [OPTIONS] COMMAND [ARGS]...
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|


**Commands:**

|Usage|Description|
|---|---|
| _[neuro project init](#neuro-project-init)_| Initialize an empty project |




### neuro project init

Initialize an empty project.<br/>

**Usage:**

```bash
neuro project init [OPTIONS] [SLUG]
```

**Examples:**

```bash

# Initializes a scaffolding for the new project with the recommended project
# structure (see http://github.com/neuromation/cookiecutter-neuro-project)
neuro project init

# Initializes a scaffolding for the new project with the recommended project
# structure and sets default project folder name to "example"
neuro project init my-project-id

```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




## neuro storage

Storage operations.

**Usage:**

```bash
neuro storage [OPTIONS] COMMAND [ARGS]...
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|


**Commands:**

|Usage|Description|
|---|---|
| _[neuro storage cp](#neuro-storage-cp)_| Copy files and directories |
| _[neuro storage ls](#neuro-storage-ls)_| List directory contents |
| _[neuro storage glob](#neuro-storage-glob)_| List resources that match PATTERNS |
| _[neuro storage rm](#neuro-storage-rm)_| Remove files or directories |
| _[neuro storage mkdir](#neuro-storage-mkdir)_| Make directories |
| _[neuro storage mv](#neuro-storage-mv)_| Move or rename files and directories |
| _[neuro storage tree](#neuro-storage-tree)_| List contents of directories in a tree-like format |
| _[neuro storage load](#neuro-storage-load)_| Copy files and directories using MinIO \(EXPERIMENTAL) |




### neuro storage cp

Copy files and directories.<br/><br/>Either SOURCES or DESTINATION should have storage:// scheme. If scheme is<br/>omitted, file:// scheme is assumed.<br/><br/>Use /dev/stdin and /dev/stdout file names to copy a file from terminal and<br/>print the content of file on the storage to console.<br/>

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

Name | Description|
|----|------------|
|_\-r, --recursive_|Recursive copy, off by default|
|_\--glob / --no-glob_|Expand glob patterns in SOURCES with explicit scheme.  \[default: True]|
|_\-t, --target-directory DIRECTORY_|Copy all SOURCES into DIRECTORY.|
|_\-T, --no-target-directory_|Treat DESTINATION as a normal file.|
|_\-u, --update_|Copy only when the SOURCE file is newer than the destination file or when the destination file is missing.|
|_--exclude_|Exclude files and directories that match the specified pattern. The default can be changed using the storage.cp\-exclude configuration variable documented in "neuro help user-config"|
|_--include_|Don't exclude files and directories that match the specified pattern. The default can be changed using the storage.cp\-exclude configuration variable documented in "neuro help user-config"|
|_\-p, --progress / -P, --no-progress_|Show progress, on by default.|
|_--help_|Show this message and exit.|




### neuro storage ls

List directory contents.<br/><br/>By default PATH is equal user's home dir \(storage:)

**Usage:**

```bash
neuro storage ls [OPTIONS] [PATHS]...
```

**Options:**

Name | Description|
|----|------------|
|_\-a, --all_|do not ignore entries starting with .|
|_\-d, --directory_|list directories themselves, not their contents.|
|_\-h, --human-readable_|with -l print human readable sizes \(e.g., 2K, 540M).|
|_-l_|use a long listing format.|
|_--sort \[name &#124; size &#124; time]_|sort by given field, default is name.|
|_--help_|Show this message and exit.|




### neuro storage glob

List resources that match PATTERNS.

**Usage:**

```bash
neuro storage glob [OPTIONS] [PATTERNS]...
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro storage rm

Remove files or directories.<br/>

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

Name | Description|
|----|------------|
|_\-r, --recursive_|remove directories and their contents recursively|
|_\--glob / --no-glob_|Expand glob patterns in PATHS  \[default: True]|
|_--help_|Show this message and exit.|




### neuro storage mkdir

Make directories.

**Usage:**

```bash
neuro storage mkdir [OPTIONS] PATHS...
```

**Options:**

Name | Description|
|----|------------|
|_\-p, --parents_|No error if existing, make parent directories as needed|
|_--help_|Show this message and exit.|




### neuro storage mv

Move or rename files and directories.<br/><br/>SOURCE must contain path to the file or directory existing on the storage,<br/>and DESTINATION must contain the full path to the target file or directory.<br/>

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

Name | Description|
|----|------------|
|_\--glob / --no-glob_|Expand glob patterns in SOURCES  \[default: True]|
|_\-t, --target-directory DIRECTORY_|Copy all SOURCES into DIRECTORY|
|_\-T, --no-target-directory_|Treat DESTINATION as a normal file|
|_--help_|Show this message and exit.|




### neuro storage tree

List contents of directories in a tree-like format.<br/><br/>Tree is a recursive directory listing program that produces a depth indented<br/>listing of files, which is colorized ala dircolors if the LS_COLORS<br/>environment variable is set and output is to tty.  With no arguments, tree<br/>lists the files in the storage: directory.  When directory arguments are<br/>given, tree lists all the files and/or directories found in the given<br/>directories each in turn.  Upon completion of listing all files/directories<br/>found, tree returns the total number of files and/or directories listed.<br/><br/>By default PATH is equal user's home dir \(storage:)

**Usage:**

```bash
neuro storage tree [OPTIONS] [PATH]
```

**Options:**

Name | Description|
|----|------------|
|_\-a, --all_|do not ignore entries starting with .|
|_\-h, --human-readable_|Print the size in a more human readable way.|
|_\-s, --size_|Print the size in bytes of each file.|
|_--sort \[name &#124; size &#124; time]_|sort by given field, default is name|
|_--help_|Show this message and exit.|




### neuro storage load

Copy files and directories using MinIO \(EXPERIMENTAL).<br/><br/>Same as "cp", but uses MinIO and the Amazon S3 protocol.<br/>\(DEPRECATED)

**Usage:**

```bash
neuro storage load [OPTIONS] [SOURCES]... [DESTINATION]
```

**Options:**

Name | Description|
|----|------------|
|_\-r, --recursive_|Recursive copy, off by default|
|_\--glob / --no-glob_|Expand glob patterns in SOURCES with explicit scheme  \[default: True]|
|_\-t, --target-directory DIRECTORY_|Copy all SOURCES into DIRECTORY|
|_\-T, --no-target-directory_|Treat DESTINATION as a normal file|
|_\-u, --update_|Copy only when the SOURCE file is newer than the destination file or when the destination file is missing|
|_\-p, --progress_|Show progress, off by default|
|_--help_|Show this message and exit.|




## neuro image

Container image operations.

**Usage:**

```bash
neuro image [OPTIONS] COMMAND [ARGS]...
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|


**Commands:**

|Usage|Description|
|---|---|
| _[neuro image ls](#neuro-image-ls)_| List images |
| _[neuro image push](#neuro-image-push)_| Push an image to platform registry |
| _[neuro image pull](#neuro-image-pull)_| Pull an image from platform registry |
| _[neuro image tags](#neuro-image-tags)_| List tags for image in platform registry |




### neuro image ls

List images.

**Usage:**

```bash
neuro image ls [OPTIONS]
```

**Options:**

Name | Description|
|----|------------|
|_-l_|List in long format.|
|_\--full-uri_|Output full image URI.|
|_--help_|Show this message and exit.|




### neuro image push

Push an image to platform registry.<br/><br/>Remote image must be URL with image:// scheme. Image names can contain tag.<br/>If tags not specified 'latest' will be used as value.<br/>

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

Name | Description|
|----|------------|
|_\-q, --quiet_|Run command in quiet mode \(DEPRECATED)|
|_--help_|Show this message and exit.|




### neuro image pull

Pull an image from platform registry.<br/><br/>Remote image name must be URL with image:// scheme. Image names can contain<br/>tag.<br/>

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

Name | Description|
|----|------------|
|_\-q, --quiet_|Run command in quiet mode \(DEPRECATED)|
|_--help_|Show this message and exit.|




### neuro image tags

List tags for image in platform registry.<br/><br/>Image name must be URL with image:// scheme.<br/>

**Usage:**

```bash
neuro image tags [OPTIONS] IMAGE
```

**Examples:**

```bash

neuro image tags image://myfriend/alpine
neuro image tags image:myimage

```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




## neuro config

Client configuration.

**Usage:**

```bash
neuro config [OPTIONS] COMMAND [ARGS]...
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|


**Commands:**

|Usage|Description|
|---|---|
| _[neuro config login](#neuro-config-login)_| Log into Neuro Platform |
| _[neuro config login\-with-token](#neuro-config-login-with-token)_| Log into Neuro Platform with token |
| _[neuro config login-headless](#neuro-config-login-headless)_| Log into Neuro Platform from non-GUI server environment |
| _[neuro config show](#neuro-config-show)_| Print current settings |
| _[neuro config show-token](#neuro-config-show-token)_| Print current authorization token |
| _[neuro config show-quota](#neuro-config-show-quota)_| Print quota and remaining computation time for active cluster |
| _[neuro config aliases](#neuro-config-aliases)_| List available command aliases |
| _[neuro config get-clusters](#neuro-config-get-clusters)_| Fetch and display the list of available clusters |
| _[neuro config switch-cluster](#neuro-config-switch-cluster)_| Switch the active cluster |
| _[neuro config docker](#neuro-config-docker)_| Configure docker client to fit the Neuro Platform |
| _[neuro config logout](#neuro-config-logout)_| Log out |




### neuro config login

Log into Neuro Platform.<br/><br/>URL is a platform entrypoint URL.

**Usage:**

```bash
neuro config login [OPTIONS] [URL]
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro config login-with-token

Log into Neuro Platform with token.<br/><br/>TOKEN is authentication token provided by administration team. URL is a<br/>platform entrypoint URL.

**Usage:**

```bash
neuro config login-with-token [OPTIONS] TOKEN [URL]
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro config login-headless

Log into Neuro Platform from non-GUI server environment.<br/><br/>URL is a platform entrypoint URL.<br/><br/>The command works similar to "neuro login" but instead of opening a browser<br/>for performing OAuth registration prints an URL that should be open on guest<br/>host.<br/><br/>Then user inputs a code displayed in a browser after successful login back<br/>in neuro command to finish the login process.

**Usage:**

```bash
neuro config login-headless [OPTIONS] [URL]
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro config show

Print current settings.

**Usage:**

```bash
neuro config show [OPTIONS]
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro config show-token

Print current authorization token.

**Usage:**

```bash
neuro config show-token [OPTIONS]
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro config show-quota

Print quota and remaining computation time for active cluster.

**Usage:**

```bash
neuro config show-quota [OPTIONS] [USER]
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro config aliases

List available command aliases.

**Usage:**

```bash
neuro config aliases [OPTIONS]
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro config get-clusters

Fetch and display the list of available clusters.

**Usage:**

```bash
neuro config get-clusters [OPTIONS]
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro config switch-cluster

Switch the active cluster.<br/><br/>CLUSTER_NAME is the cluster name to select.  The interactive prompt is used<br/>if the name is omitted \(default).

**Usage:**

```bash
neuro config switch-cluster [OPTIONS] [CLUSTER_NAME]
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro config docker

Configure docker client to fit the Neuro Platform.

**Usage:**

```bash
neuro config docker [OPTIONS]
```

**Options:**

Name | Description|
|----|------------|
|_\--docker-config PATH_|Specifies the location of the Docker client configuration files|
|_--help_|Show this message and exit.|




### neuro config logout

Log out.

**Usage:**

```bash
neuro config logout [OPTIONS]
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




## neuro completion

Output shell completion code.

**Usage:**

```bash
neuro completion [OPTIONS] COMMAND [ARGS]...
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|


**Commands:**

|Usage|Description|
|---|---|
| _[neuro completion generate](#neuro-completion-generate)_| Provide an instruction for shell completion generation |
| _[neuro completion patch](#neuro-completion-patch)_| Automatically patch shell configuration profile to enable completion |




### neuro completion generate

Provide an instruction for shell completion generation.

**Usage:**

```bash
neuro completion generate [OPTIONS] [bash|zsh]
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro completion patch

Automatically patch shell configuration profile to enable completion

**Usage:**

```bash
neuro completion patch [OPTIONS] [bash|zsh]
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




## neuro acl

Access Control List management.

**Usage:**

```bash
neuro acl [OPTIONS] COMMAND [ARGS]...
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|


**Commands:**

|Usage|Description|
|---|---|
| _[neuro acl grant](#neuro-acl-grant)_| Shares resource with another user |
| _[neuro acl revoke](#neuro-acl-revoke)_| Revoke user access from another user |
| _[neuro acl list](#neuro-acl-list)_| List shared resources |




### neuro acl grant

Shares resource with another user.<br/><br/>URI shared resource.<br/><br/>USER username to share resource with.<br/><br/>PERMISSION sharing access right: read, write, or manage.<br/>

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

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro acl revoke

Revoke user access from another user.<br/><br/>URI previously shared resource to revoke.<br/><br/>USER to revoke URI resource from.<br/>

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

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro acl list

List shared resources.<br/><br/>The command displays a list of resources shared BY current user \(default).<br/><br/>To display a list of resources shared WITH current user apply --shared<br/>option.<br/>

**Usage:**

```bash
neuro acl list [OPTIONS]
```

**Examples:**

```bash

neuro acl list
neuro acl list --scheme storage
neuro acl list --shared
neuro acl list --shared --scheme image

```

**Options:**

Name | Description|
|----|------------|
|_-u TEXT_|Use specified user or role.|
|_\-s, --scheme TEXT_|Filter resources by scheme, e.g. job, storage, image or user.|
|_--shared_|Output the resources shared by the user.|
|_\--full-uri_|Output full URI.|
|_--help_|Show this message and exit.|




## neuro help

Get help on a command.

**Usage:**

```bash
neuro help [OPTIONS] [COMMAND]...
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




## neuro run

Run a job with predefined resources configuration.<br/><br/>IMAGE container image name.<br/><br/>CMD list will be passed as commands to model container.<br/>

**Usage:**

```bash
neuro run [OPTIONS] IMAGE [CMD]...
```

**Examples:**

```bash

# Starts a container pytorch:latest on a machine with smaller GPU resources
# (see exact values in `neuro config show`) and with two volumes mounted:
#   storage://<home-directory>   --> /var/storage/home (in read-write mode),
#   storage://neuromation/public --> /var/storage/neuromation (in read-only mode).
neuro run --preset=gpu-small --volume=HOME pytorch:latest

# Starts a container using the custom image my-ubuntu:latest stored in neuromation
# registry, run /script.sh and pass arg1 and arg2 as its arguments:
neuro run -s cpu-small image:my-ubuntu:latest --entrypoint=/script.sh arg1 arg2

```

**Options:**

Name | Description|
|----|------------|
|_\-s, --preset PRESET_|Predefined resource configuration \(to see available values, run `neuro config show`)|
|_\-x, --extshm / -X, --no-extshm_|Request extended '/dev/shm' space  \[default: True]|
|_--http PORT_|Enable HTTP port forwarding to container  \[default: 80]|
|_\--http-auth / --no-http-auth_|Enable HTTP authentication for forwarded HTTP port  \[default: True]|
|_\-n, --name NAME_|Optional job name|
|_--tag TAG_|Optional job tag, multiple values allowed|
|_\-d, --description DESC_|Optional job description in free format|
|_\-q, --quiet_|Run command in quiet mode \(DEPRECATED)|
|_\-v, --volume MOUNT_|Mounts directory from vault into container. Use multiple options to mount more than one volume. --volume=HOME is an alias for storage::/var/storage/home:rw and storage://neuromation/public:/var/storage/neuromation:ro|
|_--entrypoint TEXT_|Executable entrypoint in the container \(note that it overwrites `ENTRYPOINT` and `CMD` instructions of the docker image)|
|_\-e, --env VAR=VAL_|Set environment variable in container Use multiple options to define more than one variable|
|_\--env-file PATH_|File with environment variables to pass|
|_\--life-span TIMEDELTA_|Optional job run-time limit in the format '1d2h3m4s' \(some parts may be missing). Set '0' to disable. Default value '1d' can be changed in the user config.|
|_\--wait-start / --no-wait-start_|Wait for a job start or failure  \[default: True]|
|_\--pass-config / --no-pass-config_|Upload neuro config to the job  \[default: False]|
|_--browse_|Open a job's URL in a web browser|
|_--detach_|Don't attach to job logs and don't wait for exit code|
|_\-t, --tty_|Allocate a TTY|
|_--help_|Show this message and exit.|




## neuro submit

Submit an image to run on the cluster.<br/><br/>IMAGE container image name.<br/><br/>CMD list will be passed as commands to model container.<br/>

**Usage:**

```bash
neuro submit [OPTIONS] IMAGE [CMD]...
```

**Examples:**

```bash

# Starts a container pytorch:latest with two paths mounted. Directory /q1/
# is mounted in read only mode to /qm directory within container.
# Directory /mod mounted to /mod directory in read-write mode.
neuro submit --volume storage:/q1:/qm:ro --volume storage:/mod:/mod:rw pytorch:latest

# Starts a container using the custom image my-ubuntu:latest stored in neuromation
# registry, run /script.sh and pass arg1 arg2 arg3 as its arguments:
neuro submit image:my-ubuntu:latest --entrypoint=/script.sh arg1 arg2 arg3

```

**Options:**

Name | Description|
|----|------------|
|_\-g, --gpu NUMBER_|Number of GPUs to request  \[default: 0]|
|_\--gpu-model MODEL_|GPU to use  \[default: nvidia\-tesla-k80]|
|_\--tpu-type TYPE_|TPU type to use|
|_\--tpu-sw-version VERSION_|Requested TPU software version|
|_\-c, --cpu NUMBER_|Number of CPUs to request  \[default: 0.1]|
|_\-m, --memory AMOUNT_|Memory amount to request  \[default: 1G]|
|_\-x, --extshm / -X, --no-extshm_|Request extended '/dev/shm' space  \[default: True]|
|_--http PORT_|Enable HTTP port forwarding to container|
|_\--http-auth / --no-http-auth_|Enable HTTP authentication for forwarded HTTP port  \[default: True]|
|_\-p, --preemptible / -P, --non-preemptible_|Run job on a lower-cost preemptible instance  \[default: False]|
|_\-n, --name NAME_|Optional job name|
|_--tag TAG_|Optional job tag, multiple values allowed|
|_\-d, --description DESC_|Optional job description in free format|
|_\-q, --quiet_|Run command in quiet mode \(DEPRECATED)|
|_\-v, --volume MOUNT_|Mounts directory from vault into container. Use multiple options to mount more than one volume. --volume=HOME is an alias for storage::/var/storage/home:rw and storage://neuromation/public:/var/storage/neuromation:ro|
|_--entrypoint TEXT_|Executable entrypoint in the container \(note that it overwrites `ENTRYPOINT` and `CMD` instructions of the docker image)|
|_\-e, --env VAR=VAL_|Set environment variable in container Use multiple options to define more than one variable|
|_\--env-file PATH_|File with environment variables to pass|
|_\--life-span TIMEDELTA_|Optional job run-time limit in the format '1d2h3m4s' \(some parts may be missing). Set '0' to disable. Default value '1d' can be changed in the user config.|
|_\--wait-start / --no-wait-start_|Wait for a job start or failure  \[default: True]|
|_\--pass-config / --no-pass-config_|Upload neuro config to the job  \[default: False]|
|_--browse_|Open a job's URL in a web browser|
|_--detach_|Don't attach to job logs and don't wait for exit code|
|_\-t, --tty_|Allocate a TTY|
|_--help_|Show this message and exit.|




## neuro ps

List all jobs.<br/>

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

Name | Description|
|----|------------|
|_\-s, --status \[pending &#124; running &#124; succeeded &#124; failed &#124; all]_|Filter out jobs by status \(multiple option). Note: option `all` is deprecated, use `neuro ps -a` instead.|
|_\-o, --owner TEXT_|Filter out jobs by owner \(multiple option).|
|_\-a, --all_|Show all jobs regardless the status \(equivalent to `\-s pending -s running -s succeeded -s failed`).|
|_\-n, --name NAME_|Filter out jobs by name.|
|_\-t, --tag TAG_|Filter out jobs by tag \(multiple option)|
|_\-d, --description DESCRIPTION_|Filter out jobs by description \(exact match).|
|_\-q, --quiet_|Run command in quiet mode \(DEPRECATED)|
|_\-w, --wide_|Do not cut long lines for terminal width.|
|_--format COLUMNS_|Output table format, see "neuro help ps\-format" for more info about the format specification. The default can be changed using the job.ps-format configuration variable documented in "neuro help user-config"|
|_\--full-uri_|Output full image URI.|
|_--help_|Show this message and exit.|




## neuro status

Display status of a job.

**Usage:**

```bash
neuro status [OPTIONS] JOB
```

**Options:**

Name | Description|
|----|------------|
|_\--full-uri_|Output full URI.|
|_--help_|Show this message and exit.|




## neuro exec

Execute command in a running job.<br/>

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

Name | Description|
|----|------------|
|_\-t, --tty / -T, --no-tty_|Allocate virtual tty. Useful for interactive jobs.|
|_\--no-key-check_|Disable host key checks. Should be used with caution.|
|_--timeout FLOAT_|Maximum allowed time for executing the command, 0 for no timeout  \[default: 0]|
|_--help_|Show this message and exit.|




## neuro port-forward

Forward port\(s) of a running job to local port\(s).<br/>

**Usage:**

```bash
neuro port-forward [OPTIONS] JOB LOCAL_REMOTE_PORT...
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
neuro job port-forward my-job- 2080:80 2222:22 2000:100

```

**Options:**

Name | Description|
|----|------------|
|_\--no-key-check_|Disable host key checks. Should be used with caution.|
|_--help_|Show this message and exit.|




## neuro logs

Print the logs for a container.

**Usage:**

```bash
neuro logs [OPTIONS] JOB
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




## neuro kill

Kill job\(s).

**Usage:**

```bash
neuro kill [OPTIONS] JOBS...
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




## neuro top

Display GPU/CPU/Memory usage.

**Usage:**

```bash
neuro top [OPTIONS] JOB
```

**Options:**

Name | Description|
|----|------------|
|_--timeout FLOAT_|Maximum allowed time for executing the command, 0 for no timeout  \[default: 0]|
|_--help_|Show this message and exit.|




## neuro save

Save job's state to an image.<br/>

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

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




## neuro login

Log into Neuro Platform.<br/><br/>URL is a platform entrypoint URL.

**Usage:**

```bash
neuro login [OPTIONS] [URL]
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




## neuro logout

Log out.

**Usage:**

```bash
neuro logout [OPTIONS]
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




## neuro cp

Copy files and directories.<br/><br/>Either SOURCES or DESTINATION should have storage:// scheme. If scheme is<br/>omitted, file:// scheme is assumed.<br/><br/>Use /dev/stdin and /dev/stdout file names to copy a file from terminal and<br/>print the content of file on the storage to console.<br/>

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

Name | Description|
|----|------------|
|_\-r, --recursive_|Recursive copy, off by default|
|_\--glob / --no-glob_|Expand glob patterns in SOURCES with explicit scheme.  \[default: True]|
|_\-t, --target-directory DIRECTORY_|Copy all SOURCES into DIRECTORY.|
|_\-T, --no-target-directory_|Treat DESTINATION as a normal file.|
|_\-u, --update_|Copy only when the SOURCE file is newer than the destination file or when the destination file is missing.|
|_--exclude_|Exclude files and directories that match the specified pattern. The default can be changed using the storage.cp\-exclude configuration variable documented in "neuro help user-config"|
|_--include_|Don't exclude files and directories that match the specified pattern. The default can be changed using the storage.cp\-exclude configuration variable documented in "neuro help user-config"|
|_\-p, --progress / -P, --no-progress_|Show progress, on by default.|
|_--help_|Show this message and exit.|




## neuro ls

List directory contents.<br/><br/>By default PATH is equal user's home dir \(storage:)

**Usage:**

```bash
neuro ls [OPTIONS] [PATHS]...
```

**Options:**

Name | Description|
|----|------------|
|_\-a, --all_|do not ignore entries starting with .|
|_\-d, --directory_|list directories themselves, not their contents.|
|_\-h, --human-readable_|with -l print human readable sizes \(e.g., 2K, 540M).|
|_-l_|use a long listing format.|
|_--sort \[name &#124; size &#124; time]_|sort by given field, default is name.|
|_--help_|Show this message and exit.|




## neuro rm

Remove files or directories.<br/>

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

Name | Description|
|----|------------|
|_\-r, --recursive_|remove directories and their contents recursively|
|_\--glob / --no-glob_|Expand glob patterns in PATHS  \[default: True]|
|_--help_|Show this message and exit.|




## neuro mkdir

Make directories.

**Usage:**

```bash
neuro mkdir [OPTIONS] PATHS...
```

**Options:**

Name | Description|
|----|------------|
|_\-p, --parents_|No error if existing, make parent directories as needed|
|_--help_|Show this message and exit.|




## neuro mv

Move or rename files and directories.<br/><br/>SOURCE must contain path to the file or directory existing on the storage,<br/>and DESTINATION must contain the full path to the target file or directory.<br/>

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

Name | Description|
|----|------------|
|_\--glob / --no-glob_|Expand glob patterns in SOURCES  \[default: True]|
|_\-t, --target-directory DIRECTORY_|Copy all SOURCES into DIRECTORY|
|_\-T, --no-target-directory_|Treat DESTINATION as a normal file|
|_--help_|Show this message and exit.|




## neuro images

List images.

**Usage:**

```bash
neuro images [OPTIONS]
```

**Options:**

Name | Description|
|----|------------|
|_-l_|List in long format.|
|_\--full-uri_|Output full image URI.|
|_--help_|Show this message and exit.|




## neuro push

Push an image to platform registry.<br/><br/>Remote image must be URL with image:// scheme. Image names can contain tag.<br/>If tags not specified 'latest' will be used as value.<br/>

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

Name | Description|
|----|------------|
|_\-q, --quiet_|Run command in quiet mode \(DEPRECATED)|
|_--help_|Show this message and exit.|




## neuro pull

Pull an image from platform registry.<br/><br/>Remote image name must be URL with image:// scheme. Image names can contain<br/>tag.<br/>

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

Name | Description|
|----|------------|
|_\-q, --quiet_|Run command in quiet mode \(DEPRECATED)|
|_--help_|Show this message and exit.|




## neuro share

Shares resource with another user.<br/><br/>URI shared resource.<br/><br/>USER username to share resource with.<br/><br/>PERMISSION sharing access right: read, write, or manage.<br/>

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

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




# Api

*TODO*

# Contributing

```shell
git clone https://github.com/neuromation/platform-api-clients.git
cd platform-api-clients/python
```

For OSX users install coreutils to properly interpret shell commands:

```
brew install coreutils
```

Before you begin, it is recommended to have clean virtual environment installed:

```shell
python -m venv .env
source .env/bin/activate
```

Development flow:

* Install dependencies: `make init`
* Run tests: `make test`
* Lint: `make lint`
* Publish to [pypi](https://pypi.org/project/neuromation/): `make publish`
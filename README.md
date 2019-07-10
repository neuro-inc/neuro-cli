[![codecov](https://codecov.io/gh/neuromation/platform-api-clients/branch/master/graph/badge.svg?token=FwM6ZV3gDj)](https://codecov.io/gh/neuromation/platform-api-clients)

# Table of Contents
* [Preface](#Preface)
* [neuro](#neuro)
	* [neuro job](#neuro-job)
		* [neuro job run](#neuro-job-run)
		* [neuro job submit](#neuro-job-submit)
		* [neuro job ls](#neuro-job-ls)
		* [neuro job status](#neuro-job-status)
		* [neuro job exec](#neuro-job-exec)
		* [neuro job port-forward](#neuro-job-port-forward)
		* [neuro job logs](#neuro-job-logs)
		* [neuro job kill](#neuro-job-kill)
		* [neuro job top](#neuro-job-top)
		* [neuro job browse](#neuro-job-browse)
	* [neuro storage](#neuro-storage)
		* [neuro storage cp](#neuro-storage-cp)
		* [neuro storage ls](#neuro-storage-ls)
		* [neuro storage rm](#neuro-storage-rm)
		* [neuro storage mkdir](#neuro-storage-mkdir)
		* [neuro storage mv](#neuro-storage-mv)
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
|_\--neuromation-config PATH_|Path to config file.|
|_\--show-traceback_|Show python traceback on error, useful for debugging the tool.|
|_--color \[yes &#124; no &#124; auto]_|Color mode.|
|_\--disable-pypi-version-check_|Don't periodically check PyPI to determine whether a new version of Neuromation CLI is available for download.|
|_\--network-timeout FLOAT_|Network read timeout, seconds.|
|_--version_|Show the version and exit.|
|_--help_|Show this message and exit.|


**Command Groups:**

|Usage|Description|
|---|---|
| _[neuro job](#neuro-job)_| Job operations |
| _[neuro storage](#neuro-storage)_| Storage operations |
| _[neuro image](#neuro-image)_| Container image operations |
| _[neuro config](#neuro-config)_| Client configuration |
| _[neuro completion](#neuro-completion)_| Output shell completion code |
| _[neuro acl](#neuro-acl)_| ACL operations |


**Commands:**

|Usage|Description|
|---|---|
| _[neuro help](#neuro-help)_| Get help on a command |
| _[neuro run](#neuro-run)_| Run an image with predefined configuration |
| _[neuro submit](#neuro-submit)_| Submit an image to run on the cluster |
| _[neuro ps](#neuro-ps)_| List all jobs |
| _[neuro status](#neuro-status)_| Display status of a job |
| _[neuro exec](#neuro-exec)_| Execute command in a running job |
| _[neuro port-forward](#neuro-port-forward)_| Forward port\(s) of a running job to local port\(s) |
| _[neuro logs](#neuro-logs)_| Print the logs for a container |
| _[neuro kill](#neuro-kill)_| Kill job\(s) |
| _[neuro top](#neuro-top)_| Display GPU/CPU/Memory usage |
| _[neuro login](#neuro-login)_| Log into Neuromation Platform |
| _[neuro logout](#neuro-logout)_| Log out |
| _[neuro cp](#neuro-cp)_| Copy files and directories |
| _[neuro ls](#neuro-ls)_| List directory contents |
| _[neuro rm](#neuro-rm)_| Remove files or directories |
| _[neuro mkdir](#neuro-mkdir)_| Make directories |
| _[neuro mv](#neuro-mv)_| Move or rename files and directories |
| _[neuro images](#neuro-images)_| List images |
| _[neuro push](#neuro-push)_| Push an image to platform registry |
| _[neuro pull](#neuro-pull)_| Pull an image from platform registry |
| _[neuro share](#neuro-share)_| Shares resource specified by URI to a USER with PERMISSION Examples: neuro acl... |




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
| _[neuro job run](#neuro-job-run)_| Run an image with predefined configuration |
| _[neuro job submit](#neuro-job-submit)_| Submit an image to run on the cluster |
| _[neuro job ls](#neuro-job-ls)_| List all jobs |
| _[neuro job status](#neuro-job-status)_| Display status of a job |
| _[neuro job exec](#neuro-job-exec)_| Execute command in a running job |
| _[neuro job port-forward](#neuro-job-port-forward)_| Forward port\(s) of a running job to local port\(s) |
| _[neuro job logs](#neuro-job-logs)_| Print the logs for a container |
| _[neuro job kill](#neuro-job-kill)_| Kill job\(s) |
| _[neuro job top](#neuro-job-top)_| Display GPU/CPU/Memory usage |
| _[neuro job browse](#neuro-job-browse)_| Opens a job's URL in a web browser |




### neuro job run

Run an image with predefined configuration.<br/><br/>IMAGE container image name.<br/><br/>CMD list will be passed as commands to model container.<br/>

**Usage:**

```bash
neuro job run [OPTIONS] IMAGE [CMD]...
```

**Examples:**

```bash

# Starts a container pytorch:latest with two paths mounted.
# Directory storage://<USERNAME> is mounted as /var/storage/home in read-write mode,
# storage://neuromation is mounted as :/var/storage/neuromation as read-only.
neuro run pytorch:latest --volume=HOME

```

**Options:**

Name | Description|
|----|------------|
|_\-s, --preset PRESET_|Predefined job profile|
|_\-x, --extshm / -X, --no-extshm_|Request extended '/dev/shm' space  \[default: True]|
|_--http PORT_|Enable HTTP port forwarding to container  \[default: 80]|
|_\--http-auth / --no-http-auth_|Enable HTTP authentication for forwarded HTTP port  \[default: True]|
|_\-p, --preemptible / -P, --non-preemptible_|Run job on a lower-cost preemptible instance  \[default: False]|
|_\-n, --name NAME_|Optional job name|
|_\-d, --description DESC_|Add optional description in free format|
|_\-q, --quiet_|Run command in quiet mode \(DEPRECATED)|
|_\-v, --volume MOUNT_|Mounts directory from vault into container. Use multiple options to mount more than one volume. --volume=HOME is an alias for storage://~:/var/storage/home:rw and storage://neuromation:/var/storage/neuromation:ro|
|_\-e, --env VAR=VAL_|Set environment variable in container Use multiple options to define more than one variable|
|_\--env-file PATH_|File with environment variables to pass|
|_\--wait-start / --no-wait-start_|Wait for a job start or failure  \[default: True]|
|_\--pass-config / --no-pass-config_|Upload neuro config to the job  \[default: False]|
|_--browse_|Open a job's URL in a web browser|
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

```

**Options:**

Name | Description|
|----|------------|
|_\-g, --gpu NUMBER_|Number of GPUs to request  \[default: 0]|
|_\--gpu-model MODEL_|GPU to use  \[default: nvidia\-tesla-k80]|
|_\-c, --cpu NUMBER_|Number of CPUs to request  \[default: 0.1]|
|_\-m, --memory AMOUNT_|Memory amount to request  \[default: 1G]|
|_\-x, --extshm / -X, --no-extshm_|Request extended '/dev/shm' space  \[default: True]|
|_--http PORT_|Enable HTTP port forwarding to container|
|_\--http-auth / --no-http-auth_|Enable HTTP authentication for forwarded HTTP port  \[default: True]|
|_\-p, --preemptible / -P, --non-preemptible_|Run job on a lower-cost preemptible instance  \[default: False]|
|_\-n, --name NAME_|Optional job name|
|_\-d, --description DESC_|Optional job description in free format|
|_\-q, --quiet_|Run command in quiet mode \(DEPRECATED)|
|_\-v, --volume MOUNT_|Mounts directory from vault into container. Use multiple options to mount more than one volume. --volume=HOME is an alias for storage://~:/var/storage/home:rw and storage://neuromation:/var/storage/neuromation:ro|
|_\-e, --env VAR=VAL_|Set environment variable in container Use multiple options to define more than one variable|
|_\--env-file PATH_|File with environment variables to pass|
|_\--wait-start / --no-wait-start_|Wait for a job start or failure  \[default: True]|
|_\--pass-config / --no-pass-config_|Upload neuro config to the job  \[default: False]|
|_--browse_|Open a job's URL in a web browser|
|_--help_|Show this message and exit.|




### neuro job ls

List all jobs.<br/>

**Usage:**

```bash
neuro job ls [OPTIONS]
```

**Examples:**

```bash

neuro ps --name my-experiments-v1 --status all
neuro ps --description=my favourite job
neuro ps -s failed -s succeeded -q

```

**Options:**

Name | Description|
|----|------------|
|_\-s, --status \[pending &#124; running &#124; succeeded &#124; failed &#124; all]_|Filter out job by status \(multiple option)|
|_\-n, --name NAME_|Filter out jobs by name|
|_\-d, --description DESCRIPTION_|Filter out jobs by description \(exact match)|
|_\-q, --quiet_|Run command in quiet mode \(DEPRECATED)|
|_\-w, --wide_|Do not cut long lines for terminal width|
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
|_--help_|Show this message and exit.|




### neuro job exec

Execute command in a running job.

**Usage:**

```bash
neuro job exec [OPTIONS] JOB CMD...
```

**Options:**

Name | Description|
|----|------------|
|_\-t, --tty_|Allocate virtual tty. Useful for interactive jobs.|
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
| _[neuro storage rm](#neuro-storage-rm)_| Remove files or directories |
| _[neuro storage mkdir](#neuro-storage-mkdir)_| Make directories |
| _[neuro storage mv](#neuro-storage-mv)_| Move or rename files and directories |




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

```

**Options:**

Name | Description|
|----|------------|
|_\-r, --recursive_|Recursive copy, off by default|
|_\-t, --target-directory DIRECTORY_|Copy all SOURCES into DIRECTORY|
|_\-T, --no-target-directory_|Treat DESTINATION as a normal file|
|_\-p, --progress_|Show progress, off by default|
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
|_\-h, --human-readable_|with -l print human readable sizes \(e.g., 2K, 540M)|
|_-l_|use a long listing format|
|_--sort \[name &#124; size &#124; time]_|sort by given field, default is name|
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

```

**Options:**

Name | Description|
|----|------------|
|_\-r, --recursive_|remove directories and their contents recursively|
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
|_\-t, --target-directory DIRECTORY_|Copy all SOURCES into DIRECTORY|
|_\-T, --no-target-directory_|Treat DESTINATION as a normal file|
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
| _[neuro config login](#neuro-config-login)_| Log into Neuromation Platform |
| _[neuro config login\-with-token](#neuro-config-login-with-token)_| Log into Neuromation Platform with token |
| _[neuro config login-headless](#neuro-config-login-headless)_| Log into Neuromation Platform from non-GUI server environment |
| _[neuro config show](#neuro-config-show)_| Print current settings |
| _[neuro config show-token](#neuro-config-show-token)_| Print current authorization token |
| _[neuro config docker](#neuro-config-docker)_| Configure docker client for working with platform registry |
| _[neuro config logout](#neuro-config-logout)_| Log out |




### neuro config login

Log into Neuromation Platform.<br/><br/>URL is a platform entrypoint URL.

**Usage:**

```bash
neuro config login [OPTIONS] [URL]
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro config login-with-token

Log into Neuromation Platform with token.<br/><br/>TOKEN is authentication token provided by Neuromation administration team.<br/>URL is a platform entrypoint URL.

**Usage:**

```bash
neuro config login-with-token [OPTIONS] TOKEN [URL]
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro config login-headless

Log into Neuromation Platform from non-GUI server environment.<br/><br/>URL is a platform entrypoint URL.<br/><br/>The command works similar to "neuro login" but instead of opening a browser<br/>for performing OAuth registration prints an URL that should be open on guest<br/>host.<br/><br/>Then user inputs a code displayed in a browser after successful login back<br/>in neuro command to finish the login process.

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




### neuro config docker

Configure docker client for working with platform registry

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

ACL operations.

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
| _[neuro acl grant](#neuro-acl-grant)_| Shares resource specified by URI to a USER with PERMISSION Examples: neuro acl... |
| _[neuro acl revoke](#neuro-acl-revoke)_| Revoke from a USER permissions for previously shared resource specified by URI... |
| _[neuro acl list](#neuro-acl-list)_| List resource available to a USER or shared by a USER Examples: neuro acl list... |




### neuro acl grant

Shares resource specified by URI to a USER with PERMISSION<br/>

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

Revoke from a USER permissions for previously shared resource specified by<br/>URI<br/>

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

List resource available to a USER or shared by a USER<br/>

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
|_\-s, --scheme TEXT_|Filter resources by scheme|
|_--shared_|Output the resources shared by the user|
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

Run an image with predefined configuration.<br/><br/>IMAGE container image name.<br/><br/>CMD list will be passed as commands to model container.<br/>

**Usage:**

```bash
neuro run [OPTIONS] IMAGE [CMD]...
```

**Examples:**

```bash

# Starts a container pytorch:latest with two paths mounted.
# Directory storage://<USERNAME> is mounted as /var/storage/home in read-write mode,
# storage://neuromation is mounted as :/var/storage/neuromation as read-only.
neuro run pytorch:latest --volume=HOME

```

**Options:**

Name | Description|
|----|------------|
|_\-s, --preset PRESET_|Predefined job profile|
|_\-x, --extshm / -X, --no-extshm_|Request extended '/dev/shm' space  \[default: True]|
|_--http PORT_|Enable HTTP port forwarding to container  \[default: 80]|
|_\--http-auth / --no-http-auth_|Enable HTTP authentication for forwarded HTTP port  \[default: True]|
|_\-p, --preemptible / -P, --non-preemptible_|Run job on a lower-cost preemptible instance  \[default: False]|
|_\-n, --name NAME_|Optional job name|
|_\-d, --description DESC_|Add optional description in free format|
|_\-q, --quiet_|Run command in quiet mode \(DEPRECATED)|
|_\-v, --volume MOUNT_|Mounts directory from vault into container. Use multiple options to mount more than one volume. --volume=HOME is an alias for storage://~:/var/storage/home:rw and storage://neuromation:/var/storage/neuromation:ro|
|_\-e, --env VAR=VAL_|Set environment variable in container Use multiple options to define more than one variable|
|_\--env-file PATH_|File with environment variables to pass|
|_\--wait-start / --no-wait-start_|Wait for a job start or failure  \[default: True]|
|_\--pass-config / --no-pass-config_|Upload neuro config to the job  \[default: False]|
|_--browse_|Open a job's URL in a web browser|
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

```

**Options:**

Name | Description|
|----|------------|
|_\-g, --gpu NUMBER_|Number of GPUs to request  \[default: 0]|
|_\--gpu-model MODEL_|GPU to use  \[default: nvidia\-tesla-k80]|
|_\-c, --cpu NUMBER_|Number of CPUs to request  \[default: 0.1]|
|_\-m, --memory AMOUNT_|Memory amount to request  \[default: 1G]|
|_\-x, --extshm / -X, --no-extshm_|Request extended '/dev/shm' space  \[default: True]|
|_--http PORT_|Enable HTTP port forwarding to container|
|_\--http-auth / --no-http-auth_|Enable HTTP authentication for forwarded HTTP port  \[default: True]|
|_\-p, --preemptible / -P, --non-preemptible_|Run job on a lower-cost preemptible instance  \[default: False]|
|_\-n, --name NAME_|Optional job name|
|_\-d, --description DESC_|Optional job description in free format|
|_\-q, --quiet_|Run command in quiet mode \(DEPRECATED)|
|_\-v, --volume MOUNT_|Mounts directory from vault into container. Use multiple options to mount more than one volume. --volume=HOME is an alias for storage://~:/var/storage/home:rw and storage://neuromation:/var/storage/neuromation:ro|
|_\-e, --env VAR=VAL_|Set environment variable in container Use multiple options to define more than one variable|
|_\--env-file PATH_|File with environment variables to pass|
|_\--wait-start / --no-wait-start_|Wait for a job start or failure  \[default: True]|
|_\--pass-config / --no-pass-config_|Upload neuro config to the job  \[default: False]|
|_--browse_|Open a job's URL in a web browser|
|_--help_|Show this message and exit.|




## neuro ps

List all jobs.<br/>

**Usage:**

```bash
neuro ps [OPTIONS]
```

**Examples:**

```bash

neuro ps --name my-experiments-v1 --status all
neuro ps --description=my favourite job
neuro ps -s failed -s succeeded -q

```

**Options:**

Name | Description|
|----|------------|
|_\-s, --status \[pending &#124; running &#124; succeeded &#124; failed &#124; all]_|Filter out job by status \(multiple option)|
|_\-n, --name NAME_|Filter out jobs by name|
|_\-d, --description DESCRIPTION_|Filter out jobs by description \(exact match)|
|_\-q, --quiet_|Run command in quiet mode \(DEPRECATED)|
|_\-w, --wide_|Do not cut long lines for terminal width|
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
|_--help_|Show this message and exit.|




## neuro exec

Execute command in a running job.

**Usage:**

```bash
neuro exec [OPTIONS] JOB CMD...
```

**Options:**

Name | Description|
|----|------------|
|_\-t, --tty_|Allocate virtual tty. Useful for interactive jobs.|
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
|_--help_|Show this message and exit.|




## neuro login

Log into Neuromation Platform.<br/><br/>URL is a platform entrypoint URL.

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

```

**Options:**

Name | Description|
|----|------------|
|_\-r, --recursive_|Recursive copy, off by default|
|_\-t, --target-directory DIRECTORY_|Copy all SOURCES into DIRECTORY|
|_\-T, --no-target-directory_|Treat DESTINATION as a normal file|
|_\-p, --progress_|Show progress, off by default|
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
|_\-h, --human-readable_|with -l print human readable sizes \(e.g., 2K, 540M)|
|_-l_|use a long listing format|
|_--sort \[name &#124; size &#124; time]_|sort by given field, default is name|
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

```

**Options:**

Name | Description|
|----|------------|
|_\-r, --recursive_|remove directories and their contents recursively|
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

Shares resource specified by URI to a USER with PERMISSION<br/>

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
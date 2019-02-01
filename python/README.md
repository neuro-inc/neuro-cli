[![codecov](https://codecov.io/gh/neuromation/platform-api-clients/branch/master/graph/badge.svg?token=FwM6ZV3gDj)](https://codecov.io/gh/neuromation/platform-api-clients)

# Table of Contents
* [Preface](#Preface)
* [neuro](#neuro)
	* [neuro help](#neuro-help)
	* [neuro job](#neuro-job)
		* [neuro job submit](#neuro-job-submit)
		* [neuro job ls](#neuro-job-ls)
		* [neuro job status](#neuro-job-status)
		* [neuro job exec](#neuro-job-exec)
		* [neuro job logs](#neuro-job-logs)
		* [neuro job kill](#neuro-job-kill)
		* [neuro job top](#neuro-job-top)
		* [neuro job list](#neuro-job-list)
		* [neuro job monitor](#neuro-job-monitor)
		* [neuro job ssh](#neuro-job-ssh)
	* [neuro storage](#neuro-storage)
		* [neuro storage rm](#neuro-storage-rm)
		* [neuro storage ls](#neuro-storage-ls)
		* [neuro storage cp](#neuro-storage-cp)
		* [neuro storage mkdir](#neuro-storage-mkdir)
		* [neuro storage mv](#neuro-storage-mv)
	* [neuro image](#neuro-image)
		* [neuro image push](#neuro-image-push)
		* [neuro image pull](#neuro-image-pull)
		* [neuro image ls](#neuro-image-ls)
	* [neuro config](#neuro-config)
		* [neuro config url](#neuro-config-url)
		* [neuro config id_rsa](#neuro-config-id_rsa)
		* [neuro config show](#neuro-config-show)
		* [neuro config show-token](#neuro-config-show-token)
		* [neuro config auth](#neuro-config-auth)
		* [neuro config forget](#neuro-config-forget)
		* [neuro config login](#neuro-config-login)
		* [neuro config logout](#neuro-config-logout)
	* [neuro completion](#neuro-completion)
		* [neuro completion generate](#neuro-completion-generate)
		* [neuro completion patch](#neuro-completion-patch)
	* [neuro model](#neuro-model)
		* [neuro model train](#neuro-model-train)
		* [neuro model debug](#neuro-model-debug)
	* [neuro store](#neuro-store)
		* [neuro store rm](#neuro-store-rm)
		* [neuro store ls](#neuro-store-ls)
		* [neuro store cp](#neuro-store-cp)
		* [neuro store mkdir](#neuro-store-mkdir)
		* [neuro store mv](#neuro-store-mv)
	* [neuro submit](#neuro-submit)
	* [neuro ps](#neuro-ps)
	* [neuro status](#neuro-status)
	* [neuro exec](#neuro-exec)
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
* [Manipulate Data](#neuro-store)
* Make some fun

# neuro

**Usage:**

```bash
neuro [OPTIONS] COMMAND [ARGS]...
```

**Options:**

Name | Description|
|----|------------|
|_\-v, --verbose_||
|_\--show-traceback_||
|_--version_|Show the version and exit.|
|_--help_|Show this message and exit.|


**Commands:**

* _[neuro help](#neuro-help)_: Get help on a command.
* _[neuro job](#neuro-job)_: Job operations.
* _[neuro storage](#neuro-storage)_: Storage operations.
* _[neuro image](#neuro-image)_: Container image operations.
* _[neuro config](#neuro-config)_: Client configuration.
* _[neuro completion](#neuro-completion)_: Output shell completion code.
* _[neuro model](#neuro-model)_: Model operations. (DEPRECATED)
* _[neuro store](#neuro-store)_: Alias for storage (DEPRECATED)
* _[neuro submit](#neuro-submit)_: Submit an image to run on the cluster.

IMAGE container image name COMMANDS list will be passed as commands to model
container.

* _[neuro ps](#neuro-ps)_: List all jobs.

* _[neuro status](#neuro-status)_: Display status of a job.
* _[neuro exec](#neuro-exec)_: Execute command in a running job.
* _[neuro logs](#neuro-logs)_: Print the logs for a container.
* _[neuro kill](#neuro-kill)_: Kill job(s).
* _[neuro top](#neuro-top)_: Display GPU/CPU/Memory usage.
* _[neuro login](#neuro-login)_: Log into Neuromation Platform.
* _[neuro logout](#neuro-logout)_: Log out.
* _[neuro cp](#neuro-cp)_: Copy files and directories.

Either SOURCE or DESTINATION should have storage:// scheme. If scheme is
omitted, file:// scheme is assumed.

* _[neuro ls](#neuro-ls)_: List directory contents.

By default PATH is equal user`s home dir (storage:)
* _[neuro rm](#neuro-rm)_: Remove files or directories.

* _[neuro mkdir](#neuro-mkdir)_: Make directories.
* _[neuro mv](#neuro-mv)_: Move or rename files and directories.

SOURCE must contain path to the file or directory existing on the storage,
and DESTINATION must contain the full path to the target file or directory.

* _[neuro images](#neuro-images)_: List images.
* _[neuro push](#neuro-push)_: Push an image to platform registry.

Remote image must be URL with image:// scheme. Image names can contains tag.
If tags not specified 'latest' will be used as value.

* _[neuro pull](#neuro-pull)_: Pull an image from platform registry.

Remote image name must be URL with image:// scheme. Image names can contain
tag.

* _[neuro share](#neuro-share)_: Shares resource specified by URI to a USER with PERMISSION





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

* _[neuro job submit](#neuro-job-submit)_: Submit an image to run on the cluster.

IMAGE container image name COMMANDS list will be passed as commands to model
container.

* _[neuro job ls](#neuro-job-ls)_: List all jobs.

* _[neuro job status](#neuro-job-status)_: Display status of a job.
* _[neuro job exec](#neuro-job-exec)_: Execute command in a running job.
* _[neuro job logs](#neuro-job-logs)_: Print the logs for a container.
* _[neuro job kill](#neuro-job-kill)_: Kill job(s).
* _[neuro job top](#neuro-job-top)_: Display GPU/CPU/Memory usage.
* _[neuro job list](#neuro-job-list)_: Alias for ls. (DEPRECATED)
* _[neuro job monitor](#neuro-job-monitor)_: Alias for logs. (DEPRECATED)
* _[neuro job ssh](#neuro-job-ssh)_: Starts ssh terminal connected to running job.

Job should be started with SSH support enabled.

 (DEPRECATED)





### neuro job submit

Submit an image to run on the cluster.<br/><br/>IMAGE container image name COMMANDS list will be passed as commands to model<br/>container.<br/>

**Usage:**

```bash
neuro job submit [OPTIONS] IMAGE [CMD]...
```

**Examples:**

```bash

# Starts a container pytorch:latest with two paths mounted. Directory /q1/
# is mounted in read only mode to /qm directory within container.
# Directory /mod mounted to /mod directory in read-write mode.
neuro job submit --volume storage:/q1:/qm:ro --volume storage:/mod:/mod:rw pytorch:latest

# Starts a container pytorch:latest with connection enabled to port 22 and
# sets PYTHONPATH environment value to /python.
# Please note that SSH server should be provided by container.
neuro job submit --env PYTHONPATH=/python --volume storage:/data/2018q1:/data:ro --ssh 22 pytorch:latest

```

**Options:**

Name | Description|
|----|------------|
|_\-g, --gpu NUMBER_|Number of GPUs to request  \[default: 0]|
|_\--gpu-model MODEL_|GPU to use  \[default: nvidia\-tesla-k80]|
|_\-c, --cpu NUMBER_|Number of CPUs to request  \[default: 0.1]|
|_\-m, --memory AMOUNT_|Memory amount to request  \[default: 1G]|
|_\-x, --extshm_|Request extended '/dev/shm' space|
|_--http INTEGER_|Enable HTTP port forwarding to container|
|_--ssh INTEGER_|Enable SSH port forwarding to container|
|_\--preemptible / --non-preemptible_|Run job on a lower-cost preemptible instance|
|_\-d, --description DESC_|Add optional description to the job|
|_\-q, --quiet_|Run command in quiet mode \(print only job id)|
|_--volume MOUNT_|Mounts directory from vault into container. Use multiple options to mount more than one volume|
|_\-e, --env VAR=VAL_|Set environment variable in container Use multiple options to define more than one variable|
|_\--env-file PATH_|File with environment variables to pass|
|_--help_|Show this message and exit.|




### neuro job ls

List all jobs.<br/>

**Usage:**

```bash
neuro job ls [OPTIONS]
```

**Examples:**

```bash

neuro job list --description=my favourite job
neuro job list --status=all
neuro job list -s pending -s running -q

```

**Options:**

Name | Description|
|----|------------|
|_\-s, --status \[pending|running|succeeded|failed|all]_|Filter out job by status \(multiple option)|
|_\-d, --description DESCRIPTION_|Filter out job by job description \(exact match)|
|_\-q, --quiet_||
|_--help_|Show this message and exit.|




### neuro job status

Display status of a job.

**Usage:**

```bash
neuro job status [OPTIONS] ID
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro job exec

Execute command in a running job.

**Usage:**

```bash
neuro job exec [OPTIONS] ID CMD...
```

**Options:**

Name | Description|
|----|------------|
|_\-t, --tty_|Allocate virtual tty. Useful for interactive jobs.|
|_\--no-key-check_|Disable host key checks. Should be used with caution.|
|_--help_|Show this message and exit.|




### neuro job logs

Print the logs for a container.

**Usage:**

```bash
neuro job logs [OPTIONS] ID
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro job kill

Kill job\(s).

**Usage:**

```bash
neuro job kill [OPTIONS] ID...
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro job top

Display GPU/CPU/Memory usage.

**Usage:**

```bash
neuro job top [OPTIONS] ID
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro job list

Alias for ls. \(DEPRECATED)

**Usage:**

```bash
neuro job list [OPTIONS]
```

**Options:**

Name | Description|
|----|------------|
|_\-s, --status \[pending|running|succeeded|failed|all]_|Filter out job by status \(multiple option)|
|_\-d, --description DESCRIPTION_|Filter out job by job description \(exact match)|
|_\-q, --quiet_||
|_--help_|Show this message and exit.|




### neuro job monitor

Alias for logs. \(DEPRECATED)

**Usage:**

```bash
neuro job monitor [OPTIONS] ID
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro job ssh

Starts ssh terminal connected to running job.<br/><br/>Job should be started with SSH support enabled.<br/><br/> \(DEPRECATED)<br/>

**Usage:**

```bash
neuro job ssh [OPTIONS] ID
```

**Examples:**

```bash

neuro job ssh --user alfa --key ./my_docker_id_rsa job-abc-def-ghk

```

**Options:**

Name | Description|
|----|------------|
|_--user TEXT_|Container user name  \[default: root]|
|_--key TEXT_|Path to container private key.|
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

* _[neuro storage rm](#neuro-storage-rm)_: Remove files or directories.

* _[neuro storage ls](#neuro-storage-ls)_: List directory contents.

By default PATH is equal user`s home dir (storage:)
* _[neuro storage cp](#neuro-storage-cp)_: Copy files and directories.

Either SOURCE or DESTINATION should have storage:// scheme. If scheme is
omitted, file:// scheme is assumed.

* _[neuro storage mkdir](#neuro-storage-mkdir)_: Make directories.
* _[neuro storage mv](#neuro-storage-mv)_: Move or rename files and directories.

SOURCE must contain path to the file or directory existing on the storage,
and DESTINATION must contain the full path to the target file or directory.





### neuro storage rm

Remove files or directories.<br/>

**Usage:**

```bash
neuro storage rm [OPTIONS] PATH
```

**Examples:**

```bash

neuro storage rm storage:///foo/bar/
neuro storage rm storage:/foo/bar/
neuro storage rm storage://{username}/foo/bar/

```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro storage ls

List directory contents.<br/><br/>By default PATH is equal user`s home dir \(storage:)

**Usage:**

```bash
neuro storage ls [OPTIONS] [PATH]
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro storage cp

Copy files and directories.<br/><br/>Either SOURCE or DESTINATION should have storage:// scheme. If scheme is<br/>omitted, file:// scheme is assumed.<br/>

**Usage:**

```bash
neuro storage cp [OPTIONS] SOURCE DESTINATION
```

**Examples:**

```bash

# copy local file ./foo into remote storage root
neuro storage cp ./foo storage:///
neuro storage cp ./foo storage:/

# download remote file foo into local file foo with
# explicit file:// scheme set
neuro storage cp storage:///foo file:///foo

```

**Options:**

Name | Description|
|----|------------|
|_\-r, --recursive_|Recursive copy, off by default|
|_\-p, --progress_|Show progress, off by default|
|_--help_|Show this message and exit.|




### neuro storage mkdir

Make directories.

**Usage:**

```bash
neuro storage mkdir [OPTIONS] PATH
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro storage mv

Move or rename files and directories.<br/><br/>SOURCE must contain path to the file or directory existing on the storage,<br/>and DESTINATION must contain the full path to the target file or directory.<br/>

**Usage:**

```bash
neuro storage mv [OPTIONS] SOURCE DESTINATION
```

**Examples:**

```bash

# move or rename remote file
neuro storage mv storage://{username}/foo.txt storage://{username}/bar.txt
neuro storage mv storage://{username}/foo.txt storage://~/bar/baz/foo.txt

# move or rename remote directory
neuro storage mv storage://{username}/foo/ storage://{username}/bar/
neuro storage mv storage://{username}/foo/ storage://{username}/bar/baz/foo/

```

**Options:**

Name | Description|
|----|------------|
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

* _[neuro image push](#neuro-image-push)_: Push an image to platform registry.

Remote image must be URL with image:// scheme. Image names can contains tag.
If tags not specified 'latest' will be used as value.

* _[neuro image pull](#neuro-image-pull)_: Pull an image from platform registry.

Remote image name must be URL with image:// scheme. Image names can contain
tag.

* _[neuro image ls](#neuro-image-ls)_: List images.




### neuro image push

Push an image to platform registry.<br/><br/>Remote image must be URL with image:// scheme. Image names can contains tag.<br/>If tags not specified 'latest' will be used as value.<br/>

**Usage:**

```bash
neuro image push [OPTIONS] IMAGE_NAME [REMOTE_IMAGE_NAME]
```

**Examples:**

```bash

neuro image push myimage
neuro image push alpine:latest image:my-alpine:production
neuro image push alpine image://myfriend/alpine:shared

```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro image pull

Pull an image from platform registry.<br/><br/>Remote image name must be URL with image:// scheme. Image names can contain<br/>tag.<br/>

**Usage:**

```bash
neuro image pull [OPTIONS] IMAGE_NAME [LOCAL_IMAGE_NAME]
```

**Examples:**

```bash

neuro image pull image:myimage
neuro image pull image://myfriend/alpine:shared
neuro image pull image://username/my-alpine:production alpine:from-registry

```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




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

* _[neuro config url](#neuro-config-url)_: Update settings with provided platform URL.

* _[neuro config id_rsa](#neuro-config-id_rsa)_: Update path to id_rsa file with private key.

FILE is being used for accessing remote shell, remote debug.

Note: this is temporal and going to be replaced in future by JWT token.
* _[neuro config show](#neuro-config-show)_: Print current settings.
* _[neuro config show-token](#neuro-config-show-token)_: Print current authorization token.
* _[neuro config auth](#neuro-config-auth)_: Update authorization token.
* _[neuro config forget](#neuro-config-forget)_: Forget authorization token. (DEPRECATED)
* _[neuro config login](#neuro-config-login)_: Log into Neuromation Platform.
* _[neuro config logout](#neuro-config-logout)_: Log out.




### neuro config url

Update settings with provided platform URL.<br/>

**Usage:**

```bash
neuro config url [OPTIONS] URL
```

**Examples:**

```bash

neuro config url https://platform.neuromation.io/api/v1

```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro config id_rsa

Update path to id_rsa file with private key.<br/><br/>FILE is being used for accessing remote shell, remote debug.<br/><br/>Note: this is temporal and going to be replaced in future by JWT token.

**Usage:**

```bash
neuro config id_rsa [OPTIONS] FILE
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




### neuro config auth

Update authorization token.

**Usage:**

```bash
neuro config auth [OPTIONS] TOKEN
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro config forget

Forget authorization token. \(DEPRECATED)

**Usage:**

```bash
neuro config forget [OPTIONS]
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro config login

Log into Neuromation Platform.

**Usage:**

```bash
neuro config login [OPTIONS] [URL]
```

**Options:**

Name | Description|
|----|------------|
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

* _[neuro completion generate](#neuro-completion-generate)_: Provide an instruction for shell completion generation.
* _[neuro completion patch](#neuro-completion-patch)_: Automatically patch shell configuration profile to enable completion




### neuro completion generate

Provide an instruction for shell completion generation.

**Usage:**

```bash
neuro completion generate [OPTIONS]
```

**Options:**

Name | Description|
|----|------------|
|_--shell \[bash|zsh]_|Shell type.  \[default: bash]|
|_--help_|Show this message and exit.|




### neuro completion patch

Automatically patch shell configuration profile to enable completion

**Usage:**

```bash
neuro completion patch [OPTIONS]
```

**Options:**

Name | Description|
|----|------------|
|_--shell \[bash|zsh]_|Shell type.  \[default: bash]|
|_--help_|Show this message and exit.|




## neuro model

Model operations. \(DEPRECATED)

**Usage:**

```bash
neuro model [OPTIONS] COMMAND [ARGS]...
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|


**Commands:**

* _[neuro model train](#neuro-model-train)_: Start training job using model.

The training job is created from IMAGE, dataset from DATASET and store
output weights in RESULTS.

COMMANDS list will be passed as commands to model container.
* _[neuro model debug](#neuro-model-debug)_: Starts ssh terminal connected to running job.

Job should be started with SSH support enabled.





### neuro model train

Start training job using model.<br/><br/>The training job is created from IMAGE, dataset from DATASET and store<br/>output weights in RESULTS.<br/><br/>COMMANDS list will be passed as commands to model container.

**Usage:**

```bash
neuro model train [OPTIONS] IMAGE DATASET RESULTS [CMD]...
```

**Options:**

Name | Description|
|----|------------|
|_\-g, --gpu NUMBER_|Number of GPUs to request  \[default: 0]|
|_\--gpu-model MODEL_|GPU to use  \[default: nvidia\-tesla-k80]|
|_\-c, --cpu NUMBER_|Number of CPUs to request  \[default: 0.1]|
|_\-m, --memory AMOUNT_|Memory amount to request  \[default: 1G]|
|_\-x, --extshm_|Request extended '/dev/shm' space|
|_--http INTEGER_|Enable HTTP port forwarding to container|
|_--ssh INTEGER_|Enable SSH port forwarding to container|
|_\--preemptible / --non-preemptible_|Run job on a lower-cost preemptible instance|
|_\-d, --description DESC_|Add optional description to the job|
|_\-q, --quiet_|Run command in quiet mode \(print only job id)|
|_--help_|Show this message and exit.|




### neuro model debug

Starts ssh terminal connected to running job.<br/><br/>Job should be started with SSH support enabled.<br/>

**Usage:**

```bash
neuro model debug [OPTIONS] ID
```

**Examples:**

```bash

neuro model debug --localport 12789 job-abc-def-ghk

```

**Options:**

Name | Description|
|----|------------|
|_--localport INTEGER_|Local port number for debug  \[default: 31234]|
|_--help_|Show this message and exit.|




## neuro store

Alias for storage \(DEPRECATED)

**Usage:**

```bash
neuro store [OPTIONS] COMMAND [ARGS]...
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|


**Commands:**

* _[neuro store rm](#neuro-store-rm)_: Remove files or directories.

* _[neuro store ls](#neuro-store-ls)_: List directory contents.

By default PATH is equal user`s home dir (storage:)
* _[neuro store cp](#neuro-store-cp)_: Copy files and directories.

Either SOURCE or DESTINATION should have storage:// scheme. If scheme is
omitted, file:// scheme is assumed.

* _[neuro store mkdir](#neuro-store-mkdir)_: Make directories.
* _[neuro store mv](#neuro-store-mv)_: Move or rename files and directories.

SOURCE must contain path to the file or directory existing on the storage,
and DESTINATION must contain the full path to the target file or directory.





### neuro store rm

Remove files or directories.<br/>

**Usage:**

```bash
neuro store rm [OPTIONS] PATH
```

**Examples:**

```bash

neuro storage rm storage:///foo/bar/
neuro storage rm storage:/foo/bar/
neuro storage rm storage://{username}/foo/bar/

```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro store ls

List directory contents.<br/><br/>By default PATH is equal user`s home dir \(storage:)

**Usage:**

```bash
neuro store ls [OPTIONS] [PATH]
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro store cp

Copy files and directories.<br/><br/>Either SOURCE or DESTINATION should have storage:// scheme. If scheme is<br/>omitted, file:// scheme is assumed.<br/>

**Usage:**

```bash
neuro store cp [OPTIONS] SOURCE DESTINATION
```

**Examples:**

```bash

# copy local file ./foo into remote storage root
neuro storage cp ./foo storage:///
neuro storage cp ./foo storage:/

# download remote file foo into local file foo with
# explicit file:// scheme set
neuro storage cp storage:///foo file:///foo

```

**Options:**

Name | Description|
|----|------------|
|_\-r, --recursive_|Recursive copy, off by default|
|_\-p, --progress_|Show progress, off by default|
|_--help_|Show this message and exit.|




### neuro store mkdir

Make directories.

**Usage:**

```bash
neuro store mkdir [OPTIONS] PATH
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro store mv

Move or rename files and directories.<br/><br/>SOURCE must contain path to the file or directory existing on the storage,<br/>and DESTINATION must contain the full path to the target file or directory.<br/>

**Usage:**

```bash
neuro store mv [OPTIONS] SOURCE DESTINATION
```

**Examples:**

```bash

# move or rename remote file
neuro storage mv storage://{username}/foo.txt storage://{username}/bar.txt
neuro storage mv storage://{username}/foo.txt storage://~/bar/baz/foo.txt

# move or rename remote directory
neuro storage mv storage://{username}/foo/ storage://{username}/bar/
neuro storage mv storage://{username}/foo/ storage://{username}/bar/baz/foo/

```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




## neuro submit

Submit an image to run on the cluster.<br/><br/>IMAGE container image name COMMANDS list will be passed as commands to model<br/>container.<br/>

**Usage:**

```bash
neuro submit [OPTIONS] IMAGE [CMD]...
```

**Examples:**

```bash

# Starts a container pytorch:latest with two paths mounted. Directory /q1/
# is mounted in read only mode to /qm directory within container.
# Directory /mod mounted to /mod directory in read-write mode.
neuro job submit --volume storage:/q1:/qm:ro --volume storage:/mod:/mod:rw pytorch:latest

# Starts a container pytorch:latest with connection enabled to port 22 and
# sets PYTHONPATH environment value to /python.
# Please note that SSH server should be provided by container.
neuro job submit --env PYTHONPATH=/python --volume storage:/data/2018q1:/data:ro --ssh 22 pytorch:latest

```

**Options:**

Name | Description|
|----|------------|
|_\-g, --gpu NUMBER_|Number of GPUs to request  \[default: 0]|
|_\--gpu-model MODEL_|GPU to use  \[default: nvidia\-tesla-k80]|
|_\-c, --cpu NUMBER_|Number of CPUs to request  \[default: 0.1]|
|_\-m, --memory AMOUNT_|Memory amount to request  \[default: 1G]|
|_\-x, --extshm_|Request extended '/dev/shm' space|
|_--http INTEGER_|Enable HTTP port forwarding to container|
|_--ssh INTEGER_|Enable SSH port forwarding to container|
|_\--preemptible / --non-preemptible_|Run job on a lower-cost preemptible instance|
|_\-d, --description DESC_|Add optional description to the job|
|_\-q, --quiet_|Run command in quiet mode \(print only job id)|
|_--volume MOUNT_|Mounts directory from vault into container. Use multiple options to mount more than one volume|
|_\-e, --env VAR=VAL_|Set environment variable in container Use multiple options to define more than one variable|
|_\--env-file PATH_|File with environment variables to pass|
|_--help_|Show this message and exit.|




## neuro ps

List all jobs.<br/>

**Usage:**

```bash
neuro ps [OPTIONS]
```

**Examples:**

```bash

neuro job list --description=my favourite job
neuro job list --status=all
neuro job list -s pending -s running -q

```

**Options:**

Name | Description|
|----|------------|
|_\-s, --status \[pending|running|succeeded|failed|all]_|Filter out job by status \(multiple option)|
|_\-d, --description DESCRIPTION_|Filter out job by job description \(exact match)|
|_\-q, --quiet_||
|_--help_|Show this message and exit.|




## neuro status

Display status of a job.

**Usage:**

```bash
neuro status [OPTIONS] ID
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




## neuro exec

Execute command in a running job.

**Usage:**

```bash
neuro exec [OPTIONS] ID CMD...
```

**Options:**

Name | Description|
|----|------------|
|_\-t, --tty_|Allocate virtual tty. Useful for interactive jobs.|
|_\--no-key-check_|Disable host key checks. Should be used with caution.|
|_--help_|Show this message and exit.|




## neuro logs

Print the logs for a container.

**Usage:**

```bash
neuro logs [OPTIONS] ID
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




## neuro kill

Kill job\(s).

**Usage:**

```bash
neuro kill [OPTIONS] ID...
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




## neuro top

Display GPU/CPU/Memory usage.

**Usage:**

```bash
neuro top [OPTIONS] ID
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




## neuro login

Log into Neuromation Platform.

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

Copy files and directories.<br/><br/>Either SOURCE or DESTINATION should have storage:// scheme. If scheme is<br/>omitted, file:// scheme is assumed.<br/>

**Usage:**

```bash
neuro cp [OPTIONS] SOURCE DESTINATION
```

**Examples:**

```bash

# copy local file ./foo into remote storage root
neuro storage cp ./foo storage:///
neuro storage cp ./foo storage:/

# download remote file foo into local file foo with
# explicit file:// scheme set
neuro storage cp storage:///foo file:///foo

```

**Options:**

Name | Description|
|----|------------|
|_\-r, --recursive_|Recursive copy, off by default|
|_\-p, --progress_|Show progress, off by default|
|_--help_|Show this message and exit.|




## neuro ls

List directory contents.<br/><br/>By default PATH is equal user`s home dir \(storage:)

**Usage:**

```bash
neuro ls [OPTIONS] [PATH]
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




## neuro rm

Remove files or directories.<br/>

**Usage:**

```bash
neuro rm [OPTIONS] PATH
```

**Examples:**

```bash

neuro storage rm storage:///foo/bar/
neuro storage rm storage:/foo/bar/
neuro storage rm storage://{username}/foo/bar/

```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




## neuro mkdir

Make directories.

**Usage:**

```bash
neuro mkdir [OPTIONS] PATH
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




## neuro mv

Move or rename files and directories.<br/><br/>SOURCE must contain path to the file or directory existing on the storage,<br/>and DESTINATION must contain the full path to the target file or directory.<br/>

**Usage:**

```bash
neuro mv [OPTIONS] SOURCE DESTINATION
```

**Examples:**

```bash

# move or rename remote file
neuro storage mv storage://{username}/foo.txt storage://{username}/bar.txt
neuro storage mv storage://{username}/foo.txt storage://~/bar/baz/foo.txt

# move or rename remote directory
neuro storage mv storage://{username}/foo/ storage://{username}/bar/
neuro storage mv storage://{username}/foo/ storage://{username}/bar/baz/foo/

```

**Options:**

Name | Description|
|----|------------|
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

Push an image to platform registry.<br/><br/>Remote image must be URL with image:// scheme. Image names can contains tag.<br/>If tags not specified 'latest' will be used as value.<br/>

**Usage:**

```bash
neuro push [OPTIONS] IMAGE_NAME [REMOTE_IMAGE_NAME]
```

**Examples:**

```bash

neuro image push myimage
neuro image push alpine:latest image:my-alpine:production
neuro image push alpine image://myfriend/alpine:shared

```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




## neuro pull

Pull an image from platform registry.<br/><br/>Remote image name must be URL with image:// scheme. Image names can contain<br/>tag.<br/>

**Usage:**

```bash
neuro pull [OPTIONS] IMAGE_NAME [LOCAL_IMAGE_NAME]
```

**Examples:**

```bash

neuro image pull image:myimage
neuro image pull image://myfriend/alpine:shared
neuro image pull image://username/my-alpine:production alpine:from-registry

```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




## neuro share

Shares resource specified by URI to a USER with PERMISSION<br/>

**Usage:**

```bash
neuro share [OPTIONS] URI USER [read|write|manage]
```

**Examples:**

```bash

neuro share storage:///sample_data/ alice manage
neuro share image:resnet50 bob read
neuro share job:///my_job_id alice write

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
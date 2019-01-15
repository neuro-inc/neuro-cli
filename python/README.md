[![codecov](https://codecov.io/gh/neuromation/platform-api-clients/branch/master/graph/badge.svg?token=FwM6ZV3gDj)](https://codecov.io/gh/neuromation/platform-api-clients)

# Table of Contents
* [Preface](#Preface)
* [neuro](#neuro)
	* [neuro model](#neuro-model)
		* [neuro model train](#neuro-model-train)
		* [neuro model debug](#neuro-model-debug)
	* [neuro job](#neuro-job)
		* [neuro job submit](#neuro-job-submit)
		* [neuro job monitor](#neuro-job-monitor)
		* [neuro job list](#neuro-job-list)
		* [neuro job status](#neuro-job-status)
		* [neuro job kill](#neuro-job-kill)
		* [neuro job ssh](#neuro-job-ssh)
	* [neuro store](#neuro-store)
		* [neuro store rm](#neuro-store-rm)
		* [neuro store ls](#neuro-store-ls)
		* [neuro store cp](#neuro-store-cp)
		* [neuro store mv](#neuro-store-mv)
		* [neuro store mkdir](#neuro-store-mkdir)
	* [neuro image](#neuro-image)
		* [neuro image push](#neuro-image-push)
		* [neuro image pull](#neuro-image-pull)
	* [neuro config](#neuro-config)
		* [neuro config url](#neuro-config-url)
		* [neuro config auth](#neuro-config-auth)
		* [neuro config forget](#neuro-config-forget)
		* [neuro config id_rsa](#neuro-config-id_rsa)
		* [neuro config show](#neuro-config-show)
	* [neuro completion](#neuro-completion)
		* [neuro completion generate](#neuro-completion-generate)
		* [neuro completion patch](#neuro-completion-patch)
	* [neuro share](#neuro-share)
	* [neuro help](#neuro-help)
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
neuro [options] COMMAND
```

**Options:**

Name | Description|
|----|------------|
|_\-u, --url URL_|Override API URL \[default: https://platform.dev.neuromation.io/api/v1]|
|_\-t, --token TOKEN_|API authentication token \(not implemented)|
|_--verbose_|Enable verbose logging|
|_\--show-traceback_|Show Python traceback on exception|
|_\-v, --version_|Print version and exit|


**Commands:**

* _[model](#neuro-model)_: Model training, testing and inference

* _[job](#neuro-job)_: Manage existing jobs

* _[store](#neuro-store)_: Storage operations

* _[image](#neuro-image)_: Docker container image operations

* _[config](#neuro-config)_: Configure API connection settings

* _[completion](#neuro-completion)_: Generate code to enable completion

* _[share](#neuro-share)_: Resource sharing management

* _[help](#neuro-help)_: Get help on a command



## neuro model

Model operations

**Usage:**

```bash
neuro model COMMAND
```

**Commands:**

* _[train](#neuro-model-train)_: Start model training

* _[debug](#neuro-model-debug)_: Prepare debug tunnel for PyCharm



### neuro model train

Start training job using model from IMAGE, dataset from DATASET and<br/>store output weights in RESULTS.<br/>COMMANDS list will be passed as commands to model container.

**Usage:**

```bash
neuro model train [options] IMAGE DATASET RESULTS [CMD...]
```

**Options:**

Name | Description|
|----|------------|
|_\-g, --gpu NUMBER_|Number of GPUs to request \[default: 0]|
|_\--gpu-model MODEL_|GPU to use \[default: nvidia\-tesla-k80]<br/>Other options available are<br/>nvidia\-tesla-k80<br/>nvidia\-tesla-p4<br/>nvidia\-tesla-v100|
|_\-c, --cpu NUMBER_|Number of CPUs to request \[default: 0.1]|
|_\-m, --memory AMOUNT_|Memory amount to request \[default: 1G]|
|_\-x, --extshm_|Request extended '/dev/shm' space|
|_--http NUMBER_|Enable HTTP port forwarding to container|
|_--ssh NUMBER_|Enable SSH port forwarding to container|
|_--preemptible_|Run job on a lower-cost preemptible instance|
|_\--non-preemptible_|Force job to run on a non-preemptible instance|
|_\-d, --description DESC_|Add optional description to the job|
|_\-q, --quiet_|Run command in quiet mode \(print only job id)|




### neuro model debug

Starts ssh terminal connected to running job.<br/>Job should be started with SSH support enabled.

**Usage:**

```bash
neuro model debug [options] ID
```

**Options:**

Name | Description|
|----|------------|
|_--localport NUMBER_|Local port number for debug \[default: 31234]|


**Examples:**

```bash
neuro model debug --localport 12789 job-abc-def-ghk
```



## neuro job

Model operations

**Usage:**

```bash
neuro job COMMAND
```

**Commands:**

* _[submit](#neuro-job-submit)_: Starts Job on a platform

* _[monitor](#neuro-job-monitor)_: Monitor job output stream

* _[list](#neuro-job-list)_: List all jobs

* _[status](#neuro-job-status)_: Display status of a job

* _[kill](#neuro-job-kill)_: Kill job

* _[ssh](#neuro-job-ssh)_: Start SSH terminal



### neuro job submit

Start job using IMAGE<br/>COMMANDS list will be passed as commands to model container.

**Usage:**

```bash
neuro job submit [options] [--volume MOUNT]...
          [--env VAR=VAL]... IMAGE [CMD...]
```

**Options:**

Name | Description|
|----|------------|
|_\-g, --gpu NUMBER_|Number of GPUs to request \[default: 0]|
|_\--gpu-model MODEL_|GPU to use \[default: nvidia\-tesla-k80]<br/>Other options available are<br/>nvidia\-tesla-k80<br/>nvidia\-tesla-p4<br/>nvidia\-tesla-v100|
|_\-c, --cpu NUMBER_|Number of CPUs to request \[default: 0.1]|
|_\-m, --memory AMOUNT_|Memory amount to request \[default: 1G]|
|_\-x, --extshm_|Request extended '/dev/shm' space|
|_--http NUMBER_|Enable HTTP port forwarding to container|
|_--ssh NUMBER_|Enable SSH port forwarding to container|
|_--volume MOUNT..._|Mounts directory from vault into container<br/>Use multiple options to mount more than one volume|
|_\-e, --env VAR=VAL..._|Set environment variable in container<br/>Use multiple options to define more than one variable|
|_\--env-file FILE_|File with environment variables to pass|
|_--preemptible_|Force job to run on a preemptible instance|
|_\--non-preemptible_|Force job to run on a non-preemptible instance|
|_\-d, --description DESC_|Add optional description to the job|
|_\-q, --quiet_|Run command in quiet mode \(print only job id)|


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



### neuro job monitor

Monitor job output stream

**Usage:**

```bash
neuro job monitor ID
```



### neuro job list

**Usage:**

```bash
neuro job list [options]
```

**Options:**

Name | Description|
|----|------------|
|_\-s, --status \(pending|running|succeeded|failed|all)_|<br/>Filter out job by status\(es) \(comma delimited if multiple)|
|_\-d, --description DESCRIPTION_|<br/>Filter out job by job description \(exact match)|
|_\-q, --quiet_|<br/>Run command in quiet mode \(print only job ids)<br/>List all jobs|


**Examples:**

```bash
neuro job list --description="my favourite job"
neuro job list --status=all
neuro job list --status=pending,running --quiet
```



### neuro job status

Display status of a job

**Usage:**

```bash
neuro job status ID
```



### neuro job kill

Kill job\(s)

**Usage:**

```bash
neuro job kill JOB_IDS...
```



### neuro job ssh

Starts ssh terminal connected to running job.<br/>Job should be started with SSH support enabled.

**Usage:**

```bash
neuro job ssh [options] ID
```

**Options:**

Name | Description|
|----|------------|
|_--user STRING_|Container user name \[default: root]|
|_--key STRING_|Path to container private key.|


**Examples:**

```bash
neuro job ssh --user alfa --key ./my_docker_id_rsa job-abc-def-ghk
```



## neuro store

Storage operations

**Usage:**

```bash
neuro store COMMAND
```

**Commands:**

* _[rm](#neuro-store-rm)_: Remove files or directories

* _[ls](#neuro-store-ls)_: List directory contents

* _[cp](#neuro-store-cp)_: Copy files and directories

* _[mv](#neuro-store-mv)_: Move or rename files and directories

* _[mkdir](#neuro-store-mkdir)_: Make directories



### neuro store rm

Remove files or directories.

**Usage:**

```bash
neuro store rm PATH
```

**Examples:**

```bash
neuro store rm storage:///foo/bar/
neuro store rm storage:/foo/bar/
neuro store rm storage://username/foo/bar/
```



### neuro store ls

List directory contents<br/>By default PATH is equal user`s home dir \(storage:)

**Usage:**

```bash
neuro store ls [PATH]
```



### neuro store cp

Copy files and directories<br/>Either SOURCE or DESTINATION should have storage:// scheme.<br/>If scheme is omitted, file:// scheme is assumed.

**Usage:**

```bash
neuro store cp [options] SOURCE DESTINATION
```

**Options:**

Name | Description|
|----|------------|
|_\-r, --recursive_|Recursive copy|
|_\-p, --progress_|Show progress|


**Examples:**

```bash
# copy local file ./foo into remote storage root
neuro store cp ./foo storage:///
neuro store cp ./foo storage:/
# download remote file foo into local file foo with
# explicit file:// scheme set
neuro store cp storage:///foo file:///foo
```



### neuro store mv

Move or rename files and directories. SOURCE must contain path to the<br/>file or directory existing on the storage, and DESTINATION must contain<br/>the full path to the target file or directory.

**Usage:**

```bash
neuro store mv SOURCE DESTINATION
```

**Examples:**

```bash
# move or rename remote file
neuro store mv storage://username/foo.txt storage://username/bar.txt
neuro store mv storage://username/foo.txt storage://~/bar/baz/foo.txt
# move or rename remote directory
neuro store mv storage://username/foo/ storage://username/bar/
neuro store mv storage://username/foo/ storage://username/bar/baz/foo/
```



### neuro store mkdir

Make directories

**Usage:**

```bash
neuro store mkdir PATH
```



## neuro image

Docker image operations

**Usage:**

```bash
neuro image COMMAND
```

**Commands:**

* _[push](#neuro-image-push)_: Push docker image from local machine to cloud registry.

* _[pull](#neuro-image-pull)_: Pull docker image from cloud registry to local machine.



### neuro image push

Push an image to platform registry

**Usage:**

```bash
neuro image push IMAGE_NAME
```



### neuro image pull

Pull an image from platform registry

**Usage:**

```bash
neuro image pull IMAGE_NAME
```



## neuro config

Client configuration settings commands

**Usage:**

```bash
neuro config COMMAND
```

**Commands:**

* _[url](#neuro-config-url)_: Updates API URL

* _[auth](#neuro-config-auth)_: Updates API Token

* _[forget](#neuro-config-forget)_: Forget stored API Token

* _[id_rsa](#neuro-config-id_rsa)_: Updates path to Github RSA token,
in use for SSH/Remote debug

* _[show](#neuro-config-show)_: Print current settings



### neuro config url

Updates settings with provided platform URL.

**Usage:**

```bash
neuro config url URL
```

**Examples:**

```bash
neuro config url https://platform.neuromation.io/api/v1
```



### neuro config auth

Updates authorization token

**Usage:**

```bash
neuro config auth TOKEN
```



### neuro config forget

Forget authorization token

**Usage:**

```bash
neuro config forget
```



### neuro config id_rsa

Updates path to id_rsa file with private key.<br/>File is being used for accessing remote shell, remote debug.<br/>Note: this is temporal and going to be<br/>replaced in future by JWT token.

**Usage:**

```bash
neuro config id_rsa FILE
```



### neuro config show

Prints current settings.

**Usage:**

```bash
neuro config show
```



## neuro completion

Generates code to enable bash-completion.

**Usage:**

```bash
neuro completion COMMAND
```

**Commands:**

* _[generate](#neuro-completion-generate)_: Generate code enabling bash-completion.
eval $(neuro completion generate) enables completion
for the current session.
Adding eval $(neuro completion generate) to
.bashrc_profile enables completion permanently.

* _[patch](#neuro-completion-patch)_: Automatically patch .bash_profile to enable completion



### neuro completion generate

Generate code enabling bash-completion.<br/>eval $(

**Usage:**

```bash
neuro completion generate
```



### neuro completion patch

Automatically patch .bash_profile to enable completion

**Usage:**

```bash
neuro completion patch
```



## neuro share

Shares resource specified by URI to a USER with PERMISSION \(read|write|manage)

**Usage:**

```bash
neuro share URI USER PERMISSION
```

**Examples:**

```bash
neuro share storage:///sample_data/ alice manage
neuro share image:///resnet50 bob read
neuro share job:///my_job_id alice write
```



## neuro help

Display help for given COMMAND

**Usage:**

```bash
neuro help COMMAND [SUBCOMMAND[...]]
```

**Examples:**

```bash
neuro help store
neuro help store ls
```



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


# Table of Contents
* [neuro](#neuro)
	* [neuro acl](#neuro-acl)
		* [neuro acl add-role](#neuro-acl-add-role)
		* [neuro acl grant](#neuro-acl-grant)
		* [neuro acl list-roles](#neuro-acl-list-roles)
		* [neuro acl ls](#neuro-acl-ls)
		* [neuro acl remove-role](#neuro-acl-remove-role)
		* [neuro acl revoke](#neuro-acl-revoke)
	* [neuro admin](#neuro-admin)
		* [neuro admin add-cluster](#neuro-admin-add-cluster)
		* [neuro admin add-cluster-user](#neuro-admin-add-cluster-user)
		* [neuro admin add-org](#neuro-admin-add-org)
		* [neuro admin add-org-cluster](#neuro-admin-add-org-cluster)
		* [neuro admin add-org-cluster-credits](#neuro-admin-add-org-cluster-credits)
		* [neuro admin add-org-user](#neuro-admin-add-org-user)
		* [neuro admin add-project](#neuro-admin-add-project)
		* [neuro admin add-project-user](#neuro-admin-add-project-user)
		* [neuro admin add-resource-preset](#neuro-admin-add-resource-preset)
		* [neuro admin add-user-credits](#neuro-admin-add-user-credits)
		* [neuro admin generate-cluster-config](#neuro-admin-generate-cluster-config)
		* [neuro admin get-cluster-users](#neuro-admin-get-cluster-users)
		* [neuro admin get-clusters](#neuro-admin-get-clusters)
		* [neuro admin get-org-cluster-quota](#neuro-admin-get-org-cluster-quota)
		* [neuro admin get-org-clusters](#neuro-admin-get-org-clusters)
		* [neuro admin get-org-users](#neuro-admin-get-org-users)
		* [neuro admin get-orgs](#neuro-admin-get-orgs)
		* [neuro admin get-project-users](#neuro-admin-get-project-users)
		* [neuro admin get-projects](#neuro-admin-get-projects)
		* [neuro admin get-user-quota](#neuro-admin-get-user-quota)
		* [neuro admin remove-cluster](#neuro-admin-remove-cluster)
		* [neuro admin remove-cluster-user](#neuro-admin-remove-cluster-user)
		* [neuro admin remove-org](#neuro-admin-remove-org)
		* [neuro admin remove-org-cluster](#neuro-admin-remove-org-cluster)
		* [neuro admin remove-org-user](#neuro-admin-remove-org-user)
		* [neuro admin remove-project-user](#neuro-admin-remove-project-user)
		* [neuro admin remove-resource-preset](#neuro-admin-remove-resource-preset)
		* [neuro admin set-org-cluster-credits](#neuro-admin-set-org-cluster-credits)
		* [neuro admin set-org-cluster-defaults](#neuro-admin-set-org-cluster-defaults)
		* [neuro admin set-org-cluster-quota](#neuro-admin-set-org-cluster-quota)
		* [neuro admin set-user-credits](#neuro-admin-set-user-credits)
		* [neuro admin set-user-quota](#neuro-admin-set-user-quota)
		* [neuro admin show-cluster-options](#neuro-admin-show-cluster-options)
		* [neuro admin update-cluster](#neuro-admin-update-cluster)
		* [neuro admin update-node-pool](#neuro-admin-update-node-pool)
		* [neuro admin update-org-cluster](#neuro-admin-update-org-cluster)
		* [neuro admin update-project](#neuro-admin-update-project)
		* [neuro admin update-project-user](#neuro-admin-update-project-user)
		* [neuro admin update-resource-preset](#neuro-admin-update-resource-preset)
	* [neuro blob](#neuro-blob)
		* [neuro blob cp](#neuro-blob-cp)
		* [neuro blob du](#neuro-blob-du)
		* [neuro blob glob](#neuro-blob-glob)
		* [neuro blob importbucket](#neuro-blob-importbucket)
		* [neuro blob ls](#neuro-blob-ls)
		* [neuro blob lsbucket](#neuro-blob-lsbucket)
		* [neuro blob lscredentials](#neuro-blob-lscredentials)
		* [neuro blob mkbucket](#neuro-blob-mkbucket)
		* [neuro blob mkcredentials](#neuro-blob-mkcredentials)
		* [neuro blob rm](#neuro-blob-rm)
		* [neuro blob rmbucket](#neuro-blob-rmbucket)
		* [neuro blob rmcredentials](#neuro-blob-rmcredentials)
		* [neuro blob set-bucket-publicity](#neuro-blob-set-bucket-publicity)
		* [neuro blob sign-url](#neuro-blob-sign-url)
		* [neuro blob statbucket](#neuro-blob-statbucket)
		* [neuro blob statcredentials](#neuro-blob-statcredentials)
	* [neuro completion](#neuro-completion)
		* [neuro completion generate](#neuro-completion-generate)
		* [neuro completion patch](#neuro-completion-patch)
	* [neuro config](#neuro-config)
		* [neuro config aliases](#neuro-config-aliases)
		* [neuro config docker](#neuro-config-docker)
		* [neuro config get-clusters](#neuro-config-get-clusters)
		* [neuro config login](#neuro-config-login)
		* [neuro config login-headless](#neuro-config-login-headless)
		* [neuro config login-with-token](#neuro-config-login-with-token)
		* [neuro config logout](#neuro-config-logout)
		* [neuro config show](#neuro-config-show)
		* [neuro config show-token](#neuro-config-show-token)
		* [neuro config switch-cluster](#neuro-config-switch-cluster)
		* [neuro config switch-org](#neuro-config-switch-org)
		* [neuro config switch-project](#neuro-config-switch-project)
	* [neuro disk](#neuro-disk)
		* [neuro disk create](#neuro-disk-create)
		* [neuro disk get](#neuro-disk-get)
		* [neuro disk ls](#neuro-disk-ls)
		* [neuro disk rm](#neuro-disk-rm)
	* [neuro image](#neuro-image)
		* [neuro image digest](#neuro-image-digest)
		* [neuro image ls](#neuro-image-ls)
		* [neuro image pull](#neuro-image-pull)
		* [neuro image push](#neuro-image-push)
		* [neuro image rm](#neuro-image-rm)
		* [neuro image size](#neuro-image-size)
		* [neuro image tags](#neuro-image-tags)
	* [neuro job](#neuro-job)
		* [neuro job attach](#neuro-job-attach)
		* [neuro job browse](#neuro-job-browse)
		* [neuro job bump-life-span](#neuro-job-bump-life-span)
		* [neuro job exec](#neuro-job-exec)
		* [neuro job generate-run-command](#neuro-job-generate-run-command)
		* [neuro job kill](#neuro-job-kill)
		* [neuro job logs](#neuro-job-logs)
		* [neuro job ls](#neuro-job-ls)
		* [neuro job port-forward](#neuro-job-port-forward)
		* [neuro job run](#neuro-job-run)
		* [neuro job save](#neuro-job-save)
		* [neuro job status](#neuro-job-status)
		* [neuro job top](#neuro-job-top)
	* [neuro secret](#neuro-secret)
		* [neuro secret add](#neuro-secret-add)
		* [neuro secret ls](#neuro-secret-ls)
		* [neuro secret rm](#neuro-secret-rm)
	* [neuro service-account](#neuro-service-account)
		* [neuro service-account create](#neuro-service-account-create)
		* [neuro service-account get](#neuro-service-account-get)
		* [neuro service-account ls](#neuro-service-account-ls)
		* [neuro service-account rm](#neuro-service-account-rm)
	* [neuro storage](#neuro-storage)
		* [neuro storage cp](#neuro-storage-cp)
		* [neuro storage df](#neuro-storage-df)
		* [neuro storage glob](#neuro-storage-glob)
		* [neuro storage ls](#neuro-storage-ls)
		* [neuro storage mkdir](#neuro-storage-mkdir)
		* [neuro storage mv](#neuro-storage-mv)
		* [neuro storage rm](#neuro-storage-rm)
		* [neuro storage tree](#neuro-storage-tree)
	* [neuro attach](#neuro-attach)
	* [neuro cp](#neuro-cp)
	* [neuro exec](#neuro-exec)
	* [neuro help](#neuro-help)
	* [neuro images](#neuro-images)
	* [neuro kill](#neuro-kill)
	* [neuro login](#neuro-login)
	* [neuro logout](#neuro-logout)
	* [neuro logs](#neuro-logs)
	* [neuro ls](#neuro-ls)
	* [neuro mkdir](#neuro-mkdir)
	* [neuro mv](#neuro-mv)
	* [neuro port-forward](#neuro-port-forward)
	* [neuro ps](#neuro-ps)
	* [neuro pull](#neuro-pull)
	* [neuro push](#neuro-push)
	* [neuro rm](#neuro-rm)
	* [neuro run](#neuro-run)
	* [neuro save](#neuro-save)
	* [neuro share](#neuro-share)
	* [neuro status](#neuro-status)
	* [neuro top](#neuro-top)

# neuro

**Usage:**

```bash
neuro [OPTIONS] COMMAND [ARGS]...
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_--color \[yes &#124; no &#124; auto]_|Color mode.|
|_\--disable-pypi-version-check_|Don't periodically check PyPI to determine whether a new version of Neuro Platform CLI is available for download.  \[env var: NEURO\_CLI_DISABLE_PYPI_VERSION_CHECK]|
|_\--hide-token / --no-hide-token_|Prevent user's token sent in HTTP headers from being printed out to stderr during HTTP tracing. Can be used only together with option '--trace'. On by default.|
|_\--iso-datetime-format / --no-iso-datetime-format_|Use ISO 8601 format for printing date and time|
|_\--network-timeout FLOAT_|Network read timeout, seconds.|
|_\--neuromation-config PATH_|Path to config directory.|
|_\-q, --quiet_|Give less output. Option is additive, and can be used up to 2 times.|
|_\--show-traceback_|Show python traceback on error, useful for debugging the tool.|
|_\--skip-stats / --no-skip-stats_|Skip sending usage statistics to Neuro servers. Note: the statistics has no sensitive data, e.g. file, job, image, or user names, executed command lines, environment variables, etc.|
|_--trace_|Trace sent HTTP requests and received replies to stderr.|
|_\-v, --verbose_|Give more output. Option is additive, and can be used up to 2 times.|
|_--version_|Show the version and exit.|


**Command Groups:**

|Usage|Description|
|---|---|
| _[neuro acl](#neuro-acl)_| Access Control List management |
| _[neuro admin](#neuro-admin)_| Cluster administration commands |
| _[neuro blob](#neuro-blob)_| Blob storage operations |
| _[neuro completion](#neuro-completion)_| Output shell completion code |
| _[neuro config](#neuro-config)_| Client configuration |
| _[neuro disk](#neuro-disk)_| Operations with disks |
| _[neuro image](#neuro-image)_| Container image operations |
| _[neuro job](#neuro-job)_| Job operations |
| _[neuro secret](#neuro-secret)_| Operations with secrets |
| _[neuro service-account](#neuro-service-account)_| Operations with service accounts |
| _[neuro storage](#neuro-storage)_| Storage operations |


**Commands:**

|Usage|Description|
|---|---|
| _[neuro attach](#neuro-attach)_| Attach terminal to a job |
| _[neuro cp](#neuro-cp)_| Copy files and directories |
| _[neuro exec](#neuro-exec)_| Execute command in a running job |
| _[neuro help](#neuro-help)_| Get help on a command |
| _[neuro images](#neuro-images)_| List images |
| _[neuro kill](#neuro-kill)_| Kill job\(s) |
| _[neuro login](#neuro-login)_| Log into Neuro Platform |
| _[neuro logout](#neuro-logout)_| Log out |
| _[neuro logs](#neuro-logs)_| Print the logs for a job |
| _[neuro ls](#neuro-ls)_| List directory contents |
| _[neuro mkdir](#neuro-mkdir)_| Make directories |
| _[neuro mv](#neuro-mv)_| Move or rename files and directories |
| _[neuro port-forward](#neuro-port-forward)_| Forward port\(s) of a job |
| _[neuro ps](#neuro-ps)_| List all jobs |
| _[neuro pull](#neuro-pull)_| Pull an image from platform registry |
| _[neuro push](#neuro-push)_| Push an image to platform registry |
| _[neuro rm](#neuro-rm)_| Remove files or directories |
| _[neuro run](#neuro-run)_| Run a job |
| _[neuro save](#neuro-save)_| Save job's state to an image |
| _[neuro share](#neuro-share)_| Shares resource with another user |
| _[neuro status](#neuro-status)_| Display status of a job |
| _[neuro top](#neuro-top)_| Display GPU/CPU/Memory usage |




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
| _[neuro acl add-role](#neuro-acl-add-role)_| Add new role |
| _[neuro acl grant](#neuro-acl-grant)_| Shares resource with another user |
| _[neuro acl list-roles](#neuro-acl-list-roles)_| List roles |
| _[neuro acl ls](#neuro-acl-ls)_| List shared resources |
| _[neuro acl remove-role](#neuro-acl-remove-role)_| Remove existing role |
| _[neuro acl revoke](#neuro-acl-revoke)_| Revoke user access from another user |




### neuro acl add-role

Add new role.<br/>

**Usage:**

```bash
neuro acl add-role [OPTIONS] ROLE_NAME
```

**Examples:**

```bash

neuro acl add-role mycompany/subdivision

```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro acl grant

Shares resource with another user.<br/><br/>URI shared resource.<br/><br/>USER username to share resource with.<br/><br/>PERMISSION sharing access right: read, write, or manage.<br/>

**Usage:**

```bash
neuro acl grant [OPTIONS] URI USER {read|write|manage}
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




### neuro acl list-roles

List roles.<br/>

**Usage:**

```bash
neuro acl list-roles [OPTIONS]
```

**Examples:**

```bash

neuro acl list-roles
neuro acl list-roles username/projects

```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_-u TEXT_|Fetch roles of specified user or role.|




### neuro acl ls

List shared resources.<br/><br/>The command displays a list of resources shared BY current user \(default).<br/><br/>To display a list of resources shared WITH current user apply --shared option.<br/>

**Usage:**

```bash
neuro acl ls [OPTIONS] [URI]
```

**Examples:**

```bash

neuro acl list
neuro acl list storage://
neuro acl list --shared
neuro acl list --shared image://

```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_\--full-uri_|Output full URI.|
|_--shared_|Output the resources shared by the user.|
|_-u TEXT_|Use specified user or role.|




### neuro acl remove-role

Remove existing role.<br/>

**Usage:**

```bash
neuro acl remove-role [OPTIONS] ROLE_NAME
```

**Examples:**

```bash

neuro acl remove-role mycompany/subdivision

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
| _[neuro admin add-cluster](#neuro-admin-add-cluster)_| Create a new cluster |
| _[neuro admin add\-cluster-user](#neuro-admin-add-cluster-user)_| Add user access to specified cluster |
| _[neuro admin add-org](#neuro-admin-add-org)_| Create a new org |
| _[neuro admin add\-org-cluster](#neuro-admin-add-org-cluster)_| Add org access to specified cluster |
| _[neuro admin add\-org-cluster-credits](#neuro-admin-add-org-cluster-credits)_| Add given values to org cluster balance |
| _[neuro admin add\-org-user](#neuro-admin-add-org-user)_| Add user access to specified org |
| _[neuro admin add-project](#neuro-admin-add-project)_| Add new project to specified cluster |
| _[neuro admin add\-project-user](#neuro-admin-add-project-user)_| Add user access to specified project |
| _[neuro admin add\-resource-preset](#neuro-admin-add-resource-preset)_| Add new resource preset |
| _[neuro admin add\-user-credits](#neuro-admin-add-user-credits)_| Add given values to user quota |
| _[neuro admin generate\-cluster-config](#neuro-admin-generate-cluster-config)_| Create a cluster configuration file |
| _[neuro admin get\-cluster-users](#neuro-admin-get-cluster-users)_| List users in specified cluster |
| _[neuro admin get-clusters](#neuro-admin-get-clusters)_| Print the list of available clusters |
| _[neuro admin get\-org-cluster-quota](#neuro-admin-get-org-cluster-quota)_| Get info about org quota in given cluster |
| _[neuro admin get\-org-clusters](#neuro-admin-get-org-clusters)_| Print the list of all orgs in the cluster |
| _[neuro admin get\-org-users](#neuro-admin-get-org-users)_| List users in specified org |
| _[neuro admin get-orgs](#neuro-admin-get-orgs)_| Print the list of available orgs |
| _[neuro admin get\-project-users](#neuro-admin-get-project-users)_| List users in specified project |
| _[neuro admin get-projects](#neuro-admin-get-projects)_| Print the list of all projects in the cluster |
| _[neuro admin get\-user-quota](#neuro-admin-get-user-quota)_| Get info about user quota in given cluster |
| _[neuro admin remove-cluster](#neuro-admin-remove-cluster)_| Drop a cluster |
| _[neuro admin remove\-cluster-user](#neuro-admin-remove-cluster-user)_| Remove user access from the cluster |
| _[neuro admin remove-org](#neuro-admin-remove-org)_| Drop a org |
| _[neuro admin remove\-org-cluster](#neuro-admin-remove-org-cluster)_| Drop an org cluster |
| _[neuro admin remove\-org-user](#neuro-admin-remove-org-user)_| Remove user access from the org |
| _[neuro admin remove\-project-user](#neuro-admin-remove-project-user)_| Remove user access from the project |
| _[neuro admin remove\-resource-preset](#neuro-admin-remove-resource-preset)_| Remove resource preset |
| _[neuro admin set\-org-cluster-credits](#neuro-admin-set-org-cluster-credits)_| Set org cluster credits to given value |
| _[neuro admin set\-org-cluster-defaults](#neuro-admin-set-org-cluster-defaults)_| Set org cluster defaults to given value |
| _[neuro admin set\-org-cluster-quota](#neuro-admin-set-org-cluster-quota)_| Set org cluster quota to given values |
| _[neuro admin set\-user-credits](#neuro-admin-set-user-credits)_| Set user credits to given value |
| _[neuro admin set\-user-quota](#neuro-admin-set-user-quota)_| Set user quota to given values |
| _[neuro admin show\-cluster-options](#neuro-admin-show-cluster-options)_| Show available cluster options |
| _[neuro admin update-cluster](#neuro-admin-update-cluster)_| Update a cluster |
| _[neuro admin update\-node-pool](#neuro-admin-update-node-pool)_| Update cluster node pool |
| _[neuro admin update\-org-cluster](#neuro-admin-update-org-cluster)_| Update org cluster quotas |
| _[neuro admin update-project](#neuro-admin-update-project)_| Update project settings |
| _[neuro admin update\-project-user](#neuro-admin-update-project-user)_| Update user access to specified project |
| _[neuro admin update\-resource-preset](#neuro-admin-update-resource-preset)_| Update existing resource preset |




### neuro admin add-cluster

Create a new cluster.<br/><br/>Creates cluster entry on admin side and then start its provisioning using<br/>provided config.

**Usage:**

```bash
neuro admin add-cluster [OPTIONS] CLUSTER_NAME CONFIG
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_\--default-credits AMOUNT_|Default credits amount to set \(`unlimited' stands for no limit)  \[default: unlimited]|
|_\--default-jobs AMOUNT_|Default maximum running jobs quota \(`unlimited' stands for no limit)  \[default: unlimited]|
|_\--default-role \[ROLE]_|Default role for new users added to cluster  \[default: user]|




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
|_\-c, --credits AMOUNT_|Credits amount to set \(`unlimited' stands for no limit)|
|_\-j, --jobs AMOUNT_|Maximum running jobs quota \(`unlimited' stands for no limit)|
|_--org ORG_|org name for org-cluster users|




### neuro admin add-org

Create a new org.

**Usage:**

```bash
neuro admin add-org [OPTIONS] ORG_NAME
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro admin add-org-cluster

Add org access to specified cluster.

**Usage:**

```bash
neuro admin add-org-cluster [OPTIONS] CLUSTER_NAME ORG_NAME
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_\-c, --credits AMOUNT_|Credits amount to set \(`unlimited' stands for no limit)  \[default: unlimited]|
|_\--default-credits AMOUNT_|Default credits amount to set \(`unlimited' stands for no limit)  \[default: unlimited]|
|_\--default-jobs AMOUNT_|Default maximum running jobs quota \(`unlimited' stands for no limit)  \[default: unlimited]|
|_\--default-role \[ROLE]_|Default role for new users added to org cluster  \[default: user]|
|_\-j, --jobs AMOUNT_|Maximum running jobs quota \(`unlimited' stands for no limit)  \[default: unlimited]|
|_\--storage-size AMOUNT_|Storage size, ignored for storage types with elastic storage size|




### neuro admin add-org-cluster-credits

Add given values to org cluster balance

**Usage:**

```bash
neuro admin add-org-cluster-credits [OPTIONS] CLUSTER_NAME ORG_NAME
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_\-c, --credits AMOUNT_|Credits amount to add|




### neuro admin add-org-user

Add user access to specified org.<br/><br/>The command supports one of 3 user roles: admin, manager or user.

**Usage:**

```bash
neuro admin add-org-user [OPTIONS] ORG_NAME USER_NAME [ROLE]
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro admin add-project

Add new project to specified cluster.

**Usage:**

```bash
neuro admin add-project [OPTIONS] CLUSTER_NAME NAME
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_--default_|Is this project is default, e.g. new cluster users will be automatically added to it|
|_\--default-role \[ROLE]_|Default role for new users added to project  \[default: writer]|
|_--org ORG_|org name for org-cluster projects|




### neuro admin add-project-user

Add user access to specified project.<br/><br/>The command supports one of 4 user roles: reader, writer, manager or admin.

**Usage:**

```bash
neuro admin add-project-user [OPTIONS] CLUSTER_NAME PROJECT_NAME
                                    USER_NAME [ROLE]
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_--org ORG_|org name for org-cluster projects|




### neuro admin add-resource-preset

Add new resource preset

**Usage:**

```bash
neuro admin add-resource-preset [OPTIONS] PRESET_NAME
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_\-c, --cpu NUMBER_|Number of CPUs  \[default: 0.1]|
|_\--credits-per-hour AMOUNT_|Price of running job of this preset for an hour in credits  \[default: 0]|
|_\-g, --gpu NUMBER_|Number of GPUs|
|_\--gpu-model MODEL_|GPU model|
|_\-m, --memory AMOUNT_|Memory amount  \[default: 1GB]|
|_\--preemptible-node / --non-preemptible-node_|Use a lower\-cost preemptible instance  \[default: non-preemptible-node]|
|_\-p, --scheduler / -P, --no-scheduler_|Use round robin scheduler for jobs  \[default: no-scheduler]|
|_\--tpu-sw-version VERSION_|TPU software version|
|_\--tpu-type TYPE_|TPU type|




### neuro admin add-user-credits

Add given values to user quota

**Usage:**

```bash
neuro admin add-user-credits [OPTIONS] CLUSTER_NAME USER_NAME
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_\-c, --credits AMOUNT_|Credits amount to add  \[required]|
|_--org ORG_|org name for org-cluster users|




### neuro admin generate-cluster-config

Create a cluster configuration file.

**Usage:**

```bash
neuro admin generate-cluster-config [OPTIONS] [CONFIG]
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_--type \[aws &#124; gcp &#124; azure &#124; vcd]_||




### neuro admin get-cluster-users

List users in specified cluster

**Usage:**

```bash
neuro admin get-cluster-users [OPTIONS] [CLUSTER_NAME]
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_--org ORG_|org name for org-cluster users|




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




### neuro admin get-org-cluster-quota

Get info about org quota in given cluster

**Usage:**

```bash
neuro admin get-org-cluster-quota [OPTIONS] CLUSTER_NAME ORG_NAME
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro admin get-org-clusters

Print the list of all orgs in the cluster

**Usage:**

```bash
neuro admin get-org-clusters [OPTIONS] CLUSTER_NAME
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro admin get-org-users

List users in specified org

**Usage:**

```bash
neuro admin get-org-users [OPTIONS] ORG_NAME
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro admin get-orgs

Print the list of available orgs.

**Usage:**

```bash
neuro admin get-orgs [OPTIONS]
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro admin get-project-users

List users in specified project

**Usage:**

```bash
neuro admin get-project-users [OPTIONS] CLUSTER_NAME PROJECT_NAME
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_--org ORG_|org name for org-cluster projects|




### neuro admin get-projects

Print the list of all projects in the cluster

**Usage:**

```bash
neuro admin get-projects [OPTIONS] CLUSTER_NAME
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_--org ORG_|org name for org-cluster projects|




### neuro admin get-user-quota

Get info about user quota in given cluster

**Usage:**

```bash
neuro admin get-user-quota [OPTIONS] CLUSTER_NAME USER_NAME
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_--org ORG_|org name for org-cluster users|




### neuro admin remove-cluster

Drop a cluster<br/><br/>Completely removes cluster from the system.

**Usage:**

```bash
neuro admin remove-cluster [OPTIONS] CLUSTER_NAME
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_--force_|Skip prompt|




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
|_--org ORG_|org name for org-cluster users|




### neuro admin remove-org

Drop a org<br/><br/>Completely removes org from the system.

**Usage:**

```bash
neuro admin remove-org [OPTIONS] ORG_NAME
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_--force_|Skip prompt|




### neuro admin remove-org-cluster

Drop an org cluster<br/><br/>Completely removes org from the cluster.

**Usage:**

```bash
neuro admin remove-org-cluster [OPTIONS] CLUSTER_NAME ORG_NAME
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_--force_|Skip prompt|




### neuro admin remove-org-user

Remove user access from the org.

**Usage:**

```bash
neuro admin remove-org-user [OPTIONS] ORG_NAME USER_NAME
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro admin remove-project-user

Remove user access from the project.

**Usage:**

```bash
neuro admin remove-project-user [OPTIONS] CLUSTER_NAME PROJECT_NAME
                                       USER_NAME
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_--org ORG_|org name for org-cluster projects|




### neuro admin remove-resource-preset

Remove resource preset

**Usage:**

```bash
neuro admin remove-resource-preset [OPTIONS] PRESET_NAME
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro admin set-org-cluster-credits

Set org cluster credits to given value

**Usage:**

```bash
neuro admin set-org-cluster-credits [OPTIONS] CLUSTER_NAME ORG_NAME
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_\-c, --credits AMOUNT_|Credits amount to set \(`unlimited' stands for no limit)  \[required]|




### neuro admin set-org-cluster-defaults

Set org cluster defaults to given value

**Usage:**

```bash
neuro admin set-org-cluster-defaults [OPTIONS] CLUSTER_NAME ORG_NAME
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_\--default-credits AMOUNT_|Default credits amount to set \(`unlimited' stands for no limit)  \[default: unlimited]|
|_\--default-jobs AMOUNT_|Default maximum running jobs quota \(`unlimited' stands for no limit)  \[default: unlimited]|
|_\--default-role \[ROLE]_|Default role for new users added to org cluster  \[default: user]|




### neuro admin set-org-cluster-quota

Set org cluster quota to given values

**Usage:**

```bash
neuro admin set-org-cluster-quota [OPTIONS] CLUSTER_NAME ORG_NAME
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_\-j, --jobs AMOUNT_|Maximum running jobs quota \(`unlimited' stands for no limit)  \[required]|




### neuro admin set-user-credits

Set user credits to given value

**Usage:**

```bash
neuro admin set-user-credits [OPTIONS] CLUSTER_NAME USER_NAME
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_\-c, --credits AMOUNT_|Credits amount to set \(`unlimited' stands for no limit)  \[required]|
|_--org ORG_|org name for org-cluster users|




### neuro admin set-user-quota

Set user quota to given values

**Usage:**

```bash
neuro admin set-user-quota [OPTIONS] CLUSTER_NAME USER_NAME
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_\-j, --jobs AMOUNT_|Maximum running jobs quota \(`unlimited' stands for no limit)  \[required]|
|_--org ORG_|org name for org-cluster users|




### neuro admin show-cluster-options

Show available cluster options.

**Usage:**

```bash
neuro admin show-cluster-options [OPTIONS]
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_--type \[aws &#124; gcp &#124; azure]_||




### neuro admin update-cluster

Update a cluster.

**Usage:**

```bash
neuro admin update-cluster [OPTIONS] CLUSTER_NAME
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_\--default-credits AMOUNT_|Default credits amount to set \(`unlimited' stands for no limit)  \[default: unlimited]|
|_\--default-jobs AMOUNT_|Default maximum running jobs quota \(`unlimited' stands for no limit)  \[default: unlimited]|
|_\--default-role \[ROLE]_|Default role for new users added to cluster  \[default: user]|




### neuro admin update-node-pool

Update cluster node pool.

**Usage:**

```bash
neuro admin update-node-pool [OPTIONS] CLUSTER_NAME NODE_POOL_NAME
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_\--idle-size NUMBER_|Number of idle nodes in the node pool.|




### neuro admin update-org-cluster

Update org cluster quotas.

**Usage:**

```bash
neuro admin update-org-cluster [OPTIONS] CLUSTER_NAME ORG_NAME
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_\-c, --credits AMOUNT_|Credits amount to set \(`unlimited' stands for no limit)  \[default: unlimited]|
|_\--default-credits AMOUNT_|Default credits amount to set \(`unlimited' stands for no limit)  \[default: unlimited]|
|_\--default-jobs AMOUNT_|Default maximum running jobs quota \(`unlimited' stands for no limit)  \[default: unlimited]|
|_\--default-role \[ROLE]_|Default role for new users added to org cluster  \[default: user]|
|_\-j, --jobs AMOUNT_|Maximum running jobs quota \(`unlimited' stands for no limit)  \[default: unlimited]|




### neuro admin update-project

Update project settings.

**Usage:**

```bash
neuro admin update-project [OPTIONS] CLUSTER_NAME NAME
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_--default_|Is this project is default, e.g. new cluster users will be automatically added to it|
|_\--default-role \[ROLE]_|Default role for new users added to project  \[default: writer]|
|_--org ORG_|org name for org-cluster projects|




### neuro admin update-project-user

Update user access to specified project.<br/><br/>The command supports one of 4 user roles: reader, writer, manager or admin.

**Usage:**

```bash
neuro admin update-project-user [OPTIONS] CLUSTER_NAME PROJECT_NAME
                                       USER_NAME [ROLE]
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_--org ORG_|org name for org-cluster projects|




### neuro admin update-resource-preset

Update existing resource preset

**Usage:**

```bash
neuro admin update-resource-preset [OPTIONS] PRESET_NAME
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_\-c, --cpu NUMBER_|Number of CPUs|
|_\--credits-per-hour AMOUNT_|Price of running job of this preset for an hour in credits|
|_\-g, --gpu NUMBER_|Number of GPUs|
|_\--gpu-model MODEL_|GPU model|
|_\-m, --memory AMOUNT_|Memory amount|
|_\--preemptible-node / --non-preemptible-node_|Use a lower-cost preemptible instance|
|_\-p, --scheduler / -P, --no-scheduler_|Use round robin scheduler for jobs|
|_\--tpu-sw-version VERSION_|TPU software version|
|_\--tpu-type TYPE_|TPU type|




## neuro blob

Blob storage operations.

**Usage:**

```bash
neuro blob [OPTIONS] COMMAND [ARGS]...
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|


**Commands:**

|Usage|Description|
|---|---|
| _[neuro blob cp](#neuro-blob-cp)_| Copy blobs into and from Blob Storage |
| _[neuro blob du](#neuro-blob-du)_| Get storage usage for BUCKET |
| _[neuro blob glob](#neuro-blob-glob)_| List resources that match PATTERNS |
| _[neuro blob importbucket](#neuro-blob-importbucket)_| Import an existing bucket |
| _[neuro blob ls](#neuro-blob-ls)_| List buckets or bucket contents |
| _[neuro blob lsbucket](#neuro-blob-lsbucket)_| List buckets |
| _[neuro blob lscredentials](#neuro-blob-lscredentials)_| List bucket credentials |
| _[neuro blob mkbucket](#neuro-blob-mkbucket)_| Create a new bucket |
| _[neuro blob mkcredentials](#neuro-blob-mkcredentials)_| Create a new bucket credential |
| _[neuro blob rm](#neuro-blob-rm)_| Remove blobs from bucket |
| _[neuro blob rmbucket](#neuro-blob-rmbucket)_| Remove bucket BUCKET |
| _[neuro blob rmcredentials](#neuro-blob-rmcredentials)_| Remove bucket credential BUCKET_CREDENTIAL |
| _[neuro blob set\-bucket-publicity](#neuro-blob-set-bucket-publicity)_| Change public access settings for BUCKET |
| _[neuro blob sign-url](#neuro-blob-sign-url)_| Make signed url for blob in bucket |
| _[neuro blob statbucket](#neuro-blob-statbucket)_| Get bucket BUCKET |
| _[neuro blob statcredentials](#neuro-blob-statcredentials)_| Get bucket credential BUCKET_CREDENTIAL |




### neuro blob cp

Copy blobs into and from Blob Storage.<br/><br/>Either SOURCES or DESTINATION should have `blob://` scheme. If scheme is<br/>omitted, file:// scheme is assumed. It is currently not possible to copy files<br/>between Blob Storage \(`blob://`) destination, nor with `storage://` scheme<br/>paths.<br/><br/>Use `/dev/stdin` and `/dev/stdout` file names to upload a file from standard<br/>input or output to stdout.<br/><br/>Any number of \--exclude and --include options can be passed.  The filters that<br/>appear later in the command take precedence over filters that appear earlier<br/>in the command.  If neither \--exclude nor --include options are specified the<br/>default can be changed using the storage.cp-exclude configuration variable<br/>documented in "neuro help user-config".<br/><br/>File permissions, modification times and other attributes will not be passed<br/>to Blob Storage metadata during upload.

**Usage:**

```bash
neuro blob cp [OPTIONS] [SOURCES]... [DESTINATION]
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_--continue_|Continue copying partially-copied files. Only for copying from Blob Storage.|
|_\--exclude-from-files FILES_|A list of file names that contain patterns for exclusion files and directories. Used only for uploading. The default can be changed using the storage.cp\-exclude-from-files configuration variable documented in "neuro help user-config"|
|_--exclude TEXT_|Exclude files and directories that match the specified pattern.|
|_--include TEXT_|Don't exclude files and directories that match the specified pattern.|
|_\--glob / --no-glob_|Expand glob patterns in SOURCES with explicit scheme.  \[default: glob]|
|_\-T, --no-target-directory_|Treat DESTINATION as a normal file.|
|_\-p, --progress / -P, --no-progress_|Show progress, on by default.|
|_\-r, --recursive_|Recursive copy, off by default|
|_\-t, --target-directory DIRECTORY_|Copy all SOURCES into DIRECTORY.|
|_\-u, --update_|Copy only when the SOURCE file is newer than the destination file or when the destination file is missing.|




### neuro blob du

Get storage usage for BUCKET.

**Usage:**

```bash
neuro blob du [OPTIONS] BUCKET
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_--cluster CLUSTER_|Look on a specified cluster \(the current cluster by default).|
|_--org ORG_|Look on a specified org \(the current org by default).|
|_--project PROJECT_|Look on a specified project \(the current project by default).|




### neuro blob glob

List resources that match PATTERNS.

**Usage:**

```bash
neuro blob glob [OPTIONS] [PATTERNS]...
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_\--full-uri_|Output full bucket URI.|




### neuro blob importbucket

Import an existing bucket.

**Usage:**

```bash
neuro blob importbucket [OPTIONS]
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_\--aws-access-key-id AWS\_ACCESS_KEY_ID_|AWS access\_key_id to use to access the bucket.  Required when PROVIDER is 'aws'|
|_\--aws-endpoint-url AWS_ENDPOINT_|AWS endpoint to use to access the bucket. Usually you need to set this if you use non-AWS S3 compatible provider|
|_\--aws-region-name AWS_REGION_|AWS region to use to access the bucket.|
|_\--aws-secret-access-key AWS\_SECRET_ACCESS_KEY_|AWS secret\_access_key to use to access the bucket. Required when PROVIDER is 'aws'|
|_\--azure-storage-account-url AZURE\_STORAGE_ACCOUNT_URL_|Azure account url. Usually it has following format: https://<account_id>.blob.core.windows.net Required when PROVIDER is 'azure'|
|_\--azure-storage-credential AZURE\_STORAGE_CREDENTIAL_|Azure storage credential that grants access to imported bucket. Either this or AZURE_SAS is required when PROVIDER is 'azure'|
|_\--azure-storage-sas-token AZURE_SAS_|Azure shared access signature token that grants access to imported bucket. Either this or AZURE\_STORAGE_CREDENTIAL is required when PROVIDER is 'azure'|
|_--cluster CLUSTER_|Perform in a specified cluster \(the current cluster by default).|
|_\--gcp-sa-credential GCP\_SA_CREDNETIAL_|GCP service account credential in form of base64 encoded json string that grants access to imported bucket. Required when PROVIDER is 'gcp'|
|_--name NAME_|Optional bucket name|
|_--org ORG_|Perform in a specified org \(the current org by default).|
|_--project PROJECT_|Perform in a specified project \(the current project by default).|
|_--provider PROVIDER_|Bucket provider that hosts bucket  \[required]|
|_\--provider-bucket-name EXTERNAL_NAME_|Name of bucket \(or container in case of Azure) inside the provider  \[required]|




### neuro blob ls

List buckets or bucket contents.

**Usage:**

```bash
neuro blob ls [OPTIONS] [PATHS]...
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_-l_|use a long listing format.|
|_\--full-uri_|Output full bucket URI.|
|_\-h, --human-readable_|with -l print human readable sizes \(e.g., 2K, 540M).|
|_\-r, --recursive_|List all keys under the URL path provided, not just 1 level depths.|




### neuro blob lsbucket

List buckets.

**Usage:**

```bash
neuro blob lsbucket [OPTIONS]
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_--cluster CLUSTER_|Look on a specified cluster \(the current cluster by default).|
|_\--full-uri_|Output full bucket URI.|
|_\--long-format_|Output all info about bucket.|
|_--org ORG_|Look on a specified org \(the current org by default).|
|_--project PROJECT_|Look on a specified project \(the current project by default).|




### neuro blob lscredentials

List bucket credentials.

**Usage:**

```bash
neuro blob lscredentials [OPTIONS]
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_--cluster CLUSTER_|Look on a specified cluster \(the current cluster by default).|




### neuro blob mkbucket

Create a new bucket.

**Usage:**

```bash
neuro blob mkbucket [OPTIONS]
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_--cluster CLUSTER_|Perform in a specified cluster \(the current cluster by default).|
|_--name NAME_|Optional bucket name|
|_--org ORG_|Perform in a specified org \(the current org by default).|
|_--project PROJECT_|Perform in a specified project \(the current project by default).|




### neuro blob mkcredentials

Create a new bucket credential.

**Usage:**

```bash
neuro blob mkcredentials [OPTIONS] BUCKETS...
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_--cluster CLUSTER_|Perform in a specified cluster \(the current cluster by default).|
|_--name NAME_|Optional bucket credential name|
|_--org ORG_|Perform in a specified org \(the current org by default).|
|_--project PROJECT_|Perform in a specified project \(the current project by default).|
|_\--read-only_|Make read-only credential|




### neuro blob rm

Remove blobs from bucket.

**Usage:**

```bash
neuro blob rm [OPTIONS] PATHS...
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_\--glob / --no-glob_|Expand glob patterns in PATHS  \[default: glob]|
|_\-p, --progress / -P, --no-progress_|Show progress, on by default in TTY mode, off otherwise.|
|_\-r, --recursive_|remove directories and their contents recursively|




### neuro blob rmbucket

Remove bucket BUCKET.

**Usage:**

```bash
neuro blob rmbucket [OPTIONS] BUCKETS...
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_--cluster CLUSTER_|Perform on a specified cluster \(the current cluster by default).|
|_\-f, --force_|Force removal of all blobs inside bucket|
|_--org ORG_|Perform on a specified org \(the current org by default).|
|_--project PROJECT_|Perform on a specified project \(the current project by default).|




### neuro blob rmcredentials

Remove bucket credential BUCKET_CREDENTIAL.

**Usage:**

```bash
neuro blob rmcredentials [OPTIONS] CREDENTIALS...
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_--cluster CLUSTER_|Perform on a specified cluster \(the current cluster by default).|




### neuro blob set-bucket-publicity

Change public access settings for BUCKET<br/>

**Usage:**

```bash
neuro blob set-bucket-publicity [OPTIONS] BUCKET {public|private}
```

**Examples:**

```bash

neuro blob set-bucket-publicity my-bucket public
neuro blob set-bucket-publicity my-bucket private

```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_--cluster CLUSTER_|Perform on a specified cluster \(the current cluster by default).|
|_--org ORG_|Perform on a specified org \(the current org by default).|
|_--project PROJECT_|Perform on a specified project \(the current project by default).|




### neuro blob sign-url

Make signed url for blob in bucket.

**Usage:**

```bash
neuro blob sign-url [OPTIONS] PATH
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_--expires TIMEDELTA_|Duration this signature will be valid in the format '1h2m3s'  \[default: 1h]|




### neuro blob statbucket

Get bucket BUCKET.

**Usage:**

```bash
neuro blob statbucket [OPTIONS] BUCKET
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_--cluster CLUSTER_|Look on a specified cluster \(the current cluster by default).|
|_\--full-uri_|Output full bucket URI.|
|_--org ORG_|Look on a specified org \(the current org by default).|
|_--project PROJECT_|Look on a specified project \(the current project by default).|




### neuro blob statcredentials

Get bucket credential BUCKET_CREDENTIAL.

**Usage:**

```bash
neuro blob statcredentials [OPTIONS] BUCKET_CREDENTIAL
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_--cluster CLUSTER_|Look on a specified cluster \(the current cluster by default).|




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
| _[neuro completion generate](#neuro-completion-generate)_| Show instructions for shell completion |
| _[neuro completion patch](#neuro-completion-patch)_| Patch shell profile to enable completion |




### neuro completion generate

Show instructions for shell completion.

**Usage:**

```bash
neuro completion generate [OPTIONS] {bash|zsh}
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro completion patch

Patch shell profile to enable completion<br/><br/>Patches shell configuration while depending of current shell. Files patched:<br/><br/>bash: `~/.bashrc` zsh: `~/.zshrc`

**Usage:**

```bash
neuro completion patch [OPTIONS] {bash|zsh}
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
| _[neuro config aliases](#neuro-config-aliases)_| List available command aliases |
| _[neuro config docker](#neuro-config-docker)_| Configure local docker client |
| _[neuro config get-clusters](#neuro-config-get-clusters)_| List available clusters/org pairs |
| _[neuro config login](#neuro-config-login)_| Log into Neuro Platform |
| _[neuro config login-headless](#neuro-config-login-headless)_| Log into Neuro Platform in non-GUI environ |
| _[neuro config login\-with-token](#neuro-config-login-with-token)_| Log into Neuro Platform with token |
| _[neuro config logout](#neuro-config-logout)_| Log out |
| _[neuro config show](#neuro-config-show)_| Print current settings |
| _[neuro config show-token](#neuro-config-show-token)_| Print current authorization token |
| _[neuro config switch-cluster](#neuro-config-switch-cluster)_| Switch the active cluster |
| _[neuro config switch-org](#neuro-config-switch-org)_| Switch the active organization |
| _[neuro config switch-project](#neuro-config-switch-project)_| Switch the active project |




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




### neuro config docker

Configure local docker client<br/><br/>This command configures local docker client to use Neuro Platform's docker<br/>registry.

**Usage:**

```bash
neuro config docker [OPTIONS]
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_\--docker-config PATH_|Specifies the location of the Docker client configuration files|




### neuro config get-clusters

List available clusters/org pairs.<br/><br/>This command re-fetches cluster list and then displays each cluster with<br/>available orgs.

**Usage:**

```bash
neuro config get-clusters [OPTIONS]
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




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




### neuro config login-headless

Log into Neuro Platform in non-GUI environ<br/><br/>URL is a platform entrypoint URL.<br/><br/>The command works similar to "neuro login" but instead of opening a browser<br/>for performing OAuth registration prints an URL that should be open on guest<br/>host.<br/><br/>Then user inputs a code displayed in a browser after successful login back in<br/>neuro command to finish the login process.

**Usage:**

```bash
neuro config login-headless [OPTIONS] [URL]
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
|_--energy_|Including cluster energy consumption and CO2 emissions information|




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




### neuro config switch-cluster

Switch the active cluster.<br/><br/>CLUSTER_NAME is the cluster name to select.  The interactive prompt is used if<br/>the name is omitted \(default).

**Usage:**

```bash
neuro config switch-cluster [OPTIONS] [CLUSTER_NAME]
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro config switch-org

Switch the active organization.<br/><br/>ORG\_NAME is the organization name to select. Use literal "NO_ORG" to switch to<br/>using current cluster directly instead of on behalf of some org.

**Usage:**

```bash
neuro config switch-org [OPTIONS] ORG_NAME
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro config switch-project

Switch the active project.<br/><br/>PROJECT_NAME is the project name to select. The interactive prompt is used if<br/>the name is omitted \(default).

**Usage:**

```bash
neuro config switch-project [OPTIONS] [PROJECT_NAME]
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




## neuro disk

Operations with disks.

**Usage:**

```bash
neuro disk [OPTIONS] COMMAND [ARGS]...
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|


**Commands:**

|Usage|Description|
|---|---|
| _[neuro disk create](#neuro-disk-create)_| Create a disk |
| _[neuro disk get](#neuro-disk-get)_| Get disk DISK_ID |
| _[neuro disk ls](#neuro-disk-ls)_| List disks |
| _[neuro disk rm](#neuro-disk-rm)_| Remove disk DISK_ID |




### neuro disk create

Create a disk<br/><br/>Create a disk with at least storage amount STORAGE.<br/><br/>To specify the amount, you can use the following suffixes: "kKMGTPEZY" To use<br/>decimal quantities, append "b" or "B". For example: - 1K or 1k is 1024 bytes -<br/>1Kb or 1KB is 1000 bytes - 20G is 20 * 2 ^ 30 bytes - 20Gb or 20GB is<br/>20.000.000.000 bytes<br/><br/>Note that server can have big granularity \(for example, 1G) so it will<br/>possibly round-up the amount you requested.<br/>

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

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_--cluster CLUSTER_|Perform in a specified cluster \(the current cluster by default).|
|_--name NAME_|Optional disk name|
|_--org ORG_|Perform in a specified org \(the current org by default).|
|_--project PROJECT_|Create disk in a specified project \(the current project by default).|
|_\--timeout-unused TIMEDELTA_|Optional disk lifetime limit after last usage in the format '1d2h3m4s' \(some parts may be missing). Set '0' to disable. Default value '1d' can be changed in the user config.|




### neuro disk get

Get disk DISK_ID.

**Usage:**

```bash
neuro disk get [OPTIONS] DISK
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_--cluster CLUSTER_|Look on a specified cluster \(the current cluster by default).|
|_\--full-uri_|Output full disk URI.|




### neuro disk ls

List disks.

**Usage:**

```bash
neuro disk ls [OPTIONS]
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_--cluster CLUSTER_|Look on a specified cluster \(the current cluster by default).|
|_\--full-uri_|Output full disk URI.|
|_\--long-format_|Output all info about disk.|
|_--project PROJECT_|Look on a specified project \(all projects in current cluster by default).|




### neuro disk rm

Remove disk DISK_ID.

**Usage:**

```bash
neuro disk rm [OPTIONS] DISKS...
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_--cluster CLUSTER_|Perform on a specified cluster \(the current cluster by default).|




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
| _[neuro image digest](#neuro-image-digest)_| Get digest of an image from remote registry |
| _[neuro image ls](#neuro-image-ls)_| List images |
| _[neuro image pull](#neuro-image-pull)_| Pull an image from platform registry |
| _[neuro image push](#neuro-image-push)_| Push an image to platform registry |
| _[neuro image rm](#neuro-image-rm)_| Remove image from platform registry |
| _[neuro image size](#neuro-image-size)_| Get image size |
| _[neuro image tags](#neuro-image-tags)_| List tags for image in platform registry |




### neuro image digest

Get digest of an image from remote registry<br/><br/>Image name must be URL with image:// scheme. Image name must contain tag.<br/>

**Usage:**

```bash
neuro image digest [OPTIONS] IMAGE
```

**Examples:**

```bash

neuro image digest image:/other-project/alpine:shared
neuro image digest image:myimage:latest

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
|_--cluster CLUSTER_|Show images on a specified cluster \(the current cluster by default).|
|_-l_|List in long format.|
|_\--full-uri_|Output full image URI.|
|_\-n, --name PATTERN_|Filter out images by name regex.|
|_--project PROJECT_|Filter out images by project \(multiple option, all projects in current cluster by default).|




### neuro image pull

Pull an image from platform registry.<br/><br/>Remote image name must be URL with image:// scheme. Image names can contain<br/>tag.<br/>

**Usage:**

```bash
neuro image pull [OPTIONS] REMOTE_IMAGE [LOCAL_IMAGE]
```

**Examples:**

```bash

neuro pull image:myimage
neuro pull image:/other-project/alpine:shared
neuro pull image:/project/my-alpine:production alpine:from-registry

```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro image push

Push an image to platform registry.<br/><br/>Remote image must be URL with image:// scheme. Image names can contain tag. If<br/>tags not specified 'latest' will be used as value.<br/>

**Usage:**

```bash
neuro image push [OPTIONS] LOCAL_IMAGE [REMOTE_IMAGE]
```

**Examples:**

```bash

neuro push myimage
neuro push alpine:latest image:my-alpine:production
neuro push alpine image:/other-project/alpine:shared

```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro image rm

Remove image from platform registry.<br/><br/>Image name must be URL with image:// scheme. Image name must contain tag.<br/>

**Usage:**

```bash
neuro image rm [OPTIONS] IMAGES...
```

**Examples:**

```bash

neuro image rm image:/other-project/alpine:shared
neuro image rm image:myimage:latest

```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_-f_|Force deletion of all tags referencing the image.|




### neuro image size

Get image size<br/><br/>Image name must be URL with image:// scheme. Image name must contain tag.<br/>

**Usage:**

```bash
neuro image size [OPTIONS] IMAGE
```

**Examples:**

```bash

neuro image size image:/other-project/alpine:shared
neuro image size image:myimage:latest

```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro image tags

List tags for image in platform registry.<br/><br/>Image name must be URL with image:// scheme.<br/>

**Usage:**

```bash
neuro image tags [OPTIONS] IMAGE
```

**Examples:**

```bash

neuro image tags image:/other-project/alpine
neuro image tags -l image:myimage

```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_-l_|List in long format, with image sizes.|




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
| _[neuro job attach](#neuro-job-attach)_| Attach terminal to a job |
| _[neuro job browse](#neuro-job-browse)_| Opens a job's URL in a web browser |
| _[neuro job bump\-life-span](#neuro-job-bump-life-span)_| Increase job life span |
| _[neuro job exec](#neuro-job-exec)_| Execute command in a running job |
| _[neuro job generate\-run-command](#neuro-job-generate-run-command)_| Generate command that will rerun given job |
| _[neuro job kill](#neuro-job-kill)_| Kill job\(s) |
| _[neuro job logs](#neuro-job-logs)_| Print the logs for a job |
| _[neuro job ls](#neuro-job-ls)_| List all jobs |
| _[neuro job port-forward](#neuro-job-port-forward)_| Forward port\(s) of a job |
| _[neuro job run](#neuro-job-run)_| Run a job |
| _[neuro job save](#neuro-job-save)_| Save job's state to an image |
| _[neuro job status](#neuro-job-status)_| Display status of a job |
| _[neuro job top](#neuro-job-top)_| Display GPU/CPU/Memory usage |




### neuro job attach

Attach terminal to a job<br/><br/>Attach local standard input, output, and error streams to a running job.

**Usage:**

```bash
neuro job attach [OPTIONS] JOB
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_\--port-forward LOCAL\_PORT:REMOTE_RORT_|Forward port\(s) of a running job to local port\(s) \(use multiple times for forwarding several ports)|




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




### neuro job bump-life-span

Increase job life span

**Usage:**

```bash
neuro job bump-life-span [OPTIONS] JOB TIMEDELTA
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro job exec

Execute command in a running job.<br/>

**Usage:**

```bash
neuro job exec [OPTIONS] JOB -- CMD...
```

**Examples:**

```bash

# Provides a shell to the container:
neuro exec my-job -- /bin/bash

# Executes a single command in the container and returns the control:
neuro exec --no-tty my-job -- ls -l

```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_\-t, --tty / -T, --no-tty_|Allocate a TTY, can be useful for interactive jobs. By default is on if the command is executed from a terminal, non-tty mode is used if executed from a script.|




### neuro job generate-run-command

Generate command that will rerun given job.<br/>

**Usage:**

```bash
neuro job generate-run-command [OPTIONS] JOB
```

**Examples:**

```bash

# You can use the following to directly re-execute it:
eval $(neuro job generate-run-command <job-id>)

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




### neuro job logs

Print the logs for a job.

**Usage:**

```bash
neuro job logs [OPTIONS] JOB
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_--since DATE\_OR_TIMEDELTA_|Only return logs after a specific date \(including). Use value of format '1d2h3m4s' to specify moment in past relatively to current time.|
|_--timestamps_|Include timestamps on each line in the log output.|




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
|_--help_|Show this message and exit.|
|_\-a, --all_|Show all jobs regardless the status.|
|_--cluster CLUSTER_|Show jobs on a specified cluster \(the current cluster by default).|
|_\-d, --description DESCRIPTION_|Filter out jobs by description \(exact match).|
|_--distinct_|Show only first job if names are same.|
|_--format COLUMNS_|Output table format, see "neuro help ps\-format" for more info about the format specification. The default can be changed using the job.ps-format configuration variable documented in "neuro help user-config"|
|_\--full-uri_|Output full image URI.|
|_\-n, --name NAME_|Filter out jobs by name.|
|_\-o, --owner TEXT_|Filter out jobs by owner \(multiple option). Supports `ME` option to filter by the current user.|
|_\-p, --project PROJECT_|Filter out jobs by project name \(multiple option).|
|_\--recent-first / --recent-last_|Show newer jobs first or last|
|_--since DATE\_OR_TIMEDELTA_|Show jobs created after a specific date \(including). Use value of format '1d2h3m4s' to specify moment in past relatively to current time.|
|_\-s, --status \[pending &#124; suspended &#124; running &#124; succeeded &#124; failed &#124; cancelled]_|Filter out jobs by status \(multiple option).|
|_\-t, --tag TAG_|Filter out jobs by tag \(multiple option)|
|_--until DATE\_OR_TIMEDELTA_|Show jobs created before a specific date \(including). Use value of format '1d2h3m4s' to specify moment in past relatively to current time.|
|_\-w, --wide_|Do not cut long lines for terminal width.|




### neuro job port-forward

Forward port\(s) of a job.<br/><br/>Forwards port\(s) of a running job to local port\(s).<br/>

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

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro job run

Run a job<br/><br/>IMAGE docker image name to run in a job.<br/><br/>CMD list will be passed as arguments to the executed job's image.<br/>

**Usage:**

```bash
neuro job run [OPTIONS] IMAGE [-- CMD...]
```

**Examples:**

```bash

# Starts a container pytorch/pytorch:latest on a machine with smaller GPU resources
# (see exact values in `neuro config show`) and with two volumes mounted:
#   storage:/<home-directory>   --> /var/storage/home (in read-write mode),
#   storage:/neuromation/public --> /var/storage/neuromation (in read-only mode).
neuro run --preset=gpu-small --volume=storage::/var/storage/home:rw \
--volume=storage:/neuromation/public:/var/storage/home:ro pytorch/pytorch:latest

# Starts a container using the custom image my-ubuntu:latest stored in neuro
# registry, run /script.sh and pass arg1 and arg2 as its arguments:
neuro run -s cpu-small --entrypoint=/script.sh image:my-ubuntu:latest -- arg1 arg2

```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_--browse_|Open a job's URL in a web browser|
|_--cluster CLUSTER_|Run job in a specified cluster|
|_\-d, --description DESC_|Optional job description in free format|
|_--detach_|Don't attach to job logs and don't wait for exit code|
|_\--energy-schedule NAME_|Run job only within a selected energy schedule. Selected preset should have scheduler enabled.|
|_--entrypoint TEXT_|Executable entrypoint in the container \(note that it overwrites `ENTRYPOINT` and `CMD` instructions of the docker image)|
|_\-e, --env VAR=VAL_|Set environment variable in container. Use multiple options to define more than one variable. See `neuro help secrets` for information about passing secrets as environment variables.|
|_\--env-file PATH_|File with environment variables to pass|
|_\-x, --extshm / -X, --no-extshm_|Request extended '/dev/shm' space  \[default: x]|
|_\--http-auth / --no-http-auth_|Enable HTTP authentication for forwarded HTTP port  \[default: True]|
|_\--http-port PORT_|Enable HTTP port forwarding to container  \[default: 80]|
|_\--life-span TIMEDELTA_|Optional job run-time limit in the format '1d2h3m4s' \(some parts may be missing). Set '0' to disable. Default value '1d' can be changed in the user config.|
|_\-n, --name NAME_|Optional job name|
|_--org ORG_|Run job in a specified org|
|_\--pass-config / --no-pass-config_|Upload neuro config to the job  \[default: no\-pass-config]|
|_\--port-forward LOCAL\_PORT:REMOTE_RORT_|Forward port\(s) of a running job to local port\(s) \(use multiple times for forwarding several ports)|
|_\-s, --preset PRESET_|Predefined resource configuration \(to see available values, run `neuro config show`)|
|_--priority \[low &#124; normal &#124; high]_|Priority used to specify job's start order. Jobs with higher priority will start before ones with lower priority. Priority should be supported by cluster.|
|_--privileged_|Run job in privileged mode, if it is supported by cluster.|
|_\-p, --project PROJECT_|Run job in a specified project.|
|_\--restart \[never &#124; on-failure &#124; always]_|Restart policy to apply when a job exits  \[default: never]|
|_\--schedule-timeout TIMEDELTA_|Optional job schedule timeout in the format '3m4s' \(some parts may be missing).|
|_--share USER_|Share job write permissions to user or role.|
|_--tag TAG_|Optional job tag, multiple values allowed|
|_\-t, --tty / -T, --no-tty_|Allocate a TTY, can be useful for interactive jobs. By default is on if the command is executed from a terminal, non-tty mode is used if executed from a script.|
|_\-v, --volume MOUNT_|Mounts directory from vault into container. Use multiple options to mount more than one volume. See `neuro help secrets` for information about passing secrets as mounted files.|
|_\--wait-for-seat / --no-wait-for-seat_|Wait for total running jobs quota  \[default: no\-wait-for-seat]|
|_\--wait-start / --no-wait-start_|Wait for a job start or failure  \[default: wait-start]|
|_\-w, --workdir TEXT_|Working directory inside the container|




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
|_\--full-uri_|Output full URI.|




### neuro job top

Display GPU/CPU/Memory usage.<br/>

**Usage:**

```bash
neuro job top [OPTIONS] [JOBS]...
```

**Examples:**

```bash

neuro top
neuro top job-1 job-2
neuro top --owner=user-1 --owner=user-2
neuro top --name my-experiments-v1
neuro top -t tag1 -t tag2

```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_--cluster CLUSTER_|Show jobs on a specified cluster \(the current cluster by default).|
|_\-d, --description DESCRIPTION_|Filter out jobs by description \(exact match).|
|_--format COLUMNS_|Output table format, see "neuro help top\-format" for more info about the format specification. The default can be changed using the job.top-format configuration variable documented in "neuro help user-config"|
|_\--full-uri_|Output full image URI.|
|_\-n, --name NAME_|Filter out jobs by name.|
|_\-o, --owner TEXT_|Filter out jobs by owner \(multiple option). Supports `ME` option to filter by the current user. Specify `ALL` to show jobs of all users.|
|_\-p, --project PROJECT_|Filter out jobs by project name \(multiple option).|
|_--since DATE\_OR_TIMEDELTA_|Show jobs created after a specific date \(including). Use value of format '1d2h3m4s' to specify moment in past relatively to current time.|
|_--sort COLUMNS_|Sort rows by specified column. Add "-" prefix to revert the sorting order. Multiple columns can be specified \(comma separated).  \[default: cpu]|
|_\-t, --tag TAG_|Filter out jobs by tag \(multiple option)|
|_--timeout FLOAT_|Maximum allowed time for executing the command, 0 for no timeout  \[default: 0]|
|_--until DATE\_OR_TIMEDELTA_|Show jobs created before a specific date \(including). Use value of format '1d2h3m4s' to specify moment in past relatively to current time.|




## neuro secret

Operations with secrets.

**Usage:**

```bash
neuro secret [OPTIONS] COMMAND [ARGS]...
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|


**Commands:**

|Usage|Description|
|---|---|
| _[neuro secret add](#neuro-secret-add)_| Add secret KEY with data VALUE |
| _[neuro secret ls](#neuro-secret-ls)_| List secrets |
| _[neuro secret rm](#neuro-secret-rm)_| Remove secret KEY |




### neuro secret add

Add secret KEY with data VALUE.<br/><br/>If VALUE starts with @ it points to a file with secrets content.<br/>

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

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_--cluster CLUSTER_|Perform on a specified cluster \(the current cluster by default).|
|_--org ORG_|Look on a specified org \(the current org by default).|




### neuro secret ls

List secrets.

**Usage:**

```bash
neuro secret ls [OPTIONS]
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_--cluster CLUSTER_|Look on a specified cluster \(the current cluster by default).|
|_\--full-uri_|Output full disk URI.|




### neuro secret rm

Remove secret KEY.

**Usage:**

```bash
neuro secret rm [OPTIONS] KEY
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_--cluster CLUSTER_|Perform on a specified cluster \(the current cluster by default).|
|_--org ORG_|Look on a specified org \(the current org by default).|




## neuro service-account

Operations with service accounts.

**Usage:**

```bash
neuro service-account [OPTIONS] COMMAND [ARGS]...
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|


**Commands:**

|Usage|Description|
|---|---|
| _[neuro service-account create](#neuro-service-account-create)_| Create a service account |
| _[neuro service-account get](#neuro-service-account-get)_| Get service account SERVICE_ACCOUNT |
| _[neuro service-account ls](#neuro-service-account-ls)_| List service accounts |
| _[neuro service-account rm](#neuro-service-account-rm)_| Remove service accounts SERVICE_ACCOUNT |




### neuro service-account create

Create a service account.

**Usage:**

```bash
neuro service-account create [OPTIONS]
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_\--default-cluster CLUSTER_|Service account default cluster. Current cluster will be used if not specified|
|_\--default-org ORG_|Service account default organization. Current org will be used if not specified|
|_\--default-project PROJECT_|Service account default project. Current project will be used if not specified|
|_--name NAME_|Optional service account name|




### neuro service-account get

Get service account SERVICE_ACCOUNT.

**Usage:**

```bash
neuro service-account get [OPTIONS] SERVICE_ACCOUNT
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro service-account ls

List service accounts.

**Usage:**

```bash
neuro service-account ls [OPTIONS]
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




### neuro service-account rm

Remove service accounts SERVICE_ACCOUNT.

**Usage:**

```bash
neuro service-account rm [OPTIONS] SERVICE_ACCOUNTS...
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
| _[neuro storage df](#neuro-storage-df)_| Show current storage usage |
| _[neuro storage glob](#neuro-storage-glob)_| List resources that match PATTERNS |
| _[neuro storage ls](#neuro-storage-ls)_| List directory contents |
| _[neuro storage mkdir](#neuro-storage-mkdir)_| Make directories |
| _[neuro storage mv](#neuro-storage-mv)_| Move or rename files and directories |
| _[neuro storage rm](#neuro-storage-rm)_| Remove files or directories |
| _[neuro storage tree](#neuro-storage-tree)_| List storage in a tree-like format |




### neuro storage cp

Copy files and directories.<br/><br/>Either SOURCES or DESTINATION should have storage:// scheme. If scheme is<br/>omitted, file:// scheme is assumed.<br/><br/>Use /dev/stdin and /dev/stdout file names to copy a file from terminal and<br/>print the content of file on the storage to console.<br/><br/>Any number of \--exclude and --include options can be passed.  The filters that<br/>appear later in the command take precedence over filters that appear earlier<br/>in the command.  If neither \--exclude nor --include options are specified the<br/>default can be changed using the storage.cp-exclude configuration variable<br/>documented in "neuro help user-config".<br/>

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

# download other project's remote file into the current directory
neuro cp storage:/{project}/foo.txt .

# download only files with extension `.out` into the current directory
neuro cp storage:results/*.out .

```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_--continue_|Continue copying partially-copied files.|
|_\--exclude-from-files FILES_|A list of file names that contain patterns for exclusion files and directories. Used only for uploading. The default can be changed using the storage.cp\-exclude-from-files configuration variable documented in "neuro help user-config"|
|_--exclude TEXT_|Exclude files and directories that match the specified pattern.|
|_--include TEXT_|Don't exclude files and directories that match the specified pattern.|
|_\--glob / --no-glob_|Expand glob patterns in SOURCES with explicit scheme.  \[default: glob]|
|_\-T, --no-target-directory_|Treat DESTINATION as a normal file.|
|_\-p, --progress / -P, --no-progress_|Show progress, on by default in TTY mode, off otherwise.|
|_\-r, --recursive_|Recursive copy, off by default|
|_\-t, --target-directory DIRECTORY_|Copy all SOURCES into DIRECTORY.|
|_\-u, --update_|Copy only when the SOURCE file is newer than the destination file or when the destination file is missing.|




### neuro storage df

Show current storage usage.<br/><br/>If PATH is specified, show storage usage of which path is a part.

**Usage:**

```bash
neuro storage df [OPTIONS] [PATH]
```

**Options:**

Name | Description|
|----|------------|
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




### neuro storage ls

List directory contents.<br/><br/>By default PATH is equal project's dir \(storage:)

**Usage:**

```bash
neuro storage ls [OPTIONS] [PATHS]...
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_\-d, --directory_|list directories themselves, not their contents.|
|_-l_|use a long listing format.|
|_\-h, --human-readable_|with -l print human readable sizes \(e.g., 2K, 540M).|
|_\-a, --all_|do not ignore entries starting with .|
|_--sort \[name &#124; size &#124; time]_|sort by given field, default is name.|




### neuro storage mkdir

Make directories.

**Usage:**

```bash
neuro storage mkdir [OPTIONS] PATHS...
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_\-p, --parents_|No error if existing, make parent directories as needed|




### neuro storage mv

Move or rename files and directories.<br/><br/>SOURCE must contain path to the file or directory existing on the storage, and<br/>DESTINATION must contain the full path to the target file or directory.<br/>

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

# move remote file into other project's directory
neuro mv storage:foo.txt storage:/{project}/bar.dat

# move remote file from other project's directory
neuro mv storage:/{project}/foo.txt storage:bar.dat

```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_\--glob / --no-glob_|Expand glob patterns in SOURCES  \[default: glob]|
|_\-T, --no-target-directory_|Treat DESTINATION as a normal file|
|_\-t, --target-directory DIRECTORY_|Copy all SOURCES into DIRECTORY|




### neuro storage rm

Remove files or directories.<br/>

**Usage:**

```bash
neuro storage rm [OPTIONS] PATHS...
```

**Examples:**

```bash

neuro rm storage:foo/bar
neuro rm storage:/{project}/foo/bar
neuro rm storage://{cluster}/{project}/foo/bar
neuro rm --recursive storage:/{project}/foo/
neuro rm storage:foo/**/*.tmp

```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_\--glob / --no-glob_|Expand glob patterns in PATHS  \[default: glob]|
|_\-p, --progress / -P, --no-progress_|Show progress, on by default in TTY mode, off otherwise.|
|_\-r, --recursive_|remove directories and their contents recursively|




### neuro storage tree

List storage in a tree-like format<br/><br/>Tree is a recursive directory listing program that produces a depth indented<br/>listing of files, which is colorized ala dircolors if the LS_COLORS<br/>environment variable is set and output is to tty.  With no arguments, tree<br/>lists the files in the storage: directory.  When directory arguments are<br/>given, tree lists all the files and/or directories found in the given<br/>directories each in turn.  Upon completion of listing all files/directories<br/>found, tree returns the total number of files and/or directories listed.<br/><br/>By default PATH is equal project's dir \(storage:)

**Usage:**

```bash
neuro storage tree [OPTIONS] [PATH]
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_\-h, --human-readable_|Print the size in a more human readable way.|
|_\-a, --all_|do not ignore entries starting with .|
|_\-s, --size_|Print the size in bytes of each file.|
|_--sort \[name &#124; size &#124; time]_|sort by given field, default is name|




## neuro attach

Attach terminal to a job<br/><br/>Attach local standard input, output, and error streams to a running job.

**Usage:**

```bash
neuro attach [OPTIONS] JOB
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_\--port-forward LOCAL\_PORT:REMOTE_RORT_|Forward port\(s) of a running job to local port\(s) \(use multiple times for forwarding several ports)|




## neuro cp

Copy files and directories.<br/><br/>Either SOURCES or DESTINATION should have storage:// scheme. If scheme is<br/>omitted, file:// scheme is assumed.<br/><br/>Use /dev/stdin and /dev/stdout file names to copy a file from terminal and<br/>print the content of file on the storage to console.<br/><br/>Any number of \--exclude and --include options can be passed.  The filters that<br/>appear later in the command take precedence over filters that appear earlier<br/>in the command.  If neither \--exclude nor --include options are specified the<br/>default can be changed using the storage.cp-exclude configuration variable<br/>documented in "neuro help user-config".<br/>

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

# download other project's remote file into the current directory
neuro cp storage:/{project}/foo.txt .

# download only files with extension `.out` into the current directory
neuro cp storage:results/*.out .

```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_--continue_|Continue copying partially-copied files.|
|_\--exclude-from-files FILES_|A list of file names that contain patterns for exclusion files and directories. Used only for uploading. The default can be changed using the storage.cp\-exclude-from-files configuration variable documented in "neuro help user-config"|
|_--exclude TEXT_|Exclude files and directories that match the specified pattern.|
|_--include TEXT_|Don't exclude files and directories that match the specified pattern.|
|_\--glob / --no-glob_|Expand glob patterns in SOURCES with explicit scheme.  \[default: glob]|
|_\-T, --no-target-directory_|Treat DESTINATION as a normal file.|
|_\-p, --progress / -P, --no-progress_|Show progress, on by default in TTY mode, off otherwise.|
|_\-r, --recursive_|Recursive copy, off by default|
|_\-t, --target-directory DIRECTORY_|Copy all SOURCES into DIRECTORY.|
|_\-u, --update_|Copy only when the SOURCE file is newer than the destination file or when the destination file is missing.|




## neuro exec

Execute command in a running job.<br/>

**Usage:**

```bash
neuro exec [OPTIONS] JOB -- CMD...
```

**Examples:**

```bash

# Provides a shell to the container:
neuro exec my-job -- /bin/bash

# Executes a single command in the container and returns the control:
neuro exec --no-tty my-job -- ls -l

```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_\-t, --tty / -T, --no-tty_|Allocate a TTY, can be useful for interactive jobs. By default is on if the command is executed from a terminal, non-tty mode is used if executed from a script.|




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
|_--cluster CLUSTER_|Show images on a specified cluster \(the current cluster by default).|
|_-l_|List in long format.|
|_\--full-uri_|Output full image URI.|
|_\-n, --name PATTERN_|Filter out images by name regex.|
|_--project PROJECT_|Filter out images by project \(multiple option, all projects in current cluster by default).|




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




## neuro logs

Print the logs for a job.

**Usage:**

```bash
neuro logs [OPTIONS] JOB
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_--since DATE\_OR_TIMEDELTA_|Only return logs after a specific date \(including). Use value of format '1d2h3m4s' to specify moment in past relatively to current time.|
|_--timestamps_|Include timestamps on each line in the log output.|




## neuro ls

List directory contents.<br/><br/>By default PATH is equal project's dir \(storage:)

**Usage:**

```bash
neuro ls [OPTIONS] [PATHS]...
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_\-d, --directory_|list directories themselves, not their contents.|
|_-l_|use a long listing format.|
|_\-h, --human-readable_|with -l print human readable sizes \(e.g., 2K, 540M).|
|_\-a, --all_|do not ignore entries starting with .|
|_--sort \[name &#124; size &#124; time]_|sort by given field, default is name.|




## neuro mkdir

Make directories.

**Usage:**

```bash
neuro mkdir [OPTIONS] PATHS...
```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_\-p, --parents_|No error if existing, make parent directories as needed|




## neuro mv

Move or rename files and directories.<br/><br/>SOURCE must contain path to the file or directory existing on the storage, and<br/>DESTINATION must contain the full path to the target file or directory.<br/>

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

# move remote file into other project's directory
neuro mv storage:foo.txt storage:/{project}/bar.dat

# move remote file from other project's directory
neuro mv storage:/{project}/foo.txt storage:bar.dat

```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_\--glob / --no-glob_|Expand glob patterns in SOURCES  \[default: glob]|
|_\-T, --no-target-directory_|Treat DESTINATION as a normal file|
|_\-t, --target-directory DIRECTORY_|Copy all SOURCES into DIRECTORY|




## neuro port-forward

Forward port\(s) of a job.<br/><br/>Forwards port\(s) of a running job to local port\(s).<br/>

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

Name | Description|
|----|------------|
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
|_--help_|Show this message and exit.|
|_\-a, --all_|Show all jobs regardless the status.|
|_--cluster CLUSTER_|Show jobs on a specified cluster \(the current cluster by default).|
|_\-d, --description DESCRIPTION_|Filter out jobs by description \(exact match).|
|_--distinct_|Show only first job if names are same.|
|_--format COLUMNS_|Output table format, see "neuro help ps\-format" for more info about the format specification. The default can be changed using the job.ps-format configuration variable documented in "neuro help user-config"|
|_\--full-uri_|Output full image URI.|
|_\-n, --name NAME_|Filter out jobs by name.|
|_\-o, --owner TEXT_|Filter out jobs by owner \(multiple option). Supports `ME` option to filter by the current user.|
|_\-p, --project PROJECT_|Filter out jobs by project name \(multiple option).|
|_\--recent-first / --recent-last_|Show newer jobs first or last|
|_--since DATE\_OR_TIMEDELTA_|Show jobs created after a specific date \(including). Use value of format '1d2h3m4s' to specify moment in past relatively to current time.|
|_\-s, --status \[pending &#124; suspended &#124; running &#124; succeeded &#124; failed &#124; cancelled]_|Filter out jobs by status \(multiple option).|
|_\-t, --tag TAG_|Filter out jobs by tag \(multiple option)|
|_--until DATE\_OR_TIMEDELTA_|Show jobs created before a specific date \(including). Use value of format '1d2h3m4s' to specify moment in past relatively to current time.|
|_\-w, --wide_|Do not cut long lines for terminal width.|




## neuro pull

Pull an image from platform registry.<br/><br/>Remote image name must be URL with image:// scheme. Image names can contain<br/>tag.<br/>

**Usage:**

```bash
neuro pull [OPTIONS] REMOTE_IMAGE [LOCAL_IMAGE]
```

**Examples:**

```bash

neuro pull image:myimage
neuro pull image:/other-project/alpine:shared
neuro pull image:/project/my-alpine:production alpine:from-registry

```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|




## neuro push

Push an image to platform registry.<br/><br/>Remote image must be URL with image:// scheme. Image names can contain tag. If<br/>tags not specified 'latest' will be used as value.<br/>

**Usage:**

```bash
neuro push [OPTIONS] LOCAL_IMAGE [REMOTE_IMAGE]
```

**Examples:**

```bash

neuro push myimage
neuro push alpine:latest image:my-alpine:production
neuro push alpine image:/other-project/alpine:shared

```

**Options:**

Name | Description|
|----|------------|
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
neuro rm storage:/{project}/foo/bar
neuro rm storage://{cluster}/{project}/foo/bar
neuro rm --recursive storage:/{project}/foo/
neuro rm storage:foo/**/*.tmp

```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_\--glob / --no-glob_|Expand glob patterns in PATHS  \[default: glob]|
|_\-p, --progress / -P, --no-progress_|Show progress, on by default in TTY mode, off otherwise.|
|_\-r, --recursive_|remove directories and their contents recursively|




## neuro run

Run a job<br/><br/>IMAGE docker image name to run in a job.<br/><br/>CMD list will be passed as arguments to the executed job's image.<br/>

**Usage:**

```bash
neuro run [OPTIONS] IMAGE [-- CMD...]
```

**Examples:**

```bash

# Starts a container pytorch/pytorch:latest on a machine with smaller GPU resources
# (see exact values in `neuro config show`) and with two volumes mounted:
#   storage:/<home-directory>   --> /var/storage/home (in read-write mode),
#   storage:/neuromation/public --> /var/storage/neuromation (in read-only mode).
neuro run --preset=gpu-small --volume=storage::/var/storage/home:rw \
--volume=storage:/neuromation/public:/var/storage/home:ro pytorch/pytorch:latest

# Starts a container using the custom image my-ubuntu:latest stored in neuro
# registry, run /script.sh and pass arg1 and arg2 as its arguments:
neuro run -s cpu-small --entrypoint=/script.sh image:my-ubuntu:latest -- arg1 arg2

```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_--browse_|Open a job's URL in a web browser|
|_--cluster CLUSTER_|Run job in a specified cluster|
|_\-d, --description DESC_|Optional job description in free format|
|_--detach_|Don't attach to job logs and don't wait for exit code|
|_\--energy-schedule NAME_|Run job only within a selected energy schedule. Selected preset should have scheduler enabled.|
|_--entrypoint TEXT_|Executable entrypoint in the container \(note that it overwrites `ENTRYPOINT` and `CMD` instructions of the docker image)|
|_\-e, --env VAR=VAL_|Set environment variable in container. Use multiple options to define more than one variable. See `neuro help secrets` for information about passing secrets as environment variables.|
|_\--env-file PATH_|File with environment variables to pass|
|_\-x, --extshm / -X, --no-extshm_|Request extended '/dev/shm' space  \[default: x]|
|_\--http-auth / --no-http-auth_|Enable HTTP authentication for forwarded HTTP port  \[default: True]|
|_\--http-port PORT_|Enable HTTP port forwarding to container  \[default: 80]|
|_\--life-span TIMEDELTA_|Optional job run-time limit in the format '1d2h3m4s' \(some parts may be missing). Set '0' to disable. Default value '1d' can be changed in the user config.|
|_\-n, --name NAME_|Optional job name|
|_--org ORG_|Run job in a specified org|
|_\--pass-config / --no-pass-config_|Upload neuro config to the job  \[default: no\-pass-config]|
|_\--port-forward LOCAL\_PORT:REMOTE_RORT_|Forward port\(s) of a running job to local port\(s) \(use multiple times for forwarding several ports)|
|_\-s, --preset PRESET_|Predefined resource configuration \(to see available values, run `neuro config show`)|
|_--priority \[low &#124; normal &#124; high]_|Priority used to specify job's start order. Jobs with higher priority will start before ones with lower priority. Priority should be supported by cluster.|
|_--privileged_|Run job in privileged mode, if it is supported by cluster.|
|_\-p, --project PROJECT_|Run job in a specified project.|
|_\--restart \[never &#124; on-failure &#124; always]_|Restart policy to apply when a job exits  \[default: never]|
|_\--schedule-timeout TIMEDELTA_|Optional job schedule timeout in the format '3m4s' \(some parts may be missing).|
|_--share USER_|Share job write permissions to user or role.|
|_--tag TAG_|Optional job tag, multiple values allowed|
|_\-t, --tty / -T, --no-tty_|Allocate a TTY, can be useful for interactive jobs. By default is on if the command is executed from a terminal, non-tty mode is used if executed from a script.|
|_\-v, --volume MOUNT_|Mounts directory from vault into container. Use multiple options to mount more than one volume. See `neuro help secrets` for information about passing secrets as mounted files.|
|_\--wait-for-seat / --no-wait-for-seat_|Wait for total running jobs quota  \[default: no\-wait-for-seat]|
|_\--wait-start / --no-wait-start_|Wait for a job start or failure  \[default: wait-start]|
|_\-w, --workdir TEXT_|Working directory inside the container|




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




## neuro share

Shares resource with another user.<br/><br/>URI shared resource.<br/><br/>USER username to share resource with.<br/><br/>PERMISSION sharing access right: read, write, or manage.<br/>

**Usage:**

```bash
neuro share [OPTIONS] URI USER {read|write|manage}
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
|_\--full-uri_|Output full URI.|




## neuro top

Display GPU/CPU/Memory usage.<br/>

**Usage:**

```bash
neuro top [OPTIONS] [JOBS]...
```

**Examples:**

```bash

neuro top
neuro top job-1 job-2
neuro top --owner=user-1 --owner=user-2
neuro top --name my-experiments-v1
neuro top -t tag1 -t tag2

```

**Options:**

Name | Description|
|----|------------|
|_--help_|Show this message and exit.|
|_--cluster CLUSTER_|Show jobs on a specified cluster \(the current cluster by default).|
|_\-d, --description DESCRIPTION_|Filter out jobs by description \(exact match).|
|_--format COLUMNS_|Output table format, see "neuro help top\-format" for more info about the format specification. The default can be changed using the job.top-format configuration variable documented in "neuro help user-config"|
|_\--full-uri_|Output full image URI.|
|_\-n, --name NAME_|Filter out jobs by name.|
|_\-o, --owner TEXT_|Filter out jobs by owner \(multiple option). Supports `ME` option to filter by the current user. Specify `ALL` to show jobs of all users.|
|_\-p, --project PROJECT_|Filter out jobs by project name \(multiple option).|
|_--since DATE\_OR_TIMEDELTA_|Show jobs created after a specific date \(including). Use value of format '1d2h3m4s' to specify moment in past relatively to current time.|
|_--sort COLUMNS_|Sort rows by specified column. Add "-" prefix to revert the sorting order. Multiple columns can be specified \(comma separated).  \[default: cpu]|
|_\-t, --tag TAG_|Filter out jobs by tag \(multiple option)|
|_--timeout FLOAT_|Maximum allowed time for executing the command, 0 for no timeout  \[default: 0]|
|_--until DATE\_OR_TIMEDELTA_|Show jobs created before a specific date \(including). Use value of format '1d2h3m4s' to specify moment in past relatively to current time.|



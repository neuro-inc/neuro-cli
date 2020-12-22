# admin

Cluster administration commands

## Usage

```bash
neuro admin [OPTIONS] COMMAND [ARGS]...
```

Cluster administration commands.

**Commands:**
| Usage | Description |
| :--- | :--- |
| [_get-clusters_](admin.md#get-clusters) | Print the list of available clusters |
| [_generate-cluster-config_](admin.md#generate-cluster-config) | Create a cluster configuration file |
| [_add-cluster_](admin.md#add-cluster) | Create a new cluster and start its... |
| [_show-cluster-options_](admin.md#show-cluster-options) | Create a cluster configuration file |
| [_get-cluster-users_](admin.md#get-cluster-users) | Print the list of all users in the cluster... |
| [_add-cluster-user_](admin.md#add-cluster-user) | Add user access to specified cluster |
| [_remove-cluster-user_](admin.md#remove-cluster-user) | Remove user access from the cluster |
| [_set-user-quota_](admin.md#set-user-quota) | Set user quota to given values |
| [_add-user-quota_](admin.md#add-user-quota) | Add given values to user quota |
| [_update-resource-preset_](admin.md#update-resource-preset) | Add/update resource preset |
| [_remove-resource-preset_](admin.md#remove-resource-preset) | Remove resource preset |


### get-clusters

Print the list of available clusters


#### Usage

```bash
neuro admin get-clusters [OPTIONS]
```

Print the list of available clusters.

#### Options

| Name | Description |
| :--- | :--- |
| _`--help`_ | Show this message and exit. |



### generate-cluster-config

Create a cluster configuration file


#### Usage

```bash
neuro admin generate-cluster-config [OPTIONS] [CONFIG]
```

Create a cluster configuration file.

#### Options

| Name | Description |
| :--- | :--- |
| _`--help`_ | Show this message and exit. |
| _`--type \[aws | gcp | azure\]`_ |  |



### add-cluster

Create a new cluster and start its...


#### Usage

```bash
neuro admin add-cluster [OPTIONS] CLUSTER_NAME CONFIG
```

Create a new cluster and start its provisioning.

#### Options

| Name | Description |
| :--- | :--- |
| _`--help`_ | Show this message and exit. |



### show-cluster-options

Create a cluster configuration file


#### Usage

```bash
neuro admin show-cluster-options [OPTIONS]
```

Create a cluster configuration file.

#### Options

| Name | Description |
| :--- | :--- |
| _`--help`_ | Show this message and exit. |
| _`--type \[aws | gcp | azure\]`_ |  |



### get-cluster-users

Print the list of all users in the cluster...


#### Usage

```bash
neuro admin get-cluster-users [OPTIONS] [CLUSTER_NAME]
```

Print the list of all users in the cluster with their assigned role.

#### Options

| Name | Description |
| :--- | :--- |
| _`--help`_ | Show this message and exit. |



### add-cluster-user

Add user access to specified cluster


#### Usage

```bash
neuro admin add-cluster-user [OPTIONS] CLUSTER_NAME USER_NAME [ROLE]
```

Add user access to specified cluster.

The command supports one of 3 user
roles: admin, manager or user.

#### Options

| Name | Description |
| :--- | :--- |
| _`--help`_ | Show this message and exit. |



### remove-cluster-user

Remove user access from the cluster


#### Usage

```bash
neuro admin remove-cluster-user [OPTIONS] CLUSTER_NAME USER_NAME
```

Remove user access from the cluster.

#### Options

| Name | Description |
| :--- | :--- |
| _`--help`_ | Show this message and exit. |



### set-user-quota

Set user quota to given values


#### Usage

```bash
neuro admin set-user-quota [OPTIONS] CLUSTER_NAME USER_NAME
```

Set user quota to given values

#### Options

| Name | Description |
| :--- | :--- |
| _`--help`_ | Show this message and exit. |
| _`-g`, `--gpu AMOUNT`_ | GPU quota value in hours \(h\) or minutes \(m\). |
| _`-j`, `--jobs AMOUNT`_ | Maximum running jobs quota |
| _`-n`, `--non-gpu AMOUNT`_ | Non-GPU quota value in hours \(h\) or minutes \(m\). |



### add-user-quota

Add given values to user quota


#### Usage

```bash
neuro admin add-user-quota [OPTIONS] CLUSTER_NAME USER_NAME
```

Add given values to user quota

#### Options

| Name | Description |
| :--- | :--- |
| _`--help`_ | Show this message and exit. |
| _`-g`, `--gpu AMOUNT`_ | Additional GPU quota value in hours \(h\) or minutes \(m\). |
| _`-n`, `--non-gpu AMOUNT`_ | Additional non-GPU quota value in hours \(h\) or minutes \(m\). |



### update-resource-preset

Add/update resource preset


#### Usage

```bash
neuro admin update-resource-preset [OPTIONS] CLUSTER_NAME PRESET_NAME
```

Add/update resource preset

#### Options

| Name | Description |
| :--- | :--- |
| _`--help`_ | Show this message and exit. |
| _`-c`, `--cpu NUMBER`_ | Number of CPUs  \_\[default: 0.1\]\_ |
| _`-g`, `--gpu NUMBER`_ | Number of GPUs |
| _`--gpu-model MODEL`_ | GPU model |
| _`-m`, `--memory AMOUNT`_ | Memory amount  \_\[default: 1G\]\_ |
| _`-p`, `--preemptible` / `-P`, `--non-preemptible`_ | Job preemptability support  \_\[default: False\]\_ |
| _`--preemptible-node` / `--non-preemptible-node`_ | Use a lower-cost preemptible instance  \_\[default: False\]\_ |
| _`--tpu-sw-version VERSION`_ | TPU software version |
| _`--tpu-type TYPE`_ | TPU type |



### remove-resource-preset

Remove resource preset


#### Usage

```bash
neuro admin remove-resource-preset [OPTIONS] CLUSTER_NAME PRESET_NAME
```

Remove resource preset

#### Options

| Name | Description |
| :--- | :--- |
| _`--help`_ | Show this message and exit. |



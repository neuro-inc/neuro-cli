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
| [_add-cluster_](admin.md#add-cluster) | Create a new cluster |
| [_add-cluster-user_](admin.md#add-cluster-user) | Add user access to specified cluster |
| [_add-org_](admin.md#add-org) | Create a new org |
| [_add-org-cluster_](admin.md#add-org-cluster) | Add org access to specified cluster |
| [_add-org-cluster-credits_](admin.md#add-org-cluster-credits) | Add given values to org cluster balance |
| [_add-org-user_](admin.md#add-org-user) | Add user access to specified org |
| [_add-resource-preset_](admin.md#add-resource-preset) | Add new resource preset |
| [_add-user-credits_](admin.md#add-user-credits) | Add given values to user quota |
| [_generate-cluster-config_](admin.md#generate-cluster-config) | Create a cluster configuration file |
| [_get-cluster-users_](admin.md#get-cluster-users) | List users in specified cluster |
| [_get-clusters_](admin.md#get-clusters) | Print the list of available clusters |
| [_get-org-cluster-quota_](admin.md#get-org-cluster-quota) | Get info about org quota in given cluster |
| [_get-org-clusters_](admin.md#get-org-clusters) | Print the list of all orgs in the cluster |
| [_get-org-users_](admin.md#get-org-users) | List users in specified org |
| [_get-orgs_](admin.md#get-orgs) | Print the list of available orgs |
| [_get-user-quota_](admin.md#get-user-quota) | Get info about user quota in given cluster |
| [_remove-cluster_](admin.md#remove-cluster) | Drop a cluster |
| [_remove-cluster-user_](admin.md#remove-cluster-user) | Remove user access from the cluster |
| [_remove-org_](admin.md#remove-org) | Drop a org |
| [_remove-org-user_](admin.md#remove-org-user) | Remove user access from the org |
| [_remove-resource-preset_](admin.md#remove-resource-preset) | Remove resource preset |
| [_set-org-cluster-credits_](admin.md#set-org-cluster-credits) | Set org cluster credits to given value |
| [_set-org-cluster-quota_](admin.md#set-org-cluster-quota) | Set org cluster quota to given values |
| [_set-user-credits_](admin.md#set-user-credits) | Set user credits to given value |
| [_set-user-quota_](admin.md#set-user-quota) | Set user quota to given values |
| [_show-cluster-options_](admin.md#show-cluster-options) | Show available cluster options |
| [_update-cluster_](admin.md#update-cluster) | Update a cluster |
| [_update-org-cluster_](admin.md#update-org-cluster) | Update org cluster quotas |
| [_update-resource-preset_](admin.md#update-resource-preset) | Update existing resource preset |


### add-cluster

Create a new cluster


#### Usage

```bash
neuro admin add-cluster [OPTIONS] CLUSTER_NAME CONFIG
```

Create a new cluster.

Creates cluster entry on admin side and then start its
provisioning using
provided config.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--default-credits AMOUNT_ | Default credits amount to set \(`unlimited' stands for no limit\)  _\[default: unlimited\]_ |
| _--default-jobs AMOUNT_ | Default maximum running jobs quota \(`unlimited' stands for no limit\)  _\[default: unlimited\]_ |



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
| _--help_ | Show this message and exit. |
| _-c, --credits AMOUNT_ | Credits amount to set \(`unlimited' stands for no limit\) |
| _-j, --jobs AMOUNT_ | Maximum running jobs quota \(`unlimited' stands for no limit\) |
| _--org ORG_ | org name for org-cluster users |



### add-org

Create a new org


#### Usage

```bash
neuro admin add-org [OPTIONS] ORG_NAME
```

Create a new org.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |



### add-org-cluster

Add org access to specified cluster


#### Usage

```bash
neuro admin add-org-cluster [OPTIONS] CLUSTER_NAME ORG_NAME
```

Add org access to specified cluster.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _-c, --credits AMOUNT_ | Credits amount to set \(`unlimited' stands for no limit\)  _\[default: unlimited\]_ |
| _--default-credits AMOUNT_ | Default credits amount to set \(`unlimited' stands for no limit\)  _\[default: unlimited\]_ |
| _--default-jobs AMOUNT_ | Default maximum running jobs quota \(`unlimited' stands for no limit\)  _\[default: unlimited\]_ |
| _-j, --jobs AMOUNT_ | Maximum running jobs quota \(`unlimited' stands for no limit\)  _\[default: unlimited\]_ |
| _--storage-size AMOUNT_ | Storage size, ignored for storage types with elastic storage size |



### add-org-cluster-credits

Add given values to org cluster balance


#### Usage

```bash
neuro admin add-org-cluster-credits [OPTIONS] CLUSTER_NAME ORG_NAME
```

Add given values to org cluster balance

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _-c, --credits AMOUNT_ | Credits amount to add |



### add-org-user

Add user access to specified org


#### Usage

```bash
neuro admin add-org-user [OPTIONS] ORG_NAME USER_NAME [ROLE]
```

Add user access to specified org.

The command supports one of 3 user roles:
admin, manager or user.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |



### add-resource-preset

Add new resource preset


#### Usage

```bash
neuro admin add-resource-preset [OPTIONS] PRESET_NAME
```

Add new resource preset

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _-c, --cpu NUMBER_ | Number of CPUs  _\[default: 0.1\]_ |
| _--credits-per-hour AMOUNT_ | Price of running job of this preset for an hour in credits  _\[default: 0\]_ |
| _-g, --gpu NUMBER_ | Number of GPUs |
| _--gpu-model MODEL_ | GPU model |
| _-m, --memory AMOUNT_ | Memory amount  _\[default: 1G\]_ |
| _--preemptible-node / --non-preemptible-node_ | Use a lower-cost preemptible instance  _\[default: non-preemptible-node\]_ |
| _-p, --scheduler / -P, --no-scheduler_ | Use round robin scheduler for jobs  _\[default: no-scheduler\]_ |
| _--tpu-sw-version VERSION_ | TPU software version |
| _--tpu-type TYPE_ | TPU type |



### add-user-credits

Add given values to user quota


#### Usage

```bash
neuro admin add-user-credits [OPTIONS] CLUSTER_NAME USER_NAME
```

Add given values to user quota

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _-c, --credits AMOUNT_ | Credits amount to add  _\[required\]_ |
| _--org ORG_ | org name for org-cluster users |



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
| _--help_ | Show this message and exit. |
| _--type \[aws &#124; gcp &#124; azure &#124; vcd\]_ |  |



### get-cluster-users

List users in specified cluster


#### Usage

```bash
neuro admin get-cluster-users [OPTIONS] [CLUSTER_NAME]
```

List users in specified cluster

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--org ORG_ | org name for org-cluster users |



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
| _--help_ | Show this message and exit. |



### get-org-cluster-quota

Get info about org quota in given cluster


#### Usage

```bash
neuro admin get-org-cluster-quota [OPTIONS] CLUSTER_NAME ORG_NAME
```

Get info about org quota in given cluster

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |



### get-org-clusters

Print the list of all orgs in the cluster


#### Usage

```bash
neuro admin get-org-clusters [OPTIONS] CLUSTER_NAME
```

Print the list of all orgs in the cluster

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |



### get-org-users

List users in specified org


#### Usage

```bash
neuro admin get-org-users [OPTIONS] ORG_NAME
```

List users in specified org

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |



### get-orgs

Print the list of available orgs


#### Usage

```bash
neuro admin get-orgs [OPTIONS]
```

Print the list of available orgs.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |



### get-user-quota

Get info about user quota in given cluster


#### Usage

```bash
neuro admin get-user-quota [OPTIONS] CLUSTER_NAME USER_NAME
```

Get info about user quota in given cluster

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--org ORG_ | org name for org-cluster users |



### remove-cluster

Drop a cluster


#### Usage

```bash
neuro admin remove-cluster [OPTIONS] CLUSTER_NAME
```

Drop a cluster

Completely removes cluster from the system.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--force_ | Skip prompt |



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
| _--help_ | Show this message and exit. |
| _--org ORG_ | org name for org-cluster users |



### remove-org

Drop a org


#### Usage

```bash
neuro admin remove-org [OPTIONS] ORG_NAME
```

Drop a org

Completely removes org from the system.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--force_ | Skip prompt |



### remove-org-user

Remove user access from the org


#### Usage

```bash
neuro admin remove-org-user [OPTIONS] ORG_NAME USER_NAME
```

Remove user access from the org.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |



### remove-resource-preset

Remove resource preset


#### Usage

```bash
neuro admin remove-resource-preset [OPTIONS] PRESET_NAME
```

Remove resource preset

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |



### set-org-cluster-credits

Set org cluster credits to given value


#### Usage

```bash
neuro admin set-org-cluster-credits [OPTIONS] CLUSTER_NAME ORG_NAME
```

Set org cluster credits to given value

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _-c, --credits AMOUNT_ | Credits amount to set \(`unlimited' stands for no limit\)  _\[required\]_ |



### set-org-cluster-quota

Set org cluster quota to given values


#### Usage

```bash
neuro admin set-org-cluster-quota [OPTIONS] CLUSTER_NAME ORG_NAME
```

Set org cluster quota to given values

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _-j, --jobs AMOUNT_ | Maximum running jobs quota \(`unlimited' stands for no limit\)  _\[required\]_ |



### set-user-credits

Set user credits to given value


#### Usage

```bash
neuro admin set-user-credits [OPTIONS] CLUSTER_NAME USER_NAME
```

Set user credits to given value

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _-c, --credits AMOUNT_ | Credits amount to set \(`unlimited' stands for no limit\)  _\[required\]_ |
| _--org ORG_ | org name for org-cluster users |



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
| _--help_ | Show this message and exit. |
| _-j, --jobs AMOUNT_ | Maximum running jobs quota \(`unlimited' stands for no limit\)  _\[required\]_ |
| _--org ORG_ | org name for org-cluster users |



### show-cluster-options

Show available cluster options


#### Usage

```bash
neuro admin show-cluster-options [OPTIONS]
```

Show available cluster options.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--type \[aws &#124; gcp &#124; azure\]_ |  |



### update-cluster

Update a cluster


#### Usage

```bash
neuro admin update-cluster [OPTIONS] CLUSTER_NAME
```

Update a cluster.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--default-credits AMOUNT_ | Default credits amount to set \(`unlimited' stands for no limit\)  _\[default: unlimited\]_ |
| _--default-jobs AMOUNT_ | Default maximum running jobs quota \(`unlimited' stands for no limit\)  _\[default: unlimited\]_ |



### update-org-cluster

Update org cluster quotas


#### Usage

```bash
neuro admin update-org-cluster [OPTIONS] CLUSTER_NAME ORG_NAME
```

Update org cluster quotas.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _-c, --credits AMOUNT_ | Credits amount to set \(`unlimited' stands for no limit\)  _\[default: unlimited\]_ |
| _--default-credits AMOUNT_ | Default credits amount to set \(`unlimited' stands for no limit\)  _\[default: unlimited\]_ |
| _--default-jobs AMOUNT_ | Default maximum running jobs quota \(`unlimited' stands for no limit\)  _\[default: unlimited\]_ |
| _-j, --jobs AMOUNT_ | Maximum running jobs quota \(`unlimited' stands for no limit\)  _\[default: unlimited\]_ |



### update-resource-preset

Update existing resource preset


#### Usage

```bash
neuro admin update-resource-preset [OPTIONS] PRESET_NAME
```

Update existing resource preset

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _-c, --cpu NUMBER_ | Number of CPUs |
| _--credits-per-hour AMOUNT_ | Price of running job of this preset for an hour in credits |
| _-g, --gpu NUMBER_ | Number of GPUs |
| _--gpu-model MODEL_ | GPU model |
| _-m, --memory AMOUNT_ | Memory amount |
| _--preemptible-node / --non-preemptible-node_ | Use a lower-cost preemptible instance |
| _-p, --scheduler / -P, --no-scheduler_ | Use round robin scheduler for jobs |
| _--tpu-sw-version VERSION_ | TPU software version |
| _--tpu-type TYPE_ | TPU type |



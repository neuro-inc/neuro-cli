# acl

Access Control List management

## Usage

```bash
neuro acl [OPTIONS] COMMAND [ARGS]...
```

Access Control List management.

**Commands:**
| Usage | Description |
| :--- | :--- |
| [_grant_](acl.md#grant) | Shares resource with another user |
| [_revoke_](acl.md#revoke) | Revoke user access from another user |
| [_list_](acl.md#list) | List shared resources |
| [_add-role_](acl.md#add-role) | Add new role |
| [_remove-role_](acl.md#remove-role) | Remove existing role |


### grant

Shares resource with another user


#### Usage

```bash
neuro acl grant [OPTIONS] URI USER {read|write|manage}
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

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |



### revoke

Revoke user access from another user


#### Usage

```bash
neuro acl revoke [OPTIONS] URI USER
```

Revoke user access from another user.

`URI` previously shared resource to
revoke.

`USER` to revoke `URI` resource from.

#### Examples

```bash
$ neuro acl revoke storage:///sample_data/ alice
$ neuro acl revoke image:resnet50 bob
$ neuro acl revoke job:///my_job_id alice
```

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |



### list

List shared resources


#### Usage

```bash
neuro acl list [OPTIONS] [URI]
```

List shared resources.

The command displays a list of resources shared BY
current user (default).

To display a list of resources shared `WITH` current
user apply --shared option.

#### Examples

```bash
$ neuro acl list
$ neuro acl list storage://
$ neuro acl list --shared
$ neuro acl list --shared image://
```

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--full-uri_ | Output full URI. |
| _-s, --scheme TEXT_ | Filter resources by scheme, e.g. job, storage, image or user. Deprecated, use the uri argument instead. |
| _--shared_ | Output the resources shared by the user. |
| _-u TEXT_ | Use specified user or role. |



### add-role

Add new role


#### Usage

```bash
neuro acl add-role [OPTIONS] ROLE_NAME
```

Add new role.

#### Examples

```bash
$ neuro acl add-role mycompany/subdivision
```

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |



### remove-role

Remove existing role


#### Usage

```bash
neuro acl remove-role [OPTIONS] ROLE_NAME
```

Remove existing role.

#### Examples

```bash
$ neuro acl remove-role mycompany/subdivision
```

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |



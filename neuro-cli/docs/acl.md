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
| [_add-role_](acl.md#add-role) | Add new role |
| [_grant_](acl.md#grant) | Shares resource with another user |
| [_list-roles_](acl.md#list-roles) | List roles |
| [_ls_](acl.md#ls) | List shared resources |
| [_remove-role_](acl.md#remove-role) | Remove existing role |
| [_revoke_](acl.md#revoke) | Revoke user access from another user |


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



### list-roles

List roles


#### Usage

```bash
neuro acl list-roles [OPTIONS]
```

List roles.

#### Examples

```bash
$ neuro acl list-roles
$ neuro acl list-roles username/projects
```

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _-u TEXT_ | Fetch roles of specified user or role. |



### ls

List shared resources


#### Usage

```bash
neuro acl ls [OPTIONS] [URI]
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
| _--shared_ | Output the resources shared by the user. |
| _-u TEXT_ | Use specified user or role. |



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



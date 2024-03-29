# config

Client configuration

## Usage

```bash
neuro config [OPTIONS] COMMAND [ARGS]...
```

Client configuration.

**Commands:**
| Usage | Description |
| :--- | :--- |
| [_aliases_](config.md#aliases) | List available command aliases |
| [_docker_](config.md#docker) | Configure local docker client |
| [_get-clusters_](config.md#get-clusters) | List available clusters/org pairs |
| [_login_](config.md#login) | Log into Neuro Platform |
| [_login-headless_](config.md#login-headless) | Log into Neuro Platform in non-GUI environ |
| [_login-with-token_](config.md#login-with-token) | Log into Neuro Platform with token |
| [_logout_](config.md#logout) | Log out |
| [_show_](config.md#show) | Print current settings |
| [_show-token_](config.md#show-token) | Print current authorization token |
| [_switch-cluster_](config.md#switch-cluster) | Switch the active cluster |
| [_switch-org_](config.md#switch-org) | Switch the active organization |
| [_switch-project_](config.md#switch-project) | Switch the active project |


### aliases

List available command aliases


#### Usage

```bash
neuro config aliases [OPTIONS]
```

List available command aliases.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |



### docker

Configure local docker client


#### Usage

```bash
neuro config docker [OPTIONS]
```

Configure local docker client

This command configures local docker client to
use Neuro Platform's docker registry.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--docker-config PATH_ | Specifies the location of the Docker client configuration files |



### get-clusters

List available clusters/org pairs


#### Usage

```bash
neuro config get-clusters [OPTIONS]
```

List available clusters/org pairs.

This command re-fetches cluster list and
then displays each
cluster with available orgs.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |



### login

Log into Neuro Platform


#### Usage

```bash
neuro config login [OPTIONS] [URL]
```

Log into Neuro Platform.

`URL` is a platform entrypoint `URL`.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |



### login-headless

Log into Neuro Platform in non-GUI environ


#### Usage

```bash
neuro config login-headless [OPTIONS] [URL]
```

Log into Neuro Platform in non`-GUI` environ

`URL` is a platform entrypoint
`URL`.

The command works similar to "neuro login" but instead of
opening a
browser for performing OAuth registration prints
an `URL` that should be open
on guest host.

Then user inputs a code displayed in a browser after
successful login
back in neuro command to finish the login process.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |



### login-with-token

Log into Neuro Platform with token


#### Usage

```bash
neuro config login-with-token [OPTIONS] TOKEN [URL]
```

Log into Neuro Platform with token.

`TOKEN` is authentication token provided
by administration team.
`URL` is a platform entrypoint `URL`.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |



### logout

Log out


#### Usage

```bash
neuro config logout [OPTIONS]
```

Log out.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |



### show

Print current settings


#### Usage

```bash
neuro config show [OPTIONS]
```

Print current settings.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--energy_ | Including cluster energy consumption and CO2 emissions information |



### show-token

Print current authorization token


#### Usage

```bash
neuro config show-token [OPTIONS]
```

Print current authorization token.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |



### switch-cluster

Switch the active cluster


#### Usage

```bash
neuro config switch-cluster [OPTIONS] [CLUSTER_NAME]
```

Switch the active cluster.

`CLUSTER`_`NAME` is the cluster name to select.
The interactive prompt is used if the
name is omitted (default).

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |



### switch-org

Switch the active organization


#### Usage

```bash
neuro config switch-org [OPTIONS] ORG_NAME
```

Switch the active organization.

`ORG`_`NAME` is the organization name to
select. Use literal "NO_`ORG`" to switch
to using current cluster directly
instead of on behalf of some org.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |



### switch-project

Switch the active project


#### Usage

```bash
neuro config switch-project [OPTIONS] [PROJECT_NAME]
```

Switch the active project.

`PROJECT`_`NAME` is the project name to select.
The interactive prompt is used if the
name is omitted (default).

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |



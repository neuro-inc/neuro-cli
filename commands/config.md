# config

Client configuration

## Usage

```bash
apolo config [OPTIONS] COMMAND [ARGS]...
```

Client configuration.

**Commands:**

| Usage | Description |
| :--- | :--- |
| [_login_](config.md#login) | Log into Apolo Platform |
| [_login-with-token_](config.md#login-with-token) | Log into Apolo Platform with token |
| [_login-headless_](config.md#login-headless) | Log into Apolo Platform from non-GUI server... |
| [_show_](config.md#show) | Print current settings |
| [_show-token_](config.md#show-token) | Print current authorization token |
| [_show-quota_](config.md#show-quota) | Print quota and remaining computation time... |
| [_aliases_](config.md#aliases) | List available command aliases |
| [_get-clusters_](config.md#get-clusters) | Fetch and display the list of available... |
| [_switch-cluster_](config.md#switch-cluster) | Switch the active cluster |
| [_docker_](config.md#docker) | Configure docker client to fit the Apolo... |
| [_logout_](config.md#logout) | Log out |

### login

Log into Apolo Platform

#### Usage

```bash
apolo config login [OPTIONS] [URL]
```

Log into Apolo Platform.

`URL` is a platform entrypoint `URL`.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

### login-with-token

Log into Apolo Platform with token

#### Usage

```bash
apolo config login-with-token [OPTIONS] TOKEN [URL]
```

Log into Apolo Platform with token.

`TOKEN` is authentication token provided by administration team. `URL` is a platform entrypoint `URL`.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

### login-headless

Log into Apolo Platform from non-GUI server...

#### Usage

```bash
apolo config login-headless [OPTIONS] [URL]
```

Log into Apolo Platform from non`-GUI` server environment.

`URL` is a platform entrypoint `URL`.

The command works similar to "apolo login" but instead of opening a browser for performing OAuth registration prints an `URL` that should be open on guest host.

Then user inputs a code displayed in a browser after successful login back in apolo command to finish the login process.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

### show

Print current settings

#### Usage

```bash
apolo config show [OPTIONS]
```

Print current settings.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

### show-token

Print current authorization token

#### Usage

```bash
apolo config show-token [OPTIONS]
```

Print current authorization token.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

### show-quota

Print quota and remaining computation time...

#### Usage

```bash
apolo config show-quota [OPTIONS] [USER]
```

Print quota and remaining computation time for active cluster.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

### aliases

List available command aliases

#### Usage

```bash
apolo config aliases [OPTIONS]
```

List available command aliases.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

### get-clusters

Fetch and display the list of available...

#### Usage

```bash
apolo config get-clusters [OPTIONS]
```

Fetch and display the list of available clusters.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

### switch-cluster

Switch the active cluster

#### Usage

```bash
apolo config switch-cluster [OPTIONS] [CLUSTER_NAME]
```

Switch the active cluster.

`CLUSTER`\_`NAME` is the cluster name to select. The interactive prompt is used if the name is omitted \(default\).

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

### docker

Configure docker client to fit the Apolo...

#### Usage

```bash
apolo config docker [OPTIONS]
```

Configure docker client to fit the Apolo Platform.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--docker-config PATH_ | Specifies the location of the Docker client configuration files |

### logout

Log out

#### Usage

```bash
apolo config logout [OPTIONS]
```

Log out.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |


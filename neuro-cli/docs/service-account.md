# service-account

Operations with service accounts

## Usage

```bash
neuro service-account [OPTIONS] COMMAND [ARGS]...
```

Operations with service accounts.

**Commands:**
| Usage | Description |
| :--- | :--- |
| [_ls_](service-account.md#ls) | List service accounts |
| [_create_](service-account.md#create) | Create a service account |
| [_get_](service-account.md#get) | Get service account SERVICE\_ACCOUNT |
| [_rm_](service-account.md#rm) | Remove service accounts SERVICE\_ACCOUNT |


### ls

List service accounts


#### Usage

```bash
neuro service-account ls [OPTIONS]
```

List service accounts.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |



### create

Create a service account


#### Usage

```bash
neuro service-account create [OPTIONS] ROLE
```

Create a service account.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--default-cluster CLUSTER\_NAME_ | Service account default cluster. Current cluster will be used if not specified |
| _--name NAME_ | Optional service account name |



### get

Get service account SERVICE_ACCOUNT


#### Usage

```bash
neuro service-account get [OPTIONS] SERVICE_ACCOUNT
```

Get service account `SERVICE`_`ACCOUNT`.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |



### rm

Remove service accounts SERVICE_ACCOUNT


#### Usage

```bash
neuro service-account rm [OPTIONS] SERVICE_ACCOUNTS...
```

Remove service accounts `SERVICE`_`ACCOUNT`.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |



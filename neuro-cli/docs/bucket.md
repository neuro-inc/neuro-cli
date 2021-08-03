# bucket

Operations with buckets

## Usage

```bash
neuro bucket [OPTIONS] COMMAND [ARGS]...
```

Operations with buckets.

**Commands:**
| Usage | Description |
| :--- | :--- |
| [_ls_](bucket.md#ls) | List buckets |
| [_create_](bucket.md#create) | Create a new bucket |
| [_get_](bucket.md#get) | Get bucket BUCKET\_ID |
| [_rm_](bucket.md#rm) | Remove bucket DISK\_ID |


### ls

List buckets


#### Usage

```bash
neuro bucket ls [OPTIONS]
```

List buckets.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--cluster CLUSTER_ | Look on a specified cluster \(the current cluster by default\). |
| _--full-uri_ | Output full bucket URI. |



### create

Create a new bucket


#### Usage

```bash
neuro bucket create [OPTIONS]
```

Create a new bucket.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--cluster CLUSTER_ | Perform in a specified cluster \(the current cluster by default\). |
| _--name NAME_ | Optional bucket name |



### get

Get bucket BUCKET_ID


#### Usage

```bash
neuro bucket get [OPTIONS] BUCKET
```

Get bucket `BUCKET`_ID.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--cluster CLUSTER_ | Look on a specified cluster \(the current cluster by default\). |
| _--full-uri_ | Output full bucket URI. |



### rm

Remove bucket DISK_ID


#### Usage

```bash
neuro bucket rm [OPTIONS] BUCKETS...
```

Remove bucket `DISK`_ID.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--cluster CLUSTER_ | Perform on a specified cluster \(the current cluster by default\). |



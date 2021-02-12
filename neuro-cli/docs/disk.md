# disk

Operations with disks

## Usage

```bash
neuro disk [OPTIONS] COMMAND [ARGS]...
```

Operations with disks.

**Commands:**
| Usage | Description |
| :--- | :--- |
| [_ls_](disk.md#ls) | List disks |
| [_create_](disk.md#create) | Create a disk with at least storage amount... |
| [_get_](disk.md#get) | Get disk DISK\_ID |
| [_rm_](disk.md#rm) | Remove disk DISK\_ID |


### ls

List disks


#### Usage

```bash
neuro disk ls [OPTIONS]
```

List disks.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--full-uri_ | Output full disk URI. |
| _--long-format_ | Output all info about disk. |



### create

Create a disk with at least storage amount...


#### Usage

```bash
neuro disk create [OPTIONS] STORAGE
```

Create a disk with at least storage amount `STORAGE`.

To specify the amount,
you can use the following suffixes: "k`KMGTPEZY`"
To use decimal quantities,
append "b" or "B". For example:
- 1K or 1k is `1024` bytes
- 1Kb or `1KB` is
`1000` bytes
- `20G` is 20 * 2 ^ 30 bytes
- `20G`b or `20GB` is
20.`000`.`000`.`000` bytes

Note that server can have big granularity (for
example, 1G)
so it will possibly round-up the amount you requested.

#### Examples

```bash

$ neuro disk create 10G
$ neuro disk create 500M
```

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--name NAME_ | Optional disk name |
| _--timeout-unused TIMEDELTA_ | Optional disk lifetime limit after last usage in the format '1d2h3m4s' \(some parts may be missing\). Set '0' to disable. Default value '1d' can be changed in the user config. |



### get

Get disk DISK_ID


#### Usage

```bash
neuro disk get [OPTIONS] DISK
```

Get disk `DISK`_ID.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |
| _--full-uri_ | Output full disk URI. |



### rm

Remove disk DISK_ID


#### Usage

```bash
neuro disk rm [OPTIONS] DISKS...
```

Remove disk `DISK`_ID.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |



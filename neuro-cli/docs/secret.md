# secret

Operations with secrets

## Usage

```bash
neuro secret [OPTIONS] COMMAND [ARGS]...
```

Operations with secrets.

## Commands

* [neuro secret ls](secret.md#ls): List secrets
* [neuro secret add](secret.md#add): Add secret KEY with data VALUE
* [neuro secret rm](secret.md#rm): Remove secret KEY

### ls

List secrets

#### Usage

```bash
neuro secret ls [OPTIONS]
```

List secrets.

#### Options

| Name     | Description                 |
| -------- | --------------------------- |
| `--help` | Show this message and exit. |

### add

Add secret KEY with data VALUE

#### Usage

```bash
neuro secret add [OPTIONS] KEY VALUE
```

Add secret `KEY` with data `VALUE`.

If `VALUE` starts with @ it points to a
file with secrets content.

#### Examples

```bash

$ neuro secret add KEY_NAME VALUE
$ neuro secret add KEY_NAME @path/to/file.txt
```

#### Options

| Name     | Description                 |
| -------- | --------------------------- |
| `--help` | Show this message and exit. |

### rm

Remove secret KEY

#### Usage

```bash
neuro secret rm [OPTIONS] KEY
```

Remove secret `KEY`.

#### Options

| Name     | Description                 |
| -------- | --------------------------- |
| `--help` | Show this message and exit. |

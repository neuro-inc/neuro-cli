# secret

Operations with secrets

## Usage

```bash
neuro secret [OPTIONS] COMMAND [ARGS]...
```

Operations with secrets.

**Commands:**

| Usage | Description |
| :--- | :--- |
| [_ls_](secret.md#ls) | List secrets |
| [_add_](secret.md#add) | Add secret KEY with data VALUE |
| [_rm_](secret.md#rm) | Remove secret KEY |

### ls

List secrets

#### Usage

```bash
neuro secret ls [OPTIONS]
```

List secrets.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

### add

Add secret KEY with data VALUE

#### Usage

```bash
neuro secret add [OPTIONS] KEY VALUE
```

Add secret `KEY` with data `VALUE`.

If `VALUE` starts with @ it points to a file with secrets content.

#### Examples

```bash
$ neuro secret add KEY_NAME VALUE
$ neuro secret add KEY_NAME @path/to/file.txt
```

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |

### rm

Remove secret KEY

#### Usage

```bash
neuro secret rm [OPTIONS] KEY
```

Remove secret `KEY`.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |


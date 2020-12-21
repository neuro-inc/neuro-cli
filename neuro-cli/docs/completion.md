# completion

Output shell completion code

## Usage

```bash
neuro completion [OPTIONS] COMMAND [ARGS]...
```

Output shell completion code.

## Commands

* [neuro completion generate](completion.md#generate): Provide an instruction for shell completion...
* [neuro completion patch](completion.md#patch): Automatically patch shell configuration...

### generate

Provide an instruction for shell completion...

#### Usage

```bash
neuro completion generate [OPTIONS] [bash|zsh]
```

Provide an instruction for shell completion generation.

#### Options

| Name     | Description                 |
| -------- | --------------------------- |
| `--help` | Show this message and exit. |

### patch

Automatically patch shell configuration...

#### Usage

```bash
neuro completion patch [OPTIONS] [bash|zsh]
```

Automatically patch shell configuration profile to enable completion

#### Options

| Name     | Description                 |
| -------- | --------------------------- |
| `--help` | Show this message and exit. |

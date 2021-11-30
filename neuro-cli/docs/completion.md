# completion

Output shell completion code

## Usage

```bash
neuro completion [OPTIONS] COMMAND [ARGS]...
```

Output shell completion code.

**Commands:**
| Usage | Description |
| :--- | :--- |
| [_generate_](completion.md#generate) | Show instructions for shell completion |
| [_patch_](completion.md#patch) | Patch shell profile to enable completion |


### generate

Show instructions for shell completion


#### Usage

```bash
neuro completion generate [OPTIONS] {bash|zsh}
```

Show instructions for shell completion.

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |



### patch

Patch shell profile to enable completion


#### Usage

```bash
neuro completion patch [OPTIONS] {bash|zsh}
```

Patch shell profile to enable completion

Patches shell configuration while
depending of current shell.
Files patched:

bash: `~/.bashrc`
zsh: `~/.zshrc`

#### Options

| Name | Description |
| :--- | :--- |
| _--help_ | Show this message and exit. |



# Custom command aliases

Aliases exist to provide for abbreviating a system command, or for adding default arguments to a regularly used command.

Aliases are described in user-config files \(see `apolo help user-config` for details\).

`~/.neuro/user.toml` is used for **global** aliases, `.neuro.toml` can be used for saving **project-specific** aliases. Project aliases everrides global ones if the same alias name exists in both configuration files.

There are **internal** and **external** aliases. An **internal** alias executes built-in apolo command in-place, an  **external** alias executes any **system OS** command.

## Internal alias

The internal alias is used for running existing apolo CLI command under a different name and with optional overriden defaults \(passed predefined command-line options and arguments\).

For example, the following alias definition makes `apolo lsl` command that executes `apolo storage ls -hl` for listing the storage content using a long output mode with human-readable file sizes.

```text
  [alias.lsl]
  cmd = "ls -l --human-readable"
  help = "List directory contents in a long mode.
```

Available configuration arguments:

* `[alias.lsl]`: defines a subgroup for named alias,

  ```text
               `lsl` in this case.
  ```

* `cmd`: command to execute with provided overridden options,

  the key is **mandatory**.

  `cmd` key in alias section implies **internal alias** mode.

* `help`: help string, displayed by `apolo du --help`

  command \(optional\),

Internal allases accept additional command line options and agruments, these parameters are passed to underlying command as is.

E.g., `apolo lsl storage:directory` works as `apolo ls -l --human-readable storage:directory`

## External alias

The external alias spawns a subprocess with passing default options and arguments, all user-provided arguments are passed to underlying programm as well.

For example, the following configuration defines `apolo du` command as an alias for system `du --human-readable` with optional providing the directory for analyzing.

```text
  [alias.du]
  exec = "du"
  args = "[FILE]..."
  options = [
    "-h, --human-readable   print sizes in powers of 1024 (e.g., 1023M)",
    "-d, --max-depth=N  max recursion level for subdirectories lookup",
  ]
  help = '''
    Summarize disk usage of the set of FILEs,
    recursively for directories.
  '''
```

Available configuration arguments:

* `[alias.du]`: defines a subgroup for named alias,

  `du` in this case.

* `exec`: external command to execute, the key is **mandatory**.

  `exec` key in alias section implies **external alias** mode.

* `args`: positional args accepted by the alias,

  the format is described below \(optional\).

* `options`: options and flags accepted by the alias,

  the format is described below \(optional\).

* `help`: help string, displayed by `apolo lsl --help`

  command \(optional\),

**args** is string with sequence of arguments, e.g. `DIR SRC... [DST]`

If an argument is enclosed in brackets it is **optional** \(`[FILE]`\). If an argument is ended with ellipsis the argument accepts multiple values \(`SRC...`\)

**options** is a list of strings, a string per option.

Each string describes a single option, the options definition is separated from the option description \(help\) by two or more spaces.

The option definition can contain:

* short name \(`-h`\)
* long name \(`--human-readable`\)
* indication for required value \(`-d, --max-depth=N`\).

  If the required value indicator \(`=NAME`\) is absent

  the option is considered as boolean flag.

**exec** defines an external system to execute.

The command is spawn in a subprocess, Apolo CLI waits for the subprocess finish, and, in turn, returns the exit code to the outer caller.

The parameter may specify and executable file along with some options, e.g. `exec = "du --human-readable"` enforces human-readable mode for `du` command.

`exec` can be used in **simplified** and **pattern** mode.

## Pattern mode

In **pattern mode** the system command is used along with **substitutions**, e.g. `exec = "du {human_readable} {max_depth} {file}"`. Substitution is a variable name to expand enclosed in figure brackets, e.g. `{file}`.

It is expanded with an option or positional argument specified by `args` or `options`. The substitution name is automatically lowercased, minus \(`-`\) is replaced with underscore \(`_`\). E.g. `args = "ARG-NAME"` matches to `{arg_name}`.

If the substitution corresponds to optional parameter and it is not provided by user the substitution is expanded to empty string.

If the substitution corresponds to multiple values all of them are provided, e.g. `apolo du folder1 folder2` expands to `du folder1 folder2` since `[FILE]...` argument matches to `folder1 folder2` values.

Options are expanded using longest form if provided, e.g. `apolo du -h` is expanded to `du --human-readable`.

Options with values are expanded as well, e.g. `apolo du -d 1` is expanded to `du --max-depth 1`, `apolo du --max-depth 1` matches to the same command.

## Simplified mode

In **simplified mode** the `exec` value does not contain any **substitutions**. In this case all parsed `options` and `args` are appended to executed command automatically if provided, e.g. `exec = "du"` is expanded to `exec = "du {human_readable} {max_depth} {file}"`


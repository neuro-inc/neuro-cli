Custom command aliases
======================

Aliases provide a way to abbreviate system commands and
add default arguments to commonly used commands.

Aliases are described in user-config files
(see `apolo help user-config` for details).

`~/.apolo/user.toml` is used for **global** aliases, and
`.apolo.toml` can be used for saving **project-specific** aliases.
Project aliases overrides global ones if the same alias
name exists in both configuration files.

There are two types of aliases: **internal** and **external**.
**Internal** aliases execute built-in apolo commands, and  **
external** aliases execute **system OS** commands.

Internal aliases
----------------

Internal aliases are used for running existing apolo CLI commands under
a different name and with optional overriden defaults (passed predefined
command line options and arguments).

For example, the following alias definition creates a `apolo lsl` command
that executes `apolo storage ls -hl` to list the storage's content
using a long output mode with human-readable file sizes.

```
  [alias.lsl]
  cmd = "ls -l --human-readable"
  help = "List directory contents in a long mode.
```

Available configuration arguments:

* `[alias.lsl]`: Defines a subgroup for a named alias,
                   `lsl` in this case.
* `cmd`: The command to execute with provided overridden options,
  this key is **mandatory**.
  The `cmd` key in the alias section implies **internal alias** mode.
* `help`: Help string displayed by the `apolo lsl --help`
  command (optional).

Internal aliases accept additional command line options and agruments,
and pass them to the underlying command as is.

For example, `apolo lsl storage:directory` works as
`apolo ls -l --human-readable storage:directory`


External aliases
----------------

External aliases spawn a subprocess with passing default options and
arguments. All user-provided arguments are passed to the underlying
program as well.

For example, the following configuration defines `apolo du` command as
an alias for the system `du --human-readable` command with an additional
ability to specify a directory for analysis.

```
  [alias.du]
  exec = "du"
  args = "[FILE]..."
  options = [
    "-h, --human-readable   print sizes in powers of 1024 (e.g., 1024M)",
    "-d, --max-depth=N  max recursion level for subdirectories lookup",
  ]
  help = '''
    Summarize disk usage of the set of files,
    recursively for directories.
  '''
```

Available configuration arguments:

* `[alias.du]`: Defines a subgroup for a named alias,
  `du` in this case.
* `exec`: External command to execute, this key is **mandatory**.
  The `exec` key in the alias section implies **external alias** mode.
* `args`: Positional argumentss accepted by the alias,
  the format is described below (optional).
* `options`: Options and flags accepted by the alias,
  the format is described below (optional).
* `help`: Help string displayed by `apolo du --help`
  command (optional),

**args** is a string with a sequence of arguments, e.g. `DIR SRC... [DST]`

If an argument is enclosed in square brackets, it's **optional** (`[FILE]`).
If an argument ends with an ellipsis, this argument accepts
multiple values (`SRC...`)

**options** is a list of strings specifying various options.

Each string describes a single option. The option definitions should be separated
from the option descriptions (help) by two or more spaces.

An option definition can contain:
* Short name (`-h`)
* Long name (`--human-readable`)
* Indication of the required value type (`-d, --max-depth=N`).
  If the required value indicator (`=NAME`) is absent,
  the option will be considered a boolean flag.

**exec** defines an external system command to execute.

The command is spawned in a subprocess. Apolo CLI waits for the subprocess
to be finished, and then returns the exit code to the outer caller.

The parameter may specify an executable file along with some options.
For example, `exec = "du --human-readable"` enforces human-readable mode
for the `du` command.

`exec` can be used in **simplified** and **pattern** mode.

Pattern mode
------------

In **pattern mode**, the system command is used along with **substitutions**.
For example, `exec = "du {human_readable} {max_depth} {file}"`.
Substitution is enclosed in curly brackets and represents a variable name to expand,
e.g. `{file}`.

It's expanded with an option or positional argument specified
by `args` or `options`.  The substitution name is automatically lowercased,
and dashes (`-`) are replaced with underscores (`_`).
For example, `args = "ARG-NAME"` matches to `{arg_name}`.

If a substitution corresponds to an optional parameter not provided
by the user, this substitution will be expanded to an empty string.

If a substitution corresponds to multiple values, all of them are used.
For example, `apolo du folder1 folder2` expands to `du folder1 folder2` since
the `[FILE]...` argument matches to `folder1 folder2` values.

Options are expanded using the longest form if provided,
e.g. `apolo du -h` is expanded to `du --human-readable`.

Options with values are expanded as well,
e.g. `apolo du -d 1` is expanded to `du --max-depth 1`.
`apolo du --max-depth 1` matches to the same command.

Simplified mode
---------------

In **simplified mode**, the `exec` value does not contain any **substitutions**.
In this case, all parsed `options` and `args` are appended
to the executed command automatically if provided.
For example, `exec = "du"` is expanded to
`exec = "du {human_readable} {max_depth} {file}"`
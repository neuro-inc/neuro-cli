User configuration files
========================

The Neuro client supports custom configuration files that provide default values
for particular command options, user-defined command aliases, etc.

There are two types of configuration files that a project may have: **global** and
**local**. Both of these are completely optional.

The global file is located in the standard neuro config path. Neuro CLI uses the
`~/.neuro` folder by default, so the full path for the global config file is
`~/.neuro/user.toml`.

The local config file is named `.neuro.toml` and the CLI searches for this file
starting from the current folder up to the root directory.

Local and global configurations that were found by the CLI are then merged.
If a parameter is present both in the global and local versions, the local parameter
take precedence.

These configuration files must be written in the TOML format (which is a stricter
version of the well-known INI format). See `https://en.wikipedia.org/wiki/TOML` and
`https://github.com/toml-lang/toml#toml` for this format's specification details.

Supported configuration sections and parameters:

`[alias]` section
-----------------

A section for describing user-provided aliases.

See `neuro help aliases` for details about avaiable section contents.

`[job]` section
---------------

A section for `neuro job` command group settings.

**`cluster-name`**

The name of active cluster which overrides the global cluster name set by
`neuro config switch-cluster`.  Can only be specified in the **local**
configuration file.

**`org-name`**

The name of active organization which overrides the global organization
name set by `neuro config switch-org`.  Can only be specified in
the **local** configuration file. Use literal 'NO_ORG' to setup direct
access instead of on behalf of some organization.

**`ps-format`**

Default value for the `neuro ps --format=XXX` option.

See `neuro help ps-format` for information about the value's specification.

**`top-format`**

Default value for the `neuro top --format=XXX` option.

See `neuro help top-format` for information about the value's specification.

**`life-span`**

Default job runtime limit for the `neuro run --life-span=XXX` option.

The value is a string of the following format: `1d2h3m4s` (this example will set the
limit to 1 day, 2 hours, 3 minutes, and 4 seconds). Some parts of the value can be
omitted, for example: `1d6h`, `30m`, `4h30s`. No spaces are allowed between the
parts of the value.

`[storage]` section
-------------------

A section for `neuro storage` command group settings.

**`cp-exclude`**

Default value for the `neuro cp --exclude=XXX` and `neuro cp --include=YYY` options.

The value is a list of shell wildcard patterns. Files and folders that match these
patterns will be excluded from processing.

The pattern can contain `*` and `?`. For example, `["*.jpg"]` will exclude all
files with the `.jpg` extension.

Exclamation mark `!` is used to negate the pattern. For example, `["*.jpg",
"!main.jpg"]` will exclude all `.jpg` files except for `main.jpg`.

**`cp-exclude-from-files`**

Default value for the `neuro cp --exclude-from-files=XXX` option.

The value is a list of filenames that contain patterns for excluding files
and directories from being uploaded. For every processed folder,
patterns from the matched exclusion files (e.g., ".neuroignore")
are read and recursively applied to the directory content.

Default is `[".neuroignore"]`.

The format of these files is the same as the format of `.gitignore` files:
every line contains a pattern, and the exclamation mark `!` is used to negate
the pattern. Empty lines and lines which start with `#` are ignored.

`[disk]` section
----------------

A section for `neuro disk` command group settings.

**`life-span`**

Default disk lifetime limit for the `neuro disk create --life-span=XXX` option.

The value is a string of the following format: `1d2h3m4s` (this example will set the
limit to 1 day, 2 hours, 3 minutes, and 4 seconds). Some parts of the value can be
omitted, for example: `1d6h`, `30m`, `4h30s`. No spaces are allowed between the
parts of the value.

*Example:*
```
  # jobs section
  [job]
  ps-format = "{id;max=30}, {status;max=10}"
  life-span = "1d6h"

  # storage section
  [storage]
  cp-exclude = ["*.jpg", "!main.jpg"]
  cp-exclude-from-files = [".neuroignore", ".gitignore"]

  # jobs section
  [disk]
  life-span = "7d"
```
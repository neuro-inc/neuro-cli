# user-config

User configuration files
========================

The Neuro client supports user configuration files to provide default values
for particular command options, user defined command aliases etc.

There are two configuration files: **global** and **local**, both are optional
and can be absent.

The global file is located in the standard neuro config path.  "neuro" CLI uses
`~/.neuro` folder by default, the path for global config file is
`~/.neuro/user.toml`.

The local config file is named .neuro.toml, the CLI search for this file
starting from the current folder up to the root directory.

Found local and global configurations are merged.
If a parameter is present are both global and local versions the local parameter
take a precedence.

Configuration files have a TOML format (a stricter version of well-known INI
format). See `https://en.wikipedia.org/wiki/TOML` and
`https://github.com/toml-lang/toml#toml` for the format specification details.

Supported configuration sections and parameters:

`[alias]` section
-----------------

A section for describing user-provided aliases.

See `neuro help aliases` for details about avaiable section contents.

`[job]` section
---------------

A section for `neuro job` command group settings.

**`cluster-name`**

The name of active cluster which overrides global cluster name set by
`neuro config switch-cluster`.  Can only be specified in **local**
configuration file.

**`ps-format`**

Default value for `neuro ps --format=XXX` option.

See `neuro help ps-format` for information about the value specification.

**`life-span`**

Default job run-time limit for `neuro run --life-span=XXX` option.

The value is a string in format `1d2h3m4s` (this example will set the limit to
1 day, 2 hours, 3 minutes and 4 seconds). Some values can be missing, for example:
`1d6h`, `30m`. No spaces are allowed between values.

`[storage]` section
-------------------

A section for `neuro storage` command group settings.

**`cp-exclude`**

Default value for `neuro cp --exclude=XXX` and `neuro cp --include=YYY` options.

The value is a list of shell wildcard patterns, a file or folder that matches a
pattern is excluded from processing.

The pattern can contain `*` and `?`, e.g. `["*.jpg"]` is for exclusion of all
files with `.jpg` extension.

Exclamation mark ! is used to negate the pattern, e.g. `["*.jpg", "!main.jpg"]`
excludes all `.jpg` files except `main.jpg`.

**`cp-exclude-from-files`**

Default value for `neuro cp --exclude-from-files=XXX` option.

The value is a list of filenames that contain patterns for exclusion files
and directories from uploading. For every proceeded folder
patterns from matched exclusion files (e.g. ".neuroignore")
are read and recursively applied to the directory content.

Default is `[".neuroignore"]`.

The format of files is the same as the format of `.gitignore` files:
every line contains a pattern, exclamation mark `!` is used to negate
the pattern, empty lines and lines which start with `#` are ignored.

`[disk]` section
----------------

A section for `neuro disk` command group settings.

**`life-span`**

Default disk lifetime limit for `neuro disk create --life-span=XXX` option.

The value is a string in format `1d2h3m4s` (this example will set the limit to
1 day, 2 hours, 3 minutes and 4 seconds). Some values can be missing, for example:
`1d6h`, `30m`. No spaces are allowed between values.

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
# project

Project operations

## Usage

```bash
neuro project [OPTIONS] COMMAND [ARGS]...
```

Project operations.

**Commands:**
| Usage | Description |
| :--- | :--- |
| [_init_](project.md#init) | Initialize an empty project |


### init



Initialize an empty project



#### Usage

```bash
neuro project init [OPTIONS] [SLUG]
```

Initialize an empty project.

#### Examples

```bash

# Initializes a scaffolding for the new project with the recommended project
# structure (see http://github.com/neuro-inc/cookiecutter-neuro-project)
$ neuro project init

# Initializes a scaffolding for the new project with the recommended project
# structure and sets default project folder name to "example"
$ neuro project init my-project-id
```

#### Options


| Name | Description |

| :--- | :--- |

| _`--help`_ | Show this message and exit. |




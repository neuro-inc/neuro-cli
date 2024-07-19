Format for column specification
================================

This format is a sequence of column specifications separated
by commas or spaces: `{id}, {status}, {when}`.

A column specification contains a mandatory column ID and optional properties
that indicate alignment, minimum and maximum column width,
and the column's title: `{id;align=center;min=10;max=30;width=20;TITLE}`

Here, **id** is the column's ID, **align**, **min**, **max**, and **width**
are optional properties, and **TITLE** is the column's title.

Alternatively, you can specify only the column's ID without additional properties
and omit the curly brackets by using one of the following formats:

* `id, status, when`
* `id status when`

Available properties:

* **align**: Column alignment. Accepted values: left, right, center.
* **min**: Minimum column width.
* **max**: Maximum column width.
* **width**: Default column width.

If all of these properties are skipped, the default value is used for
the specified column ID.

Multiple values can be output on different lines in one cell if several
column IDs are specified separated with "/":

* `id/name {status/when;align=center;min=10;max=30;width=20;TITLE}`

The system recognizes the following columns:

* **id** (ID): Job id.
* **name** (NAME): Job name.
* **tags** (TAGS): Job tags.
* **status** (STATUS): Job status.
* **when** (WHEN): Time of the last update of job information.
* **created** (CREATED): Job creation time.
* **started** (STARTED): Job starting time.
* **finished** (FINISHED): Job finishing time.
* **image** (IMAGE): Job image.
* **owner** (OWNER): Job owner.
* **cluster_name** (CLUSTER): Job cluster name.
* **org_name** (ORG): Job org name.
* **description** (DESCRIPTION): Job description.
* **command** (COMMAND): The command a job executes.
* **life_span** (LIFE-SPAN): Job lifespan.
* **workdir** (WORKDIR): Default working directory inside a job.
* **preset** (PRESET): Resource configuration used for a job.

These additional columns are only recognized in the `apolo top` command:

* **cpu** (CPU): Number of used CPUs.
* **memory** (MEMORY (MB)): Amount of used memory, in MB.
* **gpu** (GPU (%)): Used GPUs, per cent.
* **gpu_memory** (GPU_MEMORY (MB)): Amount of used GPU memory, in MB.

By default, all columns are left-aligned and have no minimum and default widths.

The column ID is case-insensitive, so it can be changed to any unambiguous shortened
version of the full name.  For example, `{CLUSTER:max=20}` is a good column
specificaton, while `{C:max=20}` is not, as it can be expanded both into
`cluster_name` and `command` column IDs.
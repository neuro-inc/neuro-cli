Format for columns specification
================================

The format is a sequence of column specifications separated
by commas or spaces: `{id}, {status}, {when}`.

A column spec has a mandatory column id plus optional properties
for indication of alignment, minimum and maximum column width,
and optional column title: `{id;align=center;min=10;max=30;width=20;TITLE}`

Here **id** is the column id, **align**, **min**, **max**, **width**
are properties and **TITLE** is the column title.

An alternative form is specifying the column id only without
additional properties, in this case curly brackets can be omitted:
`id, status, when` or `id status when` are valid formats.


Available properties:

* **align**: Column aligning, accepted values: left, right, center.
* **min**: Minimal column width.
* **max**: Maximal column width.
* **width**: Default column width.

All properties can be skipped, the default value for specified column ID
is used in this case.

The system recognizes the following columns:

* **id** (ID): job id.
* **name** (NAME): job name.
* **tags** (TAGS): job tags.
* **status** (STATUS): job status.
* **when** (WHEN): time of the last update of job information.
* **created** (CREATED): time of job creation.
* **started** (STARTED): time of job statrting.
* **finished** (FINISHED): time of job finishing.
* **image** (IMAGE): job image.
* **owner** (OWNER): job owner.
* **cluster_name** (CLUSTER): job cluster name.
* **description** (DESCRIPTION): job description.
* **command** (COMMAND): job command to execute.
* **life_span** (LIFE-SPAN): job life-span.
* **workdir** (WORKDIR): default working directory inside a job.
* **preset** (PRESET): resource configuration used for a job.

Columns recognizes only in the `neuro top` command:

* **cpu** (CPU): number of used CPUs.
* **memory** (MEMORY (MB)): amount of used memory, in MB.
* **gpu** (GPU (%)): used GPUs, in percents.
* **gpu_memory** (GPU_MEMORY (MB)): amount of used GPU memory, in MB.

By default all columns are left aligned and have no minimal and default widths.

The column id is case insensitive, it can be shrinked to any unambiguous subset
of the full name.  For example `{CLUSTER:max=20}` is a good column spec but
`{C:max=20}` is not; it can be expanded into both `cluster_name` and `command`
column ids.
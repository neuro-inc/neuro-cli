Added new command `neuro job exec`. This commands allows to execute
both interactive and noninteractive commands in an already running
job. The main difference from `neuro job ssh` is that there is no need
neither for an ssh daemon in the container nor for an additional
private/public key pair. Thus this command can be used even if the job
was submited without `--ssh` option. You need either `WRITE` or
`MANAGE` access to the job to execute commands in it.

Usage examples:

`neuro job exec my-job-id ls` to show content of root directory of
your job.

`neuro job exec my-job-id 'ps -A'` to show processes running in your
job.

`neuro job exec --tty my-job-id bash` to start an interactive bash
session in your job.
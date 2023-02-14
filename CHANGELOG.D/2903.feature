Added support of cluster energy schedules.
`neuro config show --energy` will display awailable energy schedule periods.
`neuro run --schedule-name <energy-schedule-name>` will run the job within the specified <energy-schedule-name>. Note - the selected preset should have an enabled scheduler.
`neuro status <job-id>` will include the energy schedule name if one was used for running the job.

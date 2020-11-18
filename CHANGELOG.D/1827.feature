Added support of max running jobs quota. The `neuro admin set-user-quota -j <count>` command configures
this quota for user. By default, a new job cannot be created after the quota is reached, but the `--wait-for-seat`
flag allows creating a job that will wait for another job to stop.

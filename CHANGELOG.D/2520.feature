Added support to set/update cluster level default credits and quota.

Use options `--default-credits` and `--default-jobs` of commands `neuro admin add-cluster`,
`neuro admin update-cluster`, `neuro admin add-org-cluster` and `neuro admin update-org-cluster`
to set and update cluster defaults. This values will when new user with role "user" is added to cluster
(either by `neuro admin add-cluster-user` or if user registers himself using web interface).
The default for managers and admins is unlimited quota and credits as the can edit their quota.

You can override default value by using `--credits` and `--jobs` options of
`neuro admin add-org-cluster` command.

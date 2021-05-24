Removed support of old runtime quota:
- `neuro config show-quota` shows credits and max parallel jobs
- `neuro admin add-user-quota/set-user-quota` only support credits and max parallel jobs
- Added new command `neuro admin get-user-quota` to print user quota
- `neuro admin get-cluster-user` now prints table with quota info for each user

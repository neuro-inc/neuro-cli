Added "Spent credits" to add "neuro admin get-cluster-users". Splitted 'quota' into 'balance' and 'quota':

- `neuro admin set-user-quota` changes only `max_running_jobs` quota.
- `neuro admin set-user-credits` changes only `credits` balance of user.
- `neuro admin add-user-credits` updates `credits` balance of user by delta.

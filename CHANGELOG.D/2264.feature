Added way to create persistent credentials to buckets to use in outside of the platform:

- use `neuro blob mkcredentials <bucket1_id> <bucket2_id> ...` to create new credentials for specified buckets
- use `neuro blob lscredentials` to list your buckets credentials
- use `neuro blob statcredentials <credentials_id>` to retrieve info about single bucket credentials
- use `neuro blob rmbucket <credentials_id>` to delete bucket credentials.

Users can name buckets credentials. The name should be unique between users buckets credentials and can be used
instead of bucket credentials id.

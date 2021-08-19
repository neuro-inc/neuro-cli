Reworked blob storage support:

* `neuro bucket ...` command group to manage buckets:
  - use `neuro bucket create` to create new bucket
  - use `neuro bucket ls` to list your buckets
  - use `neuro bucket get <bucket_id>` to retrieve info about single bucket
  - use `neuro bucket rm <bucket_id>` to delete bucket. Note that you can only delete empty buckets.
  Users can name buckets objects. The name should be unique between users buckets and can be used
  instead of bucket id.

* `neuro blob ...` command group to manage buckets contents:
  - use `neuro blob ls blob:<bucket_id>/<path_in_bucket>` to list bucket contents. Option `-r`
    disables file system emulation and displays all keys that start with <path_in_bucket>.
  - use `neuro blob glob blob:<bucket_id>/<glob_pattern>` to glob search objects in buckets.
    For example, `blob:my_bucket/**/*.txt` pattern will match all `.txt` files in `my_bucket`
    bucket.
  - use `neuro blob cp <src_uri> <dst_uri>` to copy data from/to bucket.
  - use `neuro blob rm blob:<bucket_id>/<path_in_bucket>` to delete elements from bucket.

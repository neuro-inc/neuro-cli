Added support of named:
- create new disk by `neuro disk create --name <disk-name> STORAGE` command
- name can be used to get/delete disk: `neuro disk get <disk-name>` or `neuro disk delete <disk-name>`
- name can be used to mount disk: `neuro run -v disk:<disk-name>:/mnt/disk ...`

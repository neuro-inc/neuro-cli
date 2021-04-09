Using the sharing functionality
===============================

Understanding permissions
-------------------------

The Neu.ro platform supports five levels of access:
* deny - No access
* list - Permits listing entities, but not looking at their details
* read - Read-only access to an entity
* write - Read-write access to an entity (including deletion)
* manage - Allows modification of an entity's permissions

Please note that permissions are inclusive: *write* permission implies reading,
and *manage* includes reading and writing, and so on.

Permissions can be granted via `neuro acl grant` or `neuro share` and
revoked via `neuro acl revoke`:
```
neuro acl grant job:job-0a6d3f81-b5d2-45db-95e3-548cc1fac81a bob
neuro acl revoke job:job-0a6d3f81-b5d2-45db-95e3-548cc1fac81a bob
```

You can check entities owned by you and shared with you by running
`neuro acl list`. This will show all entity URIs and their access levels.
If you want to focus on a subset of entities, you can filter them with `-s`.
For instance, `neuro acl list -s job` will only show you jobs you have access to.

If the `neuro acl list` output contains a URI such as `secret:` or `storage:`,
it means you have corresponding permissions for all entities of that type.

Running `neuro acl list --shared` will show you entities shared by you
along with users/roles you shared them with.

Roles
-----

The Neu.ro platform supports role-based access control. Role is a packed set of
permissions to multiple entities which can be shared together. There's several
default roles in each cluster, and users may additionally create their own custom
roles.

Default roles are:
* {cluster}/manager
* {cluster}/admin
* {cluster}/users/{username} - such roles are created for every cluster user and
    always contain a whole set of user's permissions.

If you want to create a new role, run
`neuro acl add-role {username}/roles/{rolename}`

This will create a role "rolename" with an empty permission set. Then you may share
resources with the new role via `neuro acl grant`:

```
neuro acl grant image:IMAGE_NAME {username}/roles/{rolename}
neuro acl grant job:JOB_NAME {username}/roles/{rolename}
neuro acl grant job:ANOTHER_JOB_NAME {username}/roles/{rolename}
neuro acl grant storage:/folder_name {username}/roles/{rolename}
```

When ready, grant this permission set to another user (`bob` in this case):

```
neuro acl grant role://{username}/roles/{rolename} bob
```

From now on, `bob` will have access to all entities listed under
the `{username}/roles/{rolename}` role. The list can be viewed by
`neuro acl list -u {username}/roles/{rolename}`.

If needed, a role can be revoked:
`neuro acl revoke role://{username}/roles/{rolename} bob`

Roles can be deleted by running `neuro acl remove-role {username}/roles/{rolename}`.
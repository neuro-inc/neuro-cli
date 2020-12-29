Using sharing functionality
===========================

Understanding permissions
-------------------------
Neu.ro platform supports five levels of access:
* deny - no access
* list - permits listing entities, but not looking at their details
* read - read-only access to entity
* write - read-write access (including deletion) to entity
* manage - allows modification of entity's permissions

Please note permissions are inclusive: write permission implies read and manage
includes read and write, and so on.

Permissions can be granted via `neuro acl grant` or `neuro share` and
revoked via `neuro acl revoke`:
```
neuro acl grant job:job-0a6d3f81-b5d2-45db-95e3-548cc1fac81a bob
neuro acl revoke job:job-0a6d3f81-b5d2-45db-95e3-548cc1fac81a bob
```

You can check entities owned by you and shared with you by others by running
`neuro acl list`. This will show all entity URIs and their access levels.
If you want to focus on a subset of entities you can filter them with `-s`.
For instance, `neuro acl list -s job` will only show you jobs you have access to.

If `neuro acl list` output contains a URI, such as `secret:` or `storage:`
it means you've got corresponding permission for all entities of that type.

Running `neuro acl list --shared` will show you entities shared by you
along with users/roles you shared them with.

Roles
-----
Neu.ro platform supports role-based access control. Role is a packed set
of permissions to multiple entities which can be shared together. There's several
default roles in each cluster, plus users may create their own custom roles.

Default roles are:
* {cluster}/manager
* {cluster}/admin
* {cluster}/users/{username} - such roles are created for every cluster user and
    always contain a whole set of user's permissions.

If you want to create a new role, run
`neuro acl add-role {username}/roles/{rolename}`

This will create a role "rolename" with empty permission set. Then you may share
resources with the new role via `neuro acl grant`:

```
neuro acl grant image:IMAGE_NAME {username}/roles/{rolename}
neuro acl grant job:JOB_NAME {username}/roles/{rolename}
neuro acl grant job:ANOTHER_JOB_NAME {username}/roles/{rolename}
neuro acl grant storage:/folder_name {username}/roles/{rolename}
```

When ready, grant this permission set to another user (`bob` in the example):

```
neuro acl grant role://{username}/roles/{rolename} bob
```

From now on, `bob` will have access to all entities listed under
the `{username}/roles/{rolename}` role. The list can be viewed by
`neuro acl list -u {username}/roles/{rolename}`.

If needed, role can be revoked:
`neuro acl revoke role://{username}/roles/{rolename} bob`

And deleted by running `neuro acl remove-role {username}/roles/{rolename}`.
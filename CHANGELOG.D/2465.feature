Added initial support of organizations.

Current organization is displayed in `neuro config show`. It can be changed using `neuro config switch-org`. To least
organizations you have access to in each cluster, use `neuro config get-clusters`.

Also you can now run job on behalf of organization. By default, `neuro run` will use current organization, but you
can override it using `neuro run --org <some_org>`.

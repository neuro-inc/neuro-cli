Added admin commands to manager orgs and org-clusters:

Managing orgs:

- `neuro admin get-orgs`               Print the list of available orgs user has access to.
- `neuro admin add-org <org_name>`     Create a new org.
- `neuro admin remove-org <org_name>`  Drop a org. Removes all memberships, very dangerous operation.

Managing org members:

- `neuro admin get-org-users <org_name>`               List all members of orgs.
- `neuro admin add-org-user <org_name> <username>`     Add user to the org.
- `neuro admin remove-org-user <org_name> <username>`  Remove user from the org.

Managing access of orgs to clusters:

- `neuro admin get-org-clusters <cluster_name>`                     Print the list of all orgs in the cluster
- `neuro admin add-org-cluster <cluster_name> <org_name>`           Add org access to specified cluster
- `neuro admin get-org-cluster-quota  <cluster_name> <org_name>`    Get info about org quota in given cluster
- `neuro admin set-org-cluster-quota [options] <cluster_name> <org_name>`    Set org cluster quota to given values
- `neuro admin set-org-cluster-credits [options] <cluster_name> <org_name>`  Set org cluster credits to given value
- `neuro admin add-org-cluster-credits [options] <cluster_name> <org_name>`  Add given values to org cluster balance

Manging access of org members to clusters:

- `neuro admin get-cluster-users --org <org_name> <cluster_name>`                      List all members of orgs added to cluster
- `neuro admin add-cluster-user --org <org_name>  <cluster_name> <username>`           Add org member to cluster
- `neuro admin remove-cluster-user --org <org_name> <cluster_name> <username>`         Remove org member user from the cluster.
- `neuro admin get-user-quota --org <org_name>  <cluster_name> <username>`             Get info about org member quota in given cluster
- `neuro admin set-user-quota [options] --org <org_name> <cluster_name> <username>`    Set org member quota in cluster to given values
- `neuro admin set-user-credits [options] --org <org_name> <cluster_name> <username>`  Set org member credits in cluster to given value
- `neuro admin add-user-credits [options] --org <org_name> <cluster_name> <username>`  Add given values to org member balance in cluster

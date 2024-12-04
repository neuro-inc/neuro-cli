Balance is no longer stored on a cluster level, and was moved to an organization level, e.g.,
to an org itself, and to an org users, instead of a cluster / cluster users.

New commands:
  - `set_org_defaults` - allows to set an organization default values, such as a default user credits

Existing commands changes:
  - `add_cluster_user` cmd is no longer accepting a `credits` argument.
  - `set_user_credits` cmd is now expecting an org name instead of a cluster name.
  - `add_user_credits` cmd is now expecting an org name instead of a cluster name.
  - `set_org_cluster_credits` is now deprecated in a favor of a `set_org_credits`.
  - `add_org_cluster_credits` is not deprecated in a favor of an `add_org_credits`.

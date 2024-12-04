Balance is no longer stored on a cluster level, and was moved to an organization level, e.g.,
to an org itself, and to an org users, instead of a cluster / cluster users.

New commands:
  - `apolo admin set-org-defaults` - allows to set an organization default values, such as a default user credits

Existing commands changes:
  - `apolo admin add-cluster-user` cmd is no longer accepting a `credits` argument.
  - `apolo admin set-user-credits` cmd is now expecting an org name instead of a cluster name.
  - `apolo admin add-user-credits` cmd is now expecting an org name instead of a cluster name.
  - `apolo admin set-org-cluster-credits` was removed in a favor of an `apolo admin set-org-credits`.
  - `apolo admin add-org-cluster-credits` was removed in a favor of an `apolo admin add-org-credits`.

Added `neuro service-account` command group. The service account allow to create auth token that can be used
for integration with third-party services.

- `neuro service-account create --name optional-name ROLE` creates new service account
- `neuro service-account ls` lists service accounts
- `neuro service-account get ID_OR_NAME` retrives single service account
- `nuero service-account rm ID_OR_NAME` removes service account and revokes token.

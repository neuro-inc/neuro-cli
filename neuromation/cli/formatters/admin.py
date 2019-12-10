from typing import Iterable, List

from neuromation.api.admin import _ClusterUser

from .ftable import table


class ClusterUserFormatter:
    def __call__(self, clusters_users: Iterable[_ClusterUser]) -> List[str]:
        headers = ("Name", "Role")
        rows = [headers]
        for user in clusters_users:
            rows.append((user.user_name, user.role.value))

        return list(table(rows=rows))

from typing import Iterable, List

import click

from neuromation.api.admin import _Cluster, _ClusterUser

from .ftable import table


class ClusterUserFormatter:
    def __call__(self, clusters_users: Iterable[_ClusterUser]) -> List[str]:
        headers = (click.style("Name", bold=True), click.style("Role", bold=True))
        rows = [headers]

        for user in clusters_users:
            rows.append((user.user_name, user.role.value))

        return list(table(rows=rows))


class ClustersFormatter:
    def __call__(self, clusters: Iterable[_Cluster]) -> List[str]:
        headers = [click.style("Name", bold=True)]
        rows = [headers]
        for cluster in clusters:
            rows.append([click.style(cluster.name, underline=True)])
        return list(table(rows=rows))

from typing import Iterable, List

import click

from neuromation.api.admin import _Cluster, _ClusterUser

from .ftable import ColumnWidth, table


class ClusterUserFormatter:
    def __call__(self, clusters_users: Iterable[_ClusterUser]) -> List[str]:
        headers = (
            click.style(
                "Name is super long oh my god what to do ", bold=True, reset=False
            )
            + click.style("underlined", underline=True)
            + " partialy styled",
            click.style("Role", bold=True),
        )
        rows = [headers]

        for user in clusters_users:
            rows.append((user.user_name, user.role.value))

        return list(table(rows=rows, widths=[ColumnWidth(max=20)] * 2))


class ClustersFormatter:
    def __call__(self, clusters: Iterable[_Cluster]) -> List[str]:
        headers = [click.style("Name", bold=True)]
        rows = [headers]
        for cluster in clusters:
            rows.append([click.style(cluster.name, underline=True)])
        return list(table(rows=rows))

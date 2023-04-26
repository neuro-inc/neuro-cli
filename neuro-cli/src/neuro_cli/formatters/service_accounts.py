import abc
import base64
import json
import operator
from typing import Sequence

from rich import box
from rich.console import Group as RichGroup
from rich.console import RenderableType
from rich.table import Table
from rich.text import Text

from neuro_sdk import ServiceAccount

from neuro_cli.formatters.utils import DatetimeFormatter


class BaseServiceAccountsFormatter:
    @abc.abstractmethod
    def __call__(self, accounts: Sequence[ServiceAccount]) -> RenderableType:
        pass


class SimpleServiceAccountsFormatter(BaseServiceAccountsFormatter):
    def __call__(self, accounts: Sequence[ServiceAccount]) -> RenderableType:
        return RichGroup(*(Text(account.id) for account in accounts))


class ServiceAccountsFormatter(BaseServiceAccountsFormatter):
    def __init__(
        self,
        datetime_formatter: DatetimeFormatter,
    ) -> None:
        self._datetime_formatter = datetime_formatter

    def _account_to_table_row(self, account: ServiceAccount) -> Sequence[str]:
        line = [
            account.id,
            account.name or "",
            account.role,
            account.default_cluster,
            self._datetime_formatter(account.created_at),
        ]
        return line

    def __call__(self, accounts: Sequence[ServiceAccount]) -> RenderableType:
        accounts = sorted(accounts, key=operator.attrgetter("id"))
        table = Table(box=box.SIMPLE_HEAVY)
        # make sure that the first column is fully expanded
        width = len("service-account-06bed296-8b27-4aa8-9e2a-f3c47b41c807")
        table.add_column("Id", style="bold", width=width)
        table.add_column("Name")
        table.add_column("Role")
        table.add_column("Default cluster")
        table.add_column("Created At")
        for account in accounts:
            table.add_row(*self._account_to_table_row(account))
        return table


class ServiceAccountFormatter:
    def __init__(self, datetime_formatter: DatetimeFormatter) -> None:
        self._datetime_formatter = datetime_formatter

    def __call__(self, account: ServiceAccount) -> RenderableType:
        table = Table(
            box=None,
            show_header=False,
            show_edge=False,
        )
        table.add_column()
        table.add_column(style="bold")
        table.add_row("Id", account.id)
        table.add_row("Name", account.name or "")
        table.add_row("Role", account.role)
        table.add_row("Owner", account.owner)
        table.add_row("Default cluster", account.default_cluster)
        table.add_row("Default org", account.default_org)
        table.add_row("Default project", account.default_project)
        table.add_row("Created at", self._datetime_formatter(account.created_at))
        return table


def service_account_token_fmtr(token: str, account: ServiceAccount) -> RenderableType:
    token_data: dict[str, str] = json.loads(base64.b64decode(token.encode()).decode())
    auth_token = token_data["token"]

    org_name = token_data.get("org_name")
    share_project_cmd_hint = (
        f"[b]neuro admin add-project-user {f'--org {org_name}' if org_name else ''}"
        f" {token_data.get('cluster')} "
        f" {token_data.get('project_name')}"
        f" {account.role}"
        " reader|writer|manager|admin[/b]\n"
    )

    lines = [
        "Full token with cluster and API url embedded (this value can "
        "be used as [b]NEURO_PASSED_CONFIG[/b] environment variable):\n",
        token,
        "\nJust auth token (this value can be passed to [b]neuro config"
        " login-with-token[/b]):\n",
        auth_token,
        "\n[b red]Save it to some secure place, you will be unable to "
        "retrieve it later![/b red]",
        "\nTo allow access to your current project for this service account, "
        "perform:\n",
        share_project_cmd_hint,
    ]
    if org_name:
        lines.extend(
            [
                "\nTo allow access to your current org for this service account, "
                "perform:\n",
                f"[b]neuro admin add-org-user {org_name} {account.role}"
                " reader|writer|manager|admin[/b]\n",
            ]
        )

    return Text.from_markup("\n".join(lines))

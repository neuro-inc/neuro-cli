from sys import platform
from typing import Dict

from click import style
from tabulate import tabulate

from neuromation.api.login import RunPreset
from neuromation.cli.root import Root


class ConfigFormatter:
    def __call__(self, root: Root) -> str:
        lines = []
        lines.append(style("User Name", bold=True) + f": {root.username}")
        lines.append(style("API URL", bold=True) + f": {root.url}")
        lines.append(style("Docker Registry URL", bold=True) + f": {root.registry_url}")
        lines.append(style("Resource Presets", bold=True) + f":")
        indent: str = "  "
        return (
            style("User Configuration", bold=True)
            + ":\n"
            + indent
            + f"\n{indent}".join(lines)
            + "\n"
            + self._format_presets(root.resource_presets)
        )

    def _format_presets(
        self, presets: Dict[str, RunPreset], indent: str = "    "
    ) -> str:
        if platform == "win32":
            yes, no = "Yes", "No"
        else:
            yes, no = "✔︎", "✖︎"
        has_tpu = False
        for preset in presets.values():
            if preset.tpu_type:
                has_tpu = True
                break

        table = []
        headers = ["Name", "#CPU", "Memory", "Preemptible", "GPU"]
        if has_tpu:
            headers.append("TPU")

        for name, preset in presets.items():
            gpu = ""
            if preset.gpu:
                gpu = f"{preset.gpu} x {preset.gpu_model}"
            row = [
                name,
                preset.cpu,
                preset.memory_mb,
                yes if preset.is_preemptible else no,
                gpu,
            ]
            if preset.tpu_type:
                tpu = f"{preset.tpu_type}/{preset.tpu_software_version}"
                row.append(tpu)
            table.append(row)
        return tabulate(  # type: ignore
            table,
            headers=headers,
            tablefmt="plain",
            colalign=("left", "right", "right", "center"),
        )

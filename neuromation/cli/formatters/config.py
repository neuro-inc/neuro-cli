from sys import platform
from typing import Dict, Iterator

from click import style

from neuromation.api import Preset
from neuromation.cli.root import Root
from neuromation.cli.utils import format_size

from .ftable import Align, table


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
            + f"\n".join(line for line in self._format_presets(root.resource_presets))
        )

    def _format_presets(self, presets: Dict[str, Preset]) -> Iterator[str]:
        if platform == "win32":
            yes, no = "Yes", "No"
        else:
            yes, no = "✔︎", "✖︎"
        has_tpu = False
        for preset in presets.values():
            if preset.tpu_type:
                has_tpu = True
                break

        rows = []
        headers = ["Name", "#CPU", "Memory", "Preemptible", "GPU"]
        rows.append(headers)
        if has_tpu:
            headers.append("TPU")

        for name, preset in presets.items():
            gpu = ""
            if preset.gpu:
                gpu = f"{preset.gpu} x {preset.gpu_model}"
            row = [
                name,
                str(preset.cpu),
                format_size(preset.memory_mb * 1024 ** 2),
                yes if preset.is_preemptible else no,
                gpu,
            ]
            if has_tpu:
                tpu = (
                    f"{preset.tpu_type}/{preset.tpu_software_version}"
                    if preset.tpu_type
                    else ""
                )
                row.append(tpu)
            rows.append(row)
        yield from table(
            rows=rows, aligns=[Align.LEFT, Align.RIGHT, Align.RIGHT, Align.CENTER]
        )

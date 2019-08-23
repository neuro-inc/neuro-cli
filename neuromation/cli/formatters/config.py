from sys import platform
from typing import Dict

from click import style

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
        lines = []

        has_tpu = False
        for preset in presets.values():
            if preset.tpu_type:
                has_tpu = True
                break

        if has_tpu:
            lines.append(
                f"Name         #CPU  Memory Preemptible #GPU  GPU Model          TPU"
            )
            for name, preset in presets.items():
                tpu = ""
                if preset.tpu_type:
                    tpu = f"{preset.tpu_type}/{preset.tpu_software_version}"
                lines.append(
                    (
                        f"{name:12}  {preset.cpu:>3} {preset.memory_mb:>7} "
                        f"{yes if preset.is_preemptible else no:^11}"
                        f"  {preset.gpu or '':>3}"
                        f"  {preset.gpu_model or '':<17}"
                        f"  {tpu}"
                    ).rstrip()
                )
        else:
            lines.append(f"Name         #CPU  Memory Preemptible #GPU  GPU Model")
            for name, preset in presets.items():
                lines.append(
                    (
                        f"{name:12}  {preset.cpu:>3} {preset.memory_mb:>7} "
                        f"{yes if preset.is_preemptible else no:^11}"
                        f"  {preset.gpu or '':>3}"
                        f"  {preset.gpu_model or ''}"
                    ).rstrip()
                )
        return indent + f"\n{indent}".join(lines)

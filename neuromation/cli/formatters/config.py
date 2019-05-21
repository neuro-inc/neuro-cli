from click import style

from neuromation.cli.root import Root


class ConfigFormatter:
    def __call__(self, root: Root) -> str:
        lines = []
        lines.append(style("User Name", bold=True) + f": {root.username}")
        lines.append(style("API URL", bold=True) + f": {root.url}")
        lines.append(style("Docker Registry URL", bold=True) + f": {root.registry_url}")
        lines.append(style("Resource Presets", bold=True) + f":")
        lines.append(f"  Name         #CPU  Memory #GPU  GPU Model")
        for name, preset in root.resource_presets.items():
            lines.append(f"  {name:12}  {preset.cpu:>3} {preset.memory:>7}  {preset.gpu or '':>3}  {preset.gpu_model or ''}".rstrip())
        indent = "  "
        return (
            style("User Configuration", bold=True)
            + ":\n"
            + indent
            + f"\n{indent}".join(lines)
        )

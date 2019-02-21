from neuromation.cli.rc import Config


class ConfigFormatter:
    def __call__(self, config: Config) -> str:
        lines = []
        lines.append(
            style("User Name", bold=True) + f": {config.get_platform_user_name()}"
        )
        lines.append(style("API URL", bold=True) + f": {config.url}")
        lines.append(
            style("Docker Registry URL", bold=True) + f": {config.registry_url}"
        )
        lines.append(
            style("Github RSA Path", bold=True) + f": {config.github_rsa_path}"
        )
        indent = "  "
        return (
            style("User Configuration", bold=True)
            + ":\n"
            + indent
            + f"\n{indent}".join(lines)
        )

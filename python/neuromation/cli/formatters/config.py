from neuromation.cli.rc import Config

from .abc import BaseFormatter


class ConfigFormatter(BaseFormatter):
    def __call__(self, config: Config) -> str:
        lines = []
        lines.append(f"User Name: {config.get_platform_user_name()}")
        lines.append(f"API URL: {config.url}")
        lines.append(f"Docker Registry URL: {config.registry_url}")
        lines.append(f"Github RSA Path: {config.github_rsa_path}")
        indent = "  "
        return "Config:\n" + indent + f"\n{indent}".join(lines)

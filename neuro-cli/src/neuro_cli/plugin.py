from neuro_sdk import ConfigScope, PluginManager

NEURO_CLI_UPGRADE = """\
You are using Neuro Platform Client {old_ver}, however {new_ver} is available.
You should consider upgrading via the following command:
    python -m pip install --upgrade neuro-cli
"""


def get_neuro_cli_txt(old: str, new: str) -> str:
    return NEURO_CLI_UPGRADE.format(old_ver=old, new_ver=new)


CERTIFI_UPGRADE = """\
Your root certificates are out of date.
You are using certifi {old_ver}, however {new_ver} is available.
Please consider upgrading certifi package, e.g.:
    python -m pip install --upgrade certifi
or
    conda update certifi
"""


def get_certifi_txt(old: str, new: str) -> str:
    return CERTIFI_UPGRADE.format(old_ver=old, new_ver=new)


def setup(manager: PluginManager) -> None:
    # Setup config options
    manager.config.define_str("job", "ps-format")
    manager.config.define_str("job", "top-format")
    manager.config.define_str("job", "life-span")
    manager.config.define_str("job", "cluster-name", scope=ConfigScope.LOCAL)
    manager.config.define_str("job", "org-name", scope=ConfigScope.LOCAL)
    manager.config.define_str_list("storage", "cp-exclude")
    manager.config.define_str_list("storage", "cp-exclude-from-files")

    manager.version_checker.register("neuro-cli", get_neuro_cli_txt)
    manager.version_checker.register("certifi", get_certifi_txt, delay=14 * 3600 * 24)

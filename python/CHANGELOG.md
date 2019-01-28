[comment]: # (Please do not modify this file)
[comment]: # (Put you comments to changelog.d and it will be moved to changelog in next release)

[comment]: # Clear the text on make release for canceling the release

[comment]: # (towncrier release notes start)

Neuromation 0.2.0b0 (2019-01-28)
================================

Features
--------


- Deep refactor ``neuro store`` command and corresponding API client. ([#324](https://github.com/neuromation/platform-api-clients/issues/324))

- Default API URL switched to HTTPS for _neuro_ cli ([#325](https://github.com/neuromation/platform-api-clients/issues/325))

- Job resource output formatting for command `neuro job status` changed ([#328](https://github.com/neuromation/platform-api-clients/issues/328))

- `neuro image pull/push` command improved for support different names/tags for images, introduced 'image://' scheme for image referencing. ([#349](https://github.com/neuromation/platform-api-clients/issues/349))

- Implement --show-traceback command line option to show python traceback in case of top-level error ([#365](https://github.com/neuromation/platform-api-clients/issues/365))

- Added new option `--insecure` for storing auth in plain text file instead system keyring. ([#366](https://github.com/neuromation/platform-api-clients/issues/366))

- New `neuro image ls` command for listing custom images available on platform repository. ([#367](https://github.com/neuromation/platform-api-clients/issues/367))

- Added new command `neuro job exec` to execute commands in already running job without ssh server. ([#373](https://github.com/neuromation/platform-api-clients/issues/373))

- Display Preemptible in job status output ([#393](https://github.com/neuromation/platform-api-clients/issues/393))

- Make the client work on Python 3.7 ([#402](https://github.com/neuromation/platform-api-clients/issues/402))


Deprecations and Removals
-------------------------


- Jobs datastructure refactored ([#320](https://github.com/neuromation/platform-api-clients/issues/320))

- Removed _keyrings.cryptfile_ from project dependencies. Please remove it self if upgrade _neuromation_. ([#366](https://github.com/neuromation/platform-api-clients/issues/366))


Misc
----

- [#285](https://github.com/neuromation/platform-api-clients/issues/285), [#393](https://github.com/neuromation/platform-api-clients/issues/393)

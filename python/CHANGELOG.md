[comment]: # (Please do not modify this file)
[comment]: # (Put you comments to changelog.d and it will be moved to changelog in next release)

[comment]: # (Clear the text on make release for canceling the release)

[comment]: # (towncrier release notes start)

Neuromation 0.3.0 (2019-02-01)
==============================

Features
--------


- Add `-p/-P` shortcuts for `--preemtible/--non-preemtible` for `neuro submit` command. ([#458](https://github.com/neuromation/platform-api-clients/issues/458))


Neuromation 0.3.0 (2019-02-01)
==============================

Features
--------


- Wait for job start/failure on job submit. ([#356](https://github.com/neuromation/platform-api-clients/issues/356))

- Support `-v` as a shortcut for `--volume` in `neuro submit ...` command. ([#383](https://github.com/neuromation/platform-api-clients/issues/383))

- Improve resource URI normalization and print normalized URIs back to the user. ([#457](https://github.com/neuromation/platform-api-clients/issues/457))

- Re-organize CLI commands for better UI/UX experience. Obsolete commands are hidden but still supported. ([#460](https://github.com/neuromation/platform-api-clients/issues/460))


Neuromation 0.2.2 (2019-01-31)
==============================

Features
--------


- Add top-level aliases for the most frequent commands. ([#439](https://github.com/neuromation/platform-api-clients/issues/439))

- Better formatting for examples section. ([#446](https://github.com/neuromation/platform-api-clients/issues/446))


Bugfixes
--------


- Bump `click` version to `7.0+`. ([#437](https://github.com/neuromation/platform-api-clients/issues/437))

- Temporary disable scary logging about unhandled exception. ([#438](https://github.com/neuromation/platform-api-clients/issues/438))

- Fix an error in local path normalization. ([#443](https://github.com/neuromation/platform-api-clients/issues/443))


Neuromation 0.2.1 (2019-01-29)
==============================

Features
--------


- Implement ``neuro job top`` ([#412](https://github.com/neuromation/platform-api-clients/issues/412))

- Pretty format output for ``neuro config show`` command, print current authentication token by ``neuro config show-token``. ([#426](https://github.com/neuromation/platform-api-clients/issues/426))

- Check `~/.nmrc` config file for strict `0o600` permissions. ([#430](https://github.com/neuromation/platform-api-clients/issues/430))


Deprecations and Removals
-------------------------


- Drop `--token` and `--url` parameters from the root command, use `neuro login` and `neuro config url` to setup config parameters. ([#430](https://github.com/neuromation/platform-api-clients/issues/430))


Neuromation 0.2.0 (2019-01-28)
==============================

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

- Implement ``neuro job top`` ([#412](https://github.com/neuromation/platform-api-clients/issues/412))


Deprecations and Removals
-------------------------


- Jobs datastructure refactored ([#320](https://github.com/neuromation/platform-api-clients/issues/320))

- Removed _keyrings.cryptfile_ from project dependencies. Please remove it self if upgrade _neuromation_. ([#366](https://github.com/neuromation/platform-api-clients/issues/366))


Misc
----

- [#285](https://github.com/neuromation/platform-api-clients/issues/285), [#393](https://github.com/neuromation/platform-api-clients/issues/393)

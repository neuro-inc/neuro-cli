[comment]: # (Please do not modify this file)
[comment]: # (Put you comments to changelog.d and it will be moved to changelog in next release)

[comment]: # (Clear the text on make release for canceling the release)

[comment]: # (towncrier release notes start)

Neuromation 19.5.13 (2019-05-13)
================================

Features
--------


- Print exposed HTTP for named jobs ([#736](https://github.com/neuromation/platform-api-clients/issues/736))

- Support retrieving server config for authorized users. ([#766](https://github.com/neuromation/platform-api-clients/issues/766))


Neuromation 19.4.23 (2019-04-23)
================================

Features
--------


- Implement *job run* command. ([#652](https://github.com/neuromation/platform-api-clients/issues/652))


Bugfixes
--------


- Fix image name parser to substitute lastest tag automatically. ([#729](https://github.com/neuromation/platform-api-clients/issues/729))


Neuromation 19.4.16 (2019-04-16)
================================

Features
--------


- New option `--neuromation-config` for using alternative config file location. Environment variable `NEUROMATION_CONFIG` can be used as option.
  New command `neuro config docker` allows to use `docker image push/pull` commands with platform registry. ([#381](https://github.com/neuromation/platform-api-clients/issues/381))

- `neuro port-forward` command now accepts multiple local-remote port pairs in order to forward several ports by a single command. ([#632](https://github.com/neuromation/platform-api-clients/issues/632))

- Support job names. ([#648](https://github.com/neuromation/platform-api-clients/issues/648))

- Make progress argument for storage API optional. ([#687](https://github.com/neuromation/platform-api-clients/issues/687))

- Rename neuromation.client to neuromation.api ([#688](https://github.com/neuromation/platform-api-clients/issues/688))

- Implement `neuro config login-with-token TOKEN URL` command. ([#712](https://github.com/neuromation/platform-api-clients/issues/712))


Bugfixes
--------


- Don't allow to submit image names starting with dash. ([#526](https://github.com/neuromation/platform-api-clients/issues/526))

- Respect `--network-timeout` option in `logs` and `cp` operations. ([#703](https://github.com/neuromation/platform-api-clients/issues/703))


Deprecations and Removals
-------------------------


- Remove deprecated functionality: `neuro model`, `neuro config id_rsa` and `neuro job submit --ssh` option. ([#700](https://github.com/neuromation/platform-api-clients/issues/700))


Neuromation 0.7.2 (2019-03-25)
==============================

Features
--------


- Change the default API endpoint to `https://staging.neu.ro/api/v1` ([#666](https://github.com/neuromation/platform-api-clients/issues/666))


Neuromation 0.7.1 (2019-03-15)
==============================

Bugfixes
--------


- Fix incorrect `--volume` parsing under windows ([#635](https://github.com/neuromation/platform-api-clients/issues/635))


Neuromation 0.7.0 (2019-03-14)
==============================

Features
--------


- New flag `--http-auth/--no-http-auth` which controls authentication for forwarded HTTP port. Enabled by default. ([#604](https://github.com/neuromation/platform-api-clients/issues/604))


Neuromation 0.6.2 (2019-03-07)
==============================

Bugfixes
--------


- Increase wait time to finish on POSIX platforms. It dignificantly decreases a chance of error report after CLI command executions. ([#597](https://github.com/neuromation/platform-api-clients/issues/597))

- Fix forward compatibility with platform server. ([#599](https://github.com/neuromation/platform-api-clients/issues/599))


Neuromation 0.6.1 (2019-03-04)
==============================

Bugfixes
--------


- Close version checker properly in case of error in a command execution. ([#586](https://github.com/neuromation/platform-api-clients/issues/586))

- Pin aiohttp to 3.5+ to satisfy minimal supported CLI version. ([#587](https://github.com/neuromation/platform-api-clients/issues/587))


Neuromation 0.6.0 (2019-03-01)
==============================

Features
--------


- Extended '/dev/shm' space (`--extshm`) turned on by default ([#449](https://github.com/neuromation/platform-api-clients/issues/449))

- Add support for server-side job list filtering (speedup of the `neuro ps`) ([#474](https://github.com/neuromation/platform-api-clients/issues/474))

- Several UX improvements. ([#486](https://github.com/neuromation/platform-api-clients/issues/486))

- `neuro store ls` now supports colored output, _LS_COLORS_(GNU) or _LSCOLORS_(BSD) environment variable required. ([#487](https://github.com/neuromation/platform-api-clients/issues/487))

- Improve shell completion logic, make shell type argument mandatory. ([#506](https://github.com/neuromation/platform-api-clients/issues/506))

- Add Http URL to neuro job submit output ([#527](https://github.com/neuromation/platform-api-clients/issues/527))

- Added neuro port-forward command to forward a port of a job exposed during job submit to a local one. ([#535](https://github.com/neuromation/platform-api-clients/issues/535))

- Support Windows platform ([#548](https://github.com/neuromation/platform-api-clients/issues/548))


Bugfixes
--------


- Fix parsing image URIs. ([#539](https://github.com/neuromation/platform-api-clients/issues/539))

- Don't fetch PyPI if `--disable-pypi-version-check` is on. ([#559](https://github.com/neuromation/platform-api-clients/issues/559))


Neuromation 0.4.0 (2019-02-12)
==============================

Features
--------


- Check the lastest PyPI neuromation release, suggest to upgrade if PyPI has a newer version. ([#308](https://github.com/neuromation/platform-api-clients/issues/308))

- Changes in `neuro store ls` behavior: display files by columns by default, add option `-l` for long output, display one per line for pipes by default. ([#427](https://github.com/neuromation/platform-api-clients/issues/427))

- Set up the platform to work with the new platform DNS names. ([#495](https://github.com/neuromation/platform-api-clients/issues/495))


Bugfixes
--------


- Use colored mode only if all stdin, stdout, and stderr are tty. ([#473](https://github.com/neuromation/platform-api-clients/issues/473))

- Improved login error reporting ([#477](https://github.com/neuromation/platform-api-clients/issues/477))


Neuromation 0.3.0 (2019-02-01)
==============================

Features
--------


- Add `-p/-P` shortcuts for `--preemtible/--non-preemtible` for `neuro submit` command. ([#458](https://github.com/neuromation/platform-api-clients/issues/458))

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

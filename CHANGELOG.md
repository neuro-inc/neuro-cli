[comment]: # (Please do not modify this file)
[comment]: # (Put you comments to changelog.d and it will be moved to changelog in next release)

[comment]: # (Clear the text on make release for canceling the release)

[comment]: # (towncrier release notes start)

Neuromation 20.3.23 (2020-03-23)
================================

Bugfixes
--------


- Bump `typing_extensions` dependency version to satisfy CLI requirements. ([#1421](https://github.com/neuromation/platform-api-clients/issues/1421))


Neuromation 20.3.20 (2020-03-20)
================================

Bugfixes
--------


- Fix `--pass-config` error: File exists: '/root/.neuro'. ([#1415](https://github.com/neuromation/platform-api-clients/issues/1415))


Neuromation 20.3.18 (2020-03-18)
================================

Features
--------


- Support job run-time limit: `neuro run --life-span "1d2h3m"`. ([#1325](https://github.com/neuromation/platform-api-clients/issues/1325))

- For cluster-specific resources (with schemes `storage`, `image` and `job`) client now use URIs containing the cluster name, e.g. `storage://{clustername}/{username}/{path}` instead of `storage://{username}/{path}`. Relative URI `storage:{path}` will be expanded to absolute URI containing the current cluster name and the user name: `storage://{clustername}/{username}/{path}`. Same for `image` and `job` schemes. ([#1341](https://github.com/neuromation/platform-api-clients/issues/1341))

- Added 'neuro image ls -l' option, which also prints Docker URL-s ([#1354](https://github.com/neuromation/platform-api-clients/issues/1354))

- Added the `-u` option in `neuro acl list` to specify a role or user to which resources are available and for which they are shared. ([#1355](https://github.com/neuromation/platform-api-clients/issues/1355))

- Sort `neuro admin get-cluster-users` by name. ([#1359](https://github.com/neuromation/platform-api-clients/issues/1359))

- Steal config files on `neuro job --pass-config`. ([#1361](https://github.com/neuromation/platform-api-clients/issues/1361))

- Support hidden files on the storage. Hide names started with a dot by default, provide ``neuro ls --all`` option to show all files. ([#1362](https://github.com/neuromation/platform-api-clients/issues/1362))

- Add HTTP tracing of neuro login commands. ([#1387](https://github.com/neuromation/platform-api-clients/issues/1387))

- Support job tags: `neuro run --tag=experiment-1`, `neuro ps --tag=experiment-1`. ([#1393](https://github.com/neuromation/platform-api-clients/issues/1393))

- Support job tags listing: `neuro job tags`. ([#1396](https://github.com/neuromation/platform-api-clients/issues/1396))

- Optionally display job's tags in `neuro ps` (the feature needs to be explicitly enabled in `.neuro.toml` config file). ([#1406](https://github.com/neuromation/platform-api-clients/issues/1406))


Bugfixes
--------


- Fix the alias finding routine when user is not logged in. ([#1360](https://github.com/neuromation/platform-api-clients/issues/1360))

- `neuro kill` exits now non-zero code if it failed to kill any job in the list. ([#1272](https://github.com/neuromation/platform-api-clients/issues/1272))

- Support un-quoted commands for neuro-exec: `neuro exec bash -c "ls && pwd"` is now a valid syntax. ([#1321](https://github.com/neuromation/platform-api-clients/issues/1321))


Neuromation 20.2.24 (2020-02-24)
=================================

Features
--------


- Support custom columns format for ``neuro ps`` command. ([#1288](https://github.com/neuromation/platform-api-clients/issues/1288))

- Support custom aliases. ([#1320](https://github.com/neuromation/platform-api-clients/issues/1320))

- Removed support of `~` in URIs (like `storage://~/path/to`). Relative URIs can be used instead (like `storage:path/to`). Support of tilde in local file paths (like `~/path/to`) has been preserved. ([#1329](https://github.com/neuromation/platform-api-clients/issues/1329))


Neuromation 20.01.22 (2020-01-22)
=================================

Features
--------


- `--env-file` now allows blank lines and comments (lines starting with "#") in the file. ([#1208](https://github.com/neuromation/platform-api-clients/issues/1208))

- Send the usage statistics to Google Analytics ([#1286](https://github.com/neuromation/platform-api-clients/issues/1286))

- Use Sqlite for saving the ``~/.neuro/db`` configuration file. ([#1298](https://github.com/neuromation/platform-api-clients/issues/1298))


Bugfixes
--------


- Fix columns width and aligning for ``neurp ps --format=<>`` command. ([#1302](https://github.com/neuromation/platform-api-clients/issues/1302))

- Fix ps-format documentation issues. ([#1303](https://github.com/neuromation/platform-api-clients/issues/1303))

- Parameters specified in ps-format now always override default values. `width` takes priority over `min` and `max`, `max` takes priority over `min`. ([#1310](https://github.com/neuromation/platform-api-clients/issues/1310))


Neuromation 20.01.15 (2020-01-15)
=================================

Features
--------


- Add `neuro admin add-user-quota` and `neuro admin set-user-quota` commands to control user quotas ([#1142](https://github.com/neuromation/platform-api-clients/issues/1142))

- Added options `--exclude` and `--include` in `neuro storage cp`. ([#1182](https://github.com/neuromation/platform-api-clients/issues/1182))

- Adjust NAME column of `neuro ps` so that grep by name works. ([#1189](https://github.com/neuromation/platform-api-clients/issues/1189))

- Read ``neuro ps --format`` spec from config files if present. ([#1294](https://github.com/neuromation/platform-api-clients/issues/1294))

- Read ``neuro cp`` filters from user configuration file. ([#1295](https://github.com/neuromation/platform-api-clients/issues/1295))


Neuromation 19.12.19 (2019-12-19)
=================================

Features
--------


- Now `neuro images` do not require the installed Docker. ([#1071](https://github.com/neuromation/platform-api-clients/issues/1071))

- Implement `neuro config get-clusters` command. ([#1177](https://github.com/neuromation/platform-api-clients/issues/1177))

- Convert configuration file into configuration directory, now it is `~/.neuro` folder. ([#1183](https://github.com/neuromation/platform-api-clients/issues/1183))

- Implement `neuro config switch-cluster` for switching between available clusters. ([#1217](https://github.com/neuromation/platform-api-clients/issues/1217))

- Implement `neuro admin get-clusters` command. ([#1223](https://github.com/neuromation/platform-api-clients/issues/1223))

- Implement `neuro admin add-cluster` command. ([#1224](https://github.com/neuromation/platform-api-clients/issues/1224))

- Add ``neuro admin generate-cluster-config`` command. ([#1227](https://github.com/neuromation/platform-api-clients/issues/1227))

- `neuro project init` now supports argument to set default value for generated project directory ([#1230](https://github.com/neuromation/platform-api-clients/issues/1230))


Bugfixes
--------


- Correctly process both quoted command arguments (`neuro run python:latest "python3 -c 'import os'") as well as unquoted version (`neuro run python:latest python3 -c 'import os'`). ([#1229](https://github.com/neuromation/platform-api-clients/issues/1229))


Neuromation 19.11.20 (2019-11-20)
=================================

Features
--------


- Trace sent HTTP requests and received replies to stderr if `--trace` flag is passed. ([#467](https://github.com/neuromation/platform-api-clients/issues/467))

- Display `Cluster` field for job status and listing commands. ([#874](https://github.com/neuromation/platform-api-clients/issues/874))

- Display `Entrypoint` field for job status command. ([#924](https://github.com/neuromation/platform-api-clients/issues/924))

- Display volumes information for `neuro status` command. ([#1003](https://github.com/neuromation/platform-api-clients/issues/1003))

- Option `--volume=HOME` deprecated. ([#1009](https://github.com/neuromation/platform-api-clients/issues/1009))

- Provide client.presets property, update docs. ([#1078](https://github.com/neuromation/platform-api-clients/issues/1078))

- Retry storage operations in case of some errors. ([#1107](https://github.com/neuromation/platform-api-clients/issues/1107))

- `neuro kill` will continue work if multiple jobs specified but you haven't required permissions for some of them. ([#1122](https://github.com/neuromation/platform-api-clients/issues/1122))

- Introduce `neuro config show-quota`. ([#1141](https://github.com/neuromation/platform-api-clients/issues/1141))

- Use pager for long lists. ([#1152](https://github.com/neuromation/platform-api-clients/issues/1152))

- Add global option '--hide-token/--no-hide-token' to be used together with '--trace' for preventing the user's token from being printed to stderr for safety reasons. ([#1158](https://github.com/neuromation/platform-api-clients/issues/1158))

- Suppress security checks for config files if NEUROMATION_TRUSTED_CONFIG_PATH environment variable is on. ([#1173](https://github.com/neuromation/platform-api-clients/issues/1173))


Bugfixes
--------


- When running a job with `--detach` option `neuro` now returns an error status if job fails to start at all (e.g., when cluster scale up fails). If job starts successfully (regardless of its run result) `neuro run` with `--detach` returns 0 like before. ([#1059](https://github.com/neuromation/platform-api-clients/issues/1059))

- Provide default arguments for api.Resources constructor to keep broken backward compatibility. ([#1070](https://github.com/neuromation/platform-api-clients/issues/1070))

- Fix help message for `neuro project init`: in fact, the command does not accept an argument. ([#1080](https://github.com/neuromation/platform-api-clients/issues/1080))

- Process 502 Bad Gateway as a separate exception, don't miss it with 400 Bad Request. ([#1111](https://github.com/neuromation/platform-api-clients/issues/1111))

- Wait for `ThreadPoolExecutor` finish befor exit from the program. ([#1144](https://github.com/neuromation/platform-api-clients/issues/1144))


Neuromation 19.9.23 (2019-09-23)
================================

Features
--------


- Introduce `neuro project init` for scaffolding an empty project. ([#1043](https://github.com/neuromation/platform-api-clients/issues/1043))

- `neuro cp -r` now works with non-directories. ([#1053](https://github.com/neuromation/platform-api-clients/issues/1053))

- Disable logging of annoying SSL errors. ([#1065](https://github.com/neuromation/platform-api-clients/issues/1065))

- Make image commands work on Windows. ([#1067](https://github.com/neuromation/platform-api-clients/issues/1067))

- Fix bug with job-name resolution introduced in release 19.8.19: do not print annoying warning messages if more than one job with specified name was found. ([#1034](https://github.com/neuromation/platform-api-clients/issues/1034))

- Fix `neuro job save` timing out too early. ([#1062](https://github.com/neuromation/platform-api-clients/issues/1062))

Neuromation 19.9.10 (2019-09-10)
================================

Features
--------


- Improved displaying a progress of copying many files. ([#1034](https://github.com/neuromation/platform-api-clients/issues/1034))


Deprecations and Removals
-------------------------


- Deprecate `neuro storage load` command. ([#1028](https://github.com/neuromation/platform-api-clients/issues/1028))


Neuromation 19.9.2 (2019-09-02)
===============================

Features
--------


- Due to `certifi` update delays, show certifi package error not earlier than two weeks after the latest version was released. ([#944](https://github.com/neuromation/platform-api-clients/issues/944))

- Support streaming output for `neuro-save` command. ([#946](https://github.com/neuromation/platform-api-clients/issues/946))

- Implement mounting all available volumes: `neuro run --volume=ALL`. ([#974](https://github.com/neuromation/platform-api-clients/issues/974))

- Uploading/downloading of a directory containing many small files is now 4-10 times faster. ([#981](https://github.com/neuromation/platform-api-clients/issues/981))

- Support Cloud TPU: new cli options `--tpu-type`, `--tpu-sw-version` added. ([#982](https://github.com/neuromation/platform-api-clients/issues/982))

- Support job operations via job-URI (e.g., `neuro status job://owner-name/job-name`). ([#988](https://github.com/neuromation/platform-api-clients/issues/988))

- Support job filtering by owner: `neuro ps -o user-1 --owner=user-2`. ([#990](https://github.com/neuromation/platform-api-clients/issues/990))

- Added the `--update` option in `neuro storage cp`.  It makes the command copying the source file only when it is newer than the destination file or when the destination file is missing. ([#1007](https://github.com/neuromation/platform-api-clients/issues/1007))

- Added the `-d` (`--directory`) option in `neuro storage ls` which makes the command to list directories themselves, not their contents. ([#1012](https://github.com/neuromation/platform-api-clients/issues/1012))


Neuromation 19.8.23 (2019-08-23)
================================

Features
--------


- `FileStatus.permission` now is `Action`, was `str`. ([#963](https://github.com/neuromation/platform-api-clients/issues/963))


Bugfixes
--------


- Fix regression: restore port-forward functionality. ([#979](https://github.com/neuromation/platform-api-clients/issues/979))


Neuromation 19.8.19 (2019-08-19)
================================

Features
--------


- Change default interactivity option for `neuro exec`: by default, interactive `--tty` will be used. ([#942](https://github.com/neuromation/platform-api-clients/issues/942))

- Use `Optional[datetime]` in `JobStatusHistory` `.created_at`, `.started_at`, `.finished_at` instead of `str`. ([#955](https://github.com/neuromation/platform-api-clients/issues/955))

- `neuro storage cp` is now up to 2 times faster for a directory with many small files. ([#958](https://github.com/neuromation/platform-api-clients/issues/958))

- Refactor port forwarding api to use async context manager for controlling a time of port
  forwarding process. ([#959](https://github.com/neuromation/platform-api-clients/issues/959))


Bugfixes
--------


- Support remote images with registry `host:port`. ([#939](https://github.com/neuromation/platform-api-clients/issues/939))


Neuromation 19.8.1 (2019-08-01)
===============================

Features
--------


- The `-p/--non-preemptible` parameter for `neuro run` has been removed in favor in embedding it into presets coming from the server. ([#928](https://github.com/neuromation/platform-api-clients/issues/928))

- Show progress for `neuro cp` by default. ([#933](https://github.com/neuromation/platform-api-clients/issues/933))

- Use dataclasses in image progress API ([#935](https://github.com/neuromation/platform-api-clients/issues/935))


Neuromation 19.7.26 (2019-07-26)
================================

Features
--------


- Add option `ps --all`, deprecate `ps -s all`. ([#538](https://github.com/neuromation/platform-api-clients/issues/538))

- Forbid mixing arguments and CLI options in `run`, `submit` and `exec` commands. Options (parameters starting from dash or double dash, e.g. `-n` and `--name`) should prepend arguments (e.g. `image:ubuntu:latest`). All tailed options belong to executed container command, not to neuro CLI itself. ([#927](https://github.com/neuromation/platform-api-clients/issues/927))


Neuromation 19.7.17 (2019-07-17)
================================

Features
--------


- The behavior of `neuro storage mv` is now closer to the behavior of the `mv` command.  It moves now files inside the target directory if it exists and moves a file under the new name otherwise.  Added also options `--target-directory` (`-t`) and `--no-target-directory` (`-T`). ([#203](https://github.com/neuromation/platform-api-clients/issues/203))

- `neuro job submit` and `neuro job run` command now support `--pass-config` option. This option ensures your local neuromation config file is uploaded to your job allowing you to executre `neuro` commands from the container. ([#827](https://github.com/neuromation/platform-api-clients/issues/827))

- Add `neuro image tags` command to list all tags for a given image ([#852](https://github.com/neuromation/platform-api-clients/issues/852))

- Stabilize jobs API ([#879](https://github.com/neuromation/platform-api-clients/issues/879))

- `neuro storage cp`, `neuro storage mv` and `neuro storage rm` support now globbing for source arguments.  Globbing can be disabled by specifying new option `--no-glob`.  Added command `neuro storage glob` which lists resources matching patterns. ([#889](https://github.com/neuromation/platform-api-clients/issues/889))


Neuromation 19.7.4 (2019-07-04)
===============================

Features
--------


- Implemented `neuro job browse`. Added the `--browse` flag to `neuro job submit` and `neuro job run`. ([#571](https://github.com/neuromation/platform-api-clients/issues/571))

- Added the global `--quiet` option, opposite to `--verbose`. Both options are additive. The `--quite` options for `neuro job` and `neuro image` are deprecated now. ([#848](https://github.com/neuromation/platform-api-clients/issues/848))

- Drop `neuromation.api.NetworkPortForwarding` for the sake of `neuromation.api.HTTPPort` ([#861](https://github.com/neuromation/platform-api-clients/issues/861))

- The output of "storage" commands in verbose mode is now more similar to the output of corresponding POSIX command. In particular ``neuro -v storage cp -r`` outputs a line for every copied file or directory. ([#869](https://github.com/neuromation/platform-api-clients/issues/869))

- The behavior of the `neuro storage cp` is now closer to the behavior of the `cp` command.  It now copies files inside the target directory if it exists and copies a file under the new name otherwise.  Added also options `--target-directory` (`-t`) and `--no-target-directory` (`-T`). ([#870](https://github.com/neuromation/platform-api-clients/issues/870))


Bugfixes
--------


- Fix certifi upgrade suggestion text. ([#845](https://github.com/neuromation/platform-api-clients/issues/845))


Neuromation 19.6.12 (2019-06-12)
================================

Features
--------


- Make non-preemtible mode default. ([#829](https://github.com/neuromation/platform-api-clients/issues/829))


Neuromation 19.6.10 (2019-06-10)
================================

Bugfixes
--------


- Improve storage operations stability by supporting sticky sessions. ([#832](https://github.com/neuromation/platform-api-clients/issues/832))


Neuromation 19.6.5 (2019-06-05)
===============================

Bugfixes
--------


- Relax pyyaml version requirement to don't force users to upgrade it if pyyaml was installed by anaconda or another non-pip installer. ([#828](https://github.com/neuromation/platform-api-clients/issues/828))


Neuromation 19.6.4 (2019-06-04)
===============================

Bugfixes
--------


- Don't run version checks if config is not loaded by CLI command. ([#826](https://github.com/neuromation/platform-api-clients/issues/826))


Neuromation 19.6.3 (2019-06-03)
===============================

Features
--------


- Changes in `neuro store mkdir` behavior: fails if the directory already exists or parent directories do not exist. Add option `--parents` to make parent directories as needed and ignore existing directories. ([#131](https://github.com/neuromation/platform-api-clients/issues/131))

- Changes in `neuro store rm` behavior: removes only files by default, add option `--recursive` to remove directories. ([#354](https://github.com/neuromation/platform-api-clients/issues/354))

- Storage commands (`neuro storage ls`, `neuro storage cp`, `neuro storage mv`, `neuro storage rm`) accept now variable number of arguments. This allows to copy or remove several files by one command. ([#784](https://github.com/neuromation/platform-api-clients/issues/784))

- Implement `neuro config login-headless` command. ([#793](https://github.com/neuromation/platform-api-clients/issues/793))

- Changes in interpretation URIs with absolute path and without host name. `storage:///foo/bar` means now the same as `storage://foo/bar` instead of `storage://{currentuser}/foo/bar`, and `storage:///` can be used for access to the storage root directory. ([#808](https://github.com/neuromation/platform-api-clients/issues/808))

- `neuro storage cp` now supports copying to/from non-regular files like character devices and named pipes. In particular this allows to output the file to the stdout or get the input from the stdin (`/dev/stdout` and `/dev/stdin` on Linux, `CON` on Windows). ([#813](https://github.com/neuromation/platform-api-clients/issues/813))

- Relax certifi required version. Raise a warning if the package should be updated. ([#819](https://github.com/neuromation/platform-api-clients/issues/819))


Bugfixes
--------


- Allow to logout even if config file is broken. ([#792](https://github.com/neuromation/platform-api-clients/issues/792))


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

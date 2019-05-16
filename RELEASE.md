# Release Process

* Make sure that the code is in a good shape, all tests are passed etc.
* Switch to `master` branch (`git checkout master`).
* Open `neuromation/__init__.py`, increment the `__version__` string, e.g. `__version__ = '1.2.3'`.
* Run `make format`.
* Run `towncrier` to update `CHANGELOG.md`.
* Open `CHANGELOG.md`, make sure that the generated file content looks good. Fix it if needed.
* Regenerate site docs. 
  * You need a clone of https://github.com/neuromation/platform-web project sibling to this repo.
  * Run `./build-tools/site-help-generator.py`. The tool regenerates files in `platform-web/docs`.
  * Verify and manually edit docs generated on the previous step.
  * Create a Pull Request for generated docs. Make sure that the docs PR passes CI checks.
  * Assign created PR to Artyom Astafurov (github: @astaff) and ping him to review (slack: @astaff, e-mail: astaff@neuromation.io)
* Commit changed `__init__.py`, `CHANGELOD.md` and deleted change pieces in `CHANGELOG.D`. Use `Release 1.2.3` commit message
* Push commited changes on github using the master branch.
* Wait for CircleCI checks finish, make sure that all tests are passed.
* Restart CI failed jobs in case of failed flaky tests.
* After CI is green make a git tag. For version `1.2.3` the tag should be `v1.2.3` (`git tag -a v1.2.3 -m "Release 1.2.3"`).
* Push a new tag, e.g. `git push origin v1.2.3`.
* Make sure that CI is green. Restart a job for tagged commit if a flaky test is encountered.
* Open PyPI (https://pypi.org/project/neuromation/), make sure that a new release is published and all needed files are awailable for downloading (https://pypi.org/project/neuromation/#files).
* Merge created pull request for `platform-web` project to publish updated documentation on the web.
* Increment version to next alpha, e.g. `__version__ = 1.3.0a0`. Commit this change to master and push on github.
* Publish a new version announcement on `platform-development` and `platform-feedback` slack channels.

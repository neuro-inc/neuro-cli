from unittest.mock import MagicMock

import pytest

from neuromation import JobItem
from neuromation.cli.formatter import OutputFormatter

TEST_JOB_STATUS = 'pending'
TEST_JOB_ID = 'job-ad09fe07-0c64-4d32-b477-3b737d215621'


@pytest.fixture
def job_item():
    return JobItem(status=TEST_JOB_STATUS,
                   id=TEST_JOB_ID,
                   client=MagicMock())


class TestOutputFormatter:

    def test_quiet(self, job_item):
        assert OutputFormatter.format_job(job_item, quiet=True) == TEST_JOB_ID

    def test_non_quiet(self, job_item):
        expected = f'Job ID: {TEST_JOB_ID} Status: {TEST_JOB_STATUS}\n' + \
               f'Shortcuts:\n' + \
               f'  neuro job status {TEST_JOB_ID}  # check job status\n' + \
               f'  neuro job monitor {TEST_JOB_ID} # monitor job stdout\n' + \
               f'  neuro job kill {TEST_JOB_ID}    # kill job'
        assert OutputFormatter.format_job(job_item, quiet=False) == expected

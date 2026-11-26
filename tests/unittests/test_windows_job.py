"""Exercise Windows job failure paths without requiring a Windows host."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from cosmic_ray import windows_job


@pytest.fixture
def kernel(monkeypatch):
    kernel = Mock()
    kernel.CreateJobObjectW.return_value = 123
    kernel.SetInformationJobObject.return_value = 1
    kernel.AssignProcessToJobObject.return_value = 1
    monkeypatch.setattr(windows_job, "_kernel32", lambda: kernel)
    monkeypatch.setattr(windows_job.ctypes, "get_last_error", lambda: 5, raising=False)
    monkeypatch.setattr(windows_job.ctypes, "WinError", lambda code: OSError(code, "API failed"), raising=False)
    return kernel


def test_initialization_failure_closes_job(kernel):
    kernel.SetInformationJobObject.return_value = 0
    with pytest.raises(OSError, match="API failed"):
        windows_job.Job()
    kernel.CloseHandle.assert_called_once_with(123)


def test_assignment_failure_does_not_resume_process(kernel, monkeypatch):
    load = Mock()
    monkeypatch.setattr(windows_job.ctypes, "WinDLL", load, raising=False)
    job = windows_job.Job()
    kernel.AssignProcessToJobObject.return_value = 0
    try:
        with pytest.raises(OSError, match="API failed"):
            job.adopt(SimpleNamespace(_handle=456))
        load.assert_not_called()
    finally:
        job.close()


@pytest.mark.parametrize("status", [0, -1073741790])
def test_resume_status_is_checked(kernel, monkeypatch, status):
    ntdll = Mock()
    ntdll.NtResumeProcess.return_value = status
    monkeypatch.setattr(windows_job.ctypes, "WinDLL", Mock(return_value=ntdll), raising=False)
    job = windows_job.Job()
    try:
        if status < 0:
            with pytest.raises(OSError, match="NtResumeProcess failed with NTSTATUS"):
                job.adopt(SimpleNamespace(_handle=456))
        else:
            job.adopt(SimpleNamespace(_handle=456))
        ntdll.NtResumeProcess.assert_called_once()
    finally:
        job.close()


def test_close_is_idempotent(kernel):
    job = windows_job.Job()
    job.close()
    job.close()
    kernel.CloseHandle.assert_called_once_with(123)

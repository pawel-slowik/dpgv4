# pylint: disable=missing-docstring
import pytest
from dpgv4 import run_external_command
from dpgv4 import ExternalCommandNotFoundError, ExternalCommandFailedError


def test_external_command_return() -> None:
    output = run_external_command(["ffmpeg", "-version"])
    assert isinstance(output, bytes)


def test_external_command_fail_not_found() -> None:
    with pytest.raises(ExternalCommandNotFoundError):
        run_external_command(["there is no such command"])


def test_external_command_fail_error() -> None:
    with pytest.raises(ExternalCommandFailedError):
        run_external_command(["false"])

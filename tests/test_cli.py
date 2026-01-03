import subprocess
import sys

from entropy_sim import __version__


def test_cli_version():
    cmd = [sys.executable, "-m", "entropy_sim", "--version"]
    assert subprocess.check_output(cmd).decode().strip() == __version__

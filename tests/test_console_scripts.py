import pytest


@pytest.mark.script_launch_mode("subprocess")
def test_deflex_compute(script_runner):
    ret = script_runner.run("deflex-compute", "--version")
    assert ret.success
    assert ret.stdout == "deflex 0.4.0rc1\n"

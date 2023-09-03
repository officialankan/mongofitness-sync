import logging
import pytest
import mdbfit


@pytest.fixture
def polar() -> mdbfit.Polar:
    return mdbfit.Polar()


def test_polar_steps(polar) -> None:
    steps = polar.get_steps()
    assert isinstance(steps, dict)

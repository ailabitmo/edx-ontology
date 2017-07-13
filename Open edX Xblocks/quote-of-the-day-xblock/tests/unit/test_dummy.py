from __future__ import absolute_import

import pytest


def test_addition():
    assert 1+1 == 2


def test_substraction():
    assert 1-1 == 0


@pytest.mark.parametrize(
    "operand1, operand2, result",
    [
        (1, 1, 2),
        (42, 18, 60),
        (7, 1, 8)
    ]
)
def test_parameterized_addition(operand1, operand2, result):
    assert operand1 + operand2 == result

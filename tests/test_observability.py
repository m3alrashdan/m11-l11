"""YOUR tests for the observability layer.

Per the lab guide, write at least 3 substantive tests, each with at least
1 assertion. The autograder enforces only the structure (3+ test functions,
each with an `assert` and a non-stub body); the specific behaviors you
choose to verify are up to you.

You name the tests, you decide what to assert, you choose the test
strategy (TestClient + header inspection? caplog + log parsing?
/metrics scrape + counter delta?). The placeholders below show one
possible split (one test per middleware), but you are free to pick any
three behaviors that exercise meaningful properties of your
instrumentation -- e.g. test that the request-id flows across two
sequential requests with distinct ids, test that the metrics counter
reflects a 500 response status correctly, test that the structured log
line carries the X-Request-ID matching the response header.

The autograder does not import your test function names; rename them
freely.
"""

import pytest


def test_one():
    # TODO: write a meaningful test of your observability layer here.
    pytest.fail("Not implemented -- write your test here")


def test_two():
    # TODO: write a meaningful test of your observability layer here.
    pytest.fail("Not implemented -- write your test here")


def test_three():
    # TODO: write a meaningful test of your observability layer here.
    pytest.fail("Not implemented -- write your test here")

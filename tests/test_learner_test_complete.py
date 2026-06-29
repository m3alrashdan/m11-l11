"""Autograder: AST check on `tests/test_observability.py`.

Per Learner-Written Test Rule: at least 3 test functions, at least 1 assertion
per function, no bare `pass`, no leftover `pytest.fail("Not implemented")`
placeholders.
"""
import ast
import os

LEARNER_TEST_FILE = os.path.join(
    os.path.dirname(__file__), "test_observability.py"
)
MIN_TESTS = 3


def _function_has_assertion(node: ast.FunctionDef) -> bool:
    for sub in ast.walk(node):
        if isinstance(sub, ast.Assert):
            return True
    return False


def _function_is_bare_pass(node: ast.FunctionDef) -> bool:
    """True iff body is a single `pass` (ignoring docstring)."""
    body = node.body
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
        body = body[1:]
    return len(body) == 1 and isinstance(body[0], ast.Pass)


def _function_has_not_implemented_placeholder(node: ast.FunctionDef) -> bool:
    """True iff function body contains a `pytest.fail("Not implemented ...")` call."""
    for sub in ast.walk(node):
        if isinstance(sub, ast.Call):
            func = sub.func
            is_pytest_fail = (
                isinstance(func, ast.Attribute)
                and func.attr == "fail"
                and isinstance(func.value, ast.Name)
                and func.value.id == "pytest"
            )
            if is_pytest_fail and sub.args:
                first = sub.args[0]
                if isinstance(first, ast.Constant) and isinstance(first.value, str):
                    if "not implemented" in first.value.lower():
                        return True
    return False


def test_learner_test_complete():
    """`tests/test_observability.py` has >= 3 substantive test functions."""
    assert os.path.exists(LEARNER_TEST_FILE), (
        f"Missing learner test file: {LEARNER_TEST_FILE}"
    )
    with open(LEARNER_TEST_FILE) as fh:
        tree = ast.parse(fh.read(), filename=LEARNER_TEST_FILE)

    test_funcs = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
    ]
    assert len(test_funcs) >= MIN_TESTS, (
        f"tests/test_observability.py has {len(test_funcs)} test functions; "
        f"required at least {MIN_TESTS}."
    )

    problems = []
    for fn in test_funcs:
        if _function_is_bare_pass(fn):
            problems.append(f"{fn.name}: body is bare `pass` (pytest counts this as PASSING; write an actual test)")
            continue
        if _function_has_not_implemented_placeholder(fn):
            problems.append(f"{fn.name}: still contains `pytest.fail(\"Not implemented...\")` placeholder")
            continue
        if not _function_has_assertion(fn):
            problems.append(f"{fn.name}: has no `assert` statement")

    assert not problems, "Learner test issues:\n  - " + "\n  - ".join(problems)

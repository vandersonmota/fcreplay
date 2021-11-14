import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--runslow", action="store_true", default=False, help="run slow tests"
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: mark test as slow to run")


def pytest_collection_modifyitems(config, items):
    if './fcreplay/tests/test_functionality.py::TestFunctionality::test_site' in config.getoption("file_or_dir"):
        return

    if config.getoption("--runslow"):
        # --runslow given in cli: do not skip slow tests
        return

    # skip slow tests
    skip_slow = pytest.mark.skip(reason="need --runslow option to run")

    # Get all items
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)

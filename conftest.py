def pytest_collect_file(path, parent):
    """Look in all Python files for test cases."""
    from _pytest.python import Module

    if path.ext == ".py":
        return Module.from_parent(parent, fspath=path)

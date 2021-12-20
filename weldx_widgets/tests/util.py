"""Testing utils."""
import contextlib
import os


@contextlib.contextmanager
def temp_env(**kw):
    """Temporarily set env variables to given mapping."""
    old = os.environ.copy()
    os.environ.update(**kw)

    yield

    os.environ = old

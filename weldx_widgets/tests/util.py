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


@contextlib.contextmanager
def voila_language(lang):
    """Temporarily sets env.QUERY_LANG to given language."""
    with temp_env(QUERY_STRING=f"&LANG={lang}"):
        yield

"""Translation related utilities."""
import gettext
import os
from pathlib import Path

__all__ = [
    "gettext",
    "set_trans_from_env",
    "_i18n",
    "_",
]

_translations = dict()


def set_trans_from_env():
    """Set locale from env.QUERY_STRING (if available, defaults to english)."""
    from weldx_widgets.kisa.save import get_param_from_env

    lang = get_param_from_env("LANG", default="en")
    os.environ["LANG"] = lang
    get_trans(lang)


def get_trans(lang_="en") -> gettext.GNUTranslations:
    """Get translation object for given lang string."""
    trans = _translations.get(lang_)
    if not trans:
        # Set up message catalog access
        if lang_ not in ("en", "de"):
            raise ValueError(f"Unsupported language: {lang_}")

        base_dir = Path(__file__).parent / "locale"
        if not base_dir.exists() and base_dir.is_dir():
            raise RuntimeError("could not set locale dir (non-existent or not a dir).")

        trans = gettext.translation("base", localedir=str(base_dir), languages=[lang_])
        _translations[lang_] = trans

    assert trans
    return trans


def _i18n(message: str) -> str:
    """Translate given message. Uses os.environ['LANG'] as target language."""
    lang = os.environ.get("LANG", "en")[:2]
    if lang.startswith("C"):
        lang = "en"
    trans_ = get_trans(lang)
    if not trans_:
        return message

    return trans_.gettext(message)


_ = _i18n  # alias

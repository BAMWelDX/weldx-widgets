"""Translation related utilities."""
import gettext
import os
from pathlib import Path

_translations = dict()


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


# set default language
get_trans("en")


def _i18n(message: str) -> str:
    """Translate given message. Uses os.environ['LANG'] as target language."""
    lang = os.environ.get("LANG", "en")[:2]
    trans_ = _translations.get(lang)
    if not trans_:
        return message

    return trans_.gettext(message)


def test_set_trans():
    """Test."""
    get_trans("de")
    os.environ["LAMG"] = "de"
    assert _i18n("Oxygen") == "Sauerstoff"

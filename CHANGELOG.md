# Release Notes

## 0.3.0 (11.07.2025)

### Added
- Added codespell spellchecking to pre-commit hooks (excluding `demo.ipynb`).
- Added Çağtay Fabry as an author in `pyproject.toml`.

### Changed
- Updated `ipywidgets` dependency to require version `>=8.1`.
- Updated `matplotlib` dependency to require version `>=3.8`.
- Updated ruff pre-commit hook to use `ruff-check` and bumped ruff version to `v0.12.2`.
- Improved type hint for `last_plot` in `WidgetGrooveSelectionTCPMovement` to use `CoordinateSystemManagerVisualizerK3D | None`.
- Replaced usage of `pd.TimedeltaIndex` with `pd.to_timedelta` in `to_tree` for improved time data handling.
- Improved removal of lines in matplotlib axes by using `artist.remove()` instead of `ax.lines.clear()` in `_update_plot`.

### Fixed
- Corrected a typo in docstring: "tiemstamps" → "timestamps".
- Updated unsafe input detection test in `is_safe_nd_array` by adding a test case for `[1., 2.]`.

### Removed
- Removed the `display` and `_ipython_display_` methods in `widget_base.py` (previously used for frontend drawing).  
(show widgets with default notebook output or explicit `display()` call)

## 0.2.6 (23.04.2025)

### Changes

- update version generation #152

### Dependencies

- require `ipython>=8` and update deprecated import #151

## 0.2.5 (06.12.2024)

### Dependencies

- add numpy 2 compatibility #139

## 0.2.4 (16.10.2024)

- Unpin Python.

## 0.2.3 (07.07.2024)

### Changes

- add `CHANGELOG.md`

### Dependencies

- pin `matplotlib<3.9`
- pin `numpy<2`

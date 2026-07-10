"""Discovery of upstream ra* tool outputs is filename-shaped, so it is testable
without an LLM. These tests pin the naming convention: every handoff file is
``<date>_<project>_<kind>_<initials_chain>.<ext>``.
"""
from __future__ import annotations

import pytest

from raconteur.context import find_methods_file


def _touch(d, name):
    p = d / name
    p.write_text("# methods\n")
    return p


# ── the project segment ───────────────────────────────────────────────────────

def test_finds_methods_file_with_project_segment(tmp_path):
    # raster names its handoff after the project, as the convention requires.
    # A regex anchored on <date>_methods skips the file the glob just found.
    _touch(tmp_path, "260707_schellingchords_methods_ra.md")
    found = find_methods_file(tmp_path)
    assert found is not None
    assert found.name == "260707_schellingchords_methods_ra.md"


def test_finds_methods_file_without_project_segment(tmp_path):
    _touch(tmp_path, "260707_methods_ra.md")
    assert find_methods_file(tmp_path).name == "260707_methods_ra.md"


@pytest.mark.parametrize("name", [
    "260707_proj_methods.md",        # no initials chain
    "26077_proj_methods_ra.md",      # datestamp is not 6 digits
    "260707_proj_methods_ra.txt",    # raster writes markdown
    "methods_ra.md",                 # no datestamp
])
def test_ignores_files_outside_the_convention(tmp_path, name):
    _touch(tmp_path, name)
    assert find_methods_file(tmp_path) is None


def test_none_when_raster_has_not_run(tmp_path):
    assert find_methods_file(tmp_path) is None


# ── which file wins ───────────────────────────────────────────────────────────

def test_highest_datestamp_wins_over_mtime(tmp_path):
    # A new datestamp starts a new revision cycle, so it supersedes an older
    # cycle even if the older file was touched more recently.
    new = _touch(tmp_path, "260707_proj_methods_ra.md")
    old = _touch(tmp_path, "260601_proj_methods_ra_DCR.md")
    import os
    os.utime(old, (2_000_000_000, 2_000_000_000))
    os.utime(new, (1_000_000_000, 1_000_000_000))
    assert find_methods_file(tmp_path).name == new.name


def test_mtime_breaks_ties_within_a_cycle(tmp_path):
    # Same cycle, chain grew: the newest state of the writeup wins regardless
    # of who last touched it.
    first = _touch(tmp_path, "260707_proj_methods_ra.md")
    later = _touch(tmp_path, "260707_proj_methods_ra_DCR.md")
    import os
    os.utime(first, (1_000_000_000, 1_000_000_000))
    os.utime(later, (2_000_000_000, 2_000_000_000))
    assert find_methods_file(tmp_path).name == later.name

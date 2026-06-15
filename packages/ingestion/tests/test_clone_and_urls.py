"""Pure-logic tests around URL parsing and the revisit/staleness contract.

The network-touching parts of clone.py (``clone_to_tempdir``,
``remote_head_sha``) are exercised by the ``slow`` httpx test.
"""

from __future__ import annotations

import pytest

from repopilot_ingestion.clone import parse_github_url


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://github.com/encode/httpx", ("encode", "httpx")),
        ("https://github.com/encode/httpx.git", ("encode", "httpx")),
        ("https://github.com/encode/httpx/", ("encode", "httpx")),
        ("http://github.com/pallets/flask", ("pallets", "flask")),
    ],
)
def test_parse_github_url_accepts_canonical_forms(
    url: str, expected: tuple[str, str]
) -> None:
    assert parse_github_url(url) == expected


@pytest.mark.parametrize(
    "url",
    [
        "https://gitlab.com/foo/bar",
        "git@github.com:foo/bar.git",
        "not a url",
        "https://github.com/foo",
    ],
)
def test_parse_github_url_rejects_unsupported(url: str) -> None:
    with pytest.raises(ValueError):
        parse_github_url(url)

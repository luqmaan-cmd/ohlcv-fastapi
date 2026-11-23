import asyncio
import os

import pytest
from fastapi import HTTPException

os.environ.setdefault("API_KEY", "primary-key")
os.environ.setdefault("API_KEYS", "uat-key:uat")

import main


def test_parse_single_bare_key():
    assert main._parse_api_keys("abc") == (("unnamed", "abc"),)


def test_parse_key_with_label():
    assert main._parse_api_keys("abc:uat") == (("uat", "abc"),)


def test_parse_multiple_keys_preserves_order():
    assert main._parse_api_keys("a:primary, b:uat") == (("primary", "a"), ("uat", "b"))


def test_parse_ignores_empty_segments_and_whitespace():
    assert main._parse_api_keys("  , a:one ,, b:two , ") == (("one", "a"), ("two", "b"))


def test_parse_empty_returns_no_keys():
    assert main._parse_api_keys("") == ()
    assert main._parse_api_keys(None) == ()


def test_parse_key_containing_colon_splits_on_last():
    assert main._parse_api_keys("ab:cd:uat") == (("uat", "ab:cd"),)


def test_parse_rejects_duplicate_labels():
    with pytest.raises(ValueError):
        main._parse_api_keys("abc:uat,def:uat")


def test_build_key_set_includes_primary_first():
    keys = main._build_key_set("primary-key", "uat-key:uat")
    assert keys[0] == ("primary", "primary-key")
    assert ("uat", "uat-key") in keys


def test_build_key_set_empty_extras_leaves_only_primary():
    assert main._build_key_set("primary-key", "") == (("primary", "primary-key"),)


def test_build_key_set_without_primary():
    assert main._build_key_set(None, "uat-key:uat") == (("uat", "uat-key"),)


def test_match_returns_label():
    keys = main._build_key_set("primary-key", "uat-key:uat")
    assert main._match_api_key("primary-key", keys) == "primary"
    assert main._match_api_key("uat-key", keys) == "uat"


def test_match_rejects_unknown_and_missing():
    keys = main._build_key_set("primary-key", "uat-key:uat")
    assert main._match_api_key("nope", keys) is None
    assert main._match_api_key("", keys) is None
    assert main._match_api_key(None, keys) is None


def test_match_prefix_is_not_sufficient():
    keys = main._build_key_set("primary-key", "uat-key:uat")
    assert main._match_api_key("primary", keys) is None
    assert main._match_api_key("primary-key-extra", keys) is None


def test_verify_accepts_either_transport():
    assert asyncio.run(main.verify_api_key(api_key="primary-key", header_key=None)) == "primary"
    assert asyncio.run(main.verify_api_key(api_key=None, header_key="uat-key")) == "uat"


def test_verify_header_wins_when_both_supplied():
    assert asyncio.run(main.verify_api_key(api_key="bogus", header_key="uat-key")) == "uat"
    assert asyncio.run(main.verify_api_key(api_key="primary-key", header_key="bogus")) == "primary"


def test_verify_rejects_bad_and_missing():
    for kwargs in (
        {"api_key": "bogus", "header_key": None},
        {"api_key": None, "header_key": "bogus"},
        {"api_key": None, "header_key": None},
    ):
        with pytest.raises(HTTPException) as exc:
            asyncio.run(main.verify_api_key(**kwargs))
        assert exc.value.status_code == 401
        assert exc.value.detail == "Invalid or missing API key"

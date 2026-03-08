"""Tests for utility functions used by the Celery tasks.

These are pure functions that can be tested without
Django database or Celery broker.
"""

import pytest
from datetime import date
from api.tasks import parse_date


class TestParseDate:
    """Verify multi-format date parsing used during extraction."""

    def test_iso_format(self):
        """Parses YYYY-MM-DD (standard ISO)."""
        assert parse_date("2026-01-15") == date(2026, 1, 15)

    def test_us_format(self):
        """Parses MM/DD/YYYY (US receipts)."""
        assert parse_date("01/15/2026") == date(2026, 1, 15)

    def test_european_format(self):
        """Parses DD/MM/YYYY (European receipts)."""
        assert parse_date("15/01/2026") == date(2026, 1, 15)

    def test_slash_iso_format(self):
        """Parses YYYY/MM/DD."""
        assert parse_date("2026/01/15") == date(2026, 1, 15)

    def test_returns_none_for_garbage(self):
        """Unrecognised strings return None, never raise."""
        assert parse_date("not-a-date") is None

    def test_returns_none_for_empty_string(self):
        """Empty string returns None."""
        assert parse_date("") is None

    def test_returns_none_for_none(self):
        """None input returns None."""
        assert parse_date(None) is None

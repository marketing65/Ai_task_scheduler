"""
Unit tests for the date_handler service.
Tests date validation, format normalization, and Hindi relative date resolution.
"""

from datetime import datetime, timedelta
from app.services.date_handler import validate_date_format, resolve_hindi_relative_date


class TestValidateDateFormat:
    """Tests for validate_date_format()."""

    def test_valid_yyyy_mm_dd(self):
        assert validate_date_format("2026-04-25") == "2026-04-25"

    def test_valid_yyyy_mm_dd_different_date(self):
        assert validate_date_format("2026-12-31") == "2026-12-31"

    def test_dd_mm_yyyy_slash(self):
        assert validate_date_format("25/04/2026") == "2026-04-25"

    def test_dd_mm_yyyy_dash(self):
        assert validate_date_format("25-04-2026") == "2026-04-25"

    def test_dd_month_yyyy(self):
        assert validate_date_format("25 April 2026") == "2026-04-25"

    def test_dd_month_short_yyyy(self):
        assert validate_date_format("25 Apr 2026") == "2026-04-25"

    def test_month_dd_yyyy(self):
        assert validate_date_format("April 25, 2026") == "2026-04-25"

    def test_dd_month_no_year(self):
        """When no year is given, should default to current year."""
        current_year = datetime.now().year
        result = validate_date_format("25 April")
        assert result == f"{current_year}-04-25"

    def test_none_input(self):
        assert validate_date_format(None) is None

    def test_empty_string(self):
        assert validate_date_format("") is None

    def test_null_string(self):
        assert validate_date_format("null") is None

    def test_none_string(self):
        assert validate_date_format("none") is None

    def test_na_string(self):
        assert validate_date_format("n/a") is None

    def test_whitespace_only(self):
        assert validate_date_format("   ") is None

    def test_invalid_date_string(self):
        """Completely unparseable string should return None."""
        assert validate_date_format("not-a-date") is None


class TestResolveHindiRelativeDate:
    """Tests for resolve_hindi_relative_date()."""

    def test_aaj(self):
        """'aaj' should resolve to today."""
        expected = datetime.now().strftime("%Y-%m-%d")
        assert resolve_hindi_relative_date("aaj karna hai") == expected

    def test_kal(self):
        """'kal' should resolve to tomorrow."""
        expected = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        assert resolve_hindi_relative_date("kal tak bhejo") == expected

    def test_parso(self):
        """'parso' should resolve to day after tomorrow."""
        expected = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
        assert resolve_hindi_relative_date("parso tak complete karo") == expected

    def test_agle_hafte(self):
        """'agle hafte' should resolve to 7 days from now."""
        expected = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        assert resolve_hindi_relative_date("agle hafte bhej do") == expected

    def test_no_relative_date(self):
        """No Hindi date phrase should return None."""
        assert resolve_hindi_relative_date("documents submit karo") is None

    def test_kal_tak(self):
        """'kal tak' should resolve to tomorrow."""
        expected = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        assert resolve_hindi_relative_date("kal tak report ready karo") == expected

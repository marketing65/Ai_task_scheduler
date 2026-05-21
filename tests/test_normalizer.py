"""
Unit tests for the normalizer service.
Tests name normalization (honorific stripping) and department normalization.
"""

from app.services.normalizer import normalize_name, normalize_department


class TestNormalizeName:
    """Tests for normalize_name()."""

    def test_strip_sir(self):
        assert normalize_name("Mukesh sir") == "Mukesh"

    def test_strip_mam(self):
        assert normalize_name("Simran mam") == "Simran"

    def test_strip_ji(self):
        assert normalize_name("Gupta ji") == "Gupta"

    def test_strip_bhai(self):
        assert normalize_name("Rahul bhai") == "Rahul"

    def test_strip_madam(self):
        assert normalize_name("Priya madam") == "Priya"

    def test_strip_dr(self):
        assert normalize_name("Dr. Sharma") == "Sharma"

    def test_strip_multiple_honorifics(self):
        assert normalize_name("Dr. Sharma ji") == "Sharma"

    def test_preserves_titlecase(self):
        assert normalize_name("rahul") == "Rahul"

    def test_none_input(self):
        assert normalize_name(None) is None

    def test_empty_string(self):
        assert normalize_name("") is None

    def test_whitespace_only(self):
        assert normalize_name("   ") is None

    def test_name_with_extra_spaces(self):
        assert normalize_name("  Mukesh   sir  ") == "Mukesh"

    def test_sahab(self):
        assert normalize_name("Kumar sahab") == "Kumar"

    def test_mr(self):
        assert normalize_name("Mr. Verma") == "Verma"

    def test_mrs(self):
        assert normalize_name("Mrs. Singh") == "Singh"


class TestNormalizeDepartment:
    """Tests for normalize_department()."""

    def test_hr_mein(self):
        assert normalize_department("HR mein") == "HR"

    def test_hr_plain(self):
        assert normalize_department("HR") == "HR"

    def test_production_side(self):
        assert normalize_department("production side") == "Production"

    def test_accounts_wale(self):
        assert normalize_department("accounts wale") == "Accounts"

    def test_it_department(self):
        assert normalize_department("IT department") == "IT"

    def test_finance(self):
        assert normalize_department("Finance") == "Finance"

    def test_sales_team(self):
        assert normalize_department("sales team") == "Sales"

    def test_marketing(self):
        assert normalize_department("marketing department") == "Marketing"

    def test_human_resources(self):
        assert normalize_department("human resources") == "HR"

    def test_operations(self):
        assert normalize_department("operations") == "Operations"

    def test_ops(self):
        assert normalize_department("ops") == "Operations"

    def test_quality_assurance(self):
        assert normalize_department("quality assurance") == "Quality"

    def test_none_input(self):
        assert normalize_department(None) is None

    def test_empty_string(self):
        assert normalize_department("") is None

    def test_unknown_department(self):
        """Unknown departments should be title-cased."""
        result = normalize_department("compliance")
        assert result == "Compliance"

    def test_supply_chain(self):
        assert normalize_department("supply chain") == "Logistics"

    def test_purchase(self):
        assert normalize_department("purchase") == "Procurement"

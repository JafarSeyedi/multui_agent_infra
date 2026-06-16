# engines/masking/tests/test_masking_models.py
from engines.masking.models.masking_models import MaskingRule, AnonymizationResult
from engines.masking.models.parsers.masking_rule_parser import parse_masking_rule
from engines.masking.models.writers.masking_rule_writer import write_masking_rule


def test_masking_rule():
    rule = MaskingRule(field_path="user.ssn", replacement="XXX-XX-XXXX")
    assert rule.field_path == "user.ssn"


def test_masking_rule_roundtrip():
    rule = MaskingRule(field_path="password", replacement="***", enabled=True)
    data = write_masking_rule(rule)
    parsed = parse_masking_rule(data)
    assert parsed.field_path == "password"
    assert parsed.replacement == "***"


def test_anonymization_result():
    r = AnonymizationResult(original="hello", anonymized="***")
    assert r.original == "hello"

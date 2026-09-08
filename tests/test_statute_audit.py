"""The statute audit table must match what the rules actually enforce.

For every audit entry, drive the rule across its claimed statutory threshold
and pin the verdict flip: a code constant drifting from the statute fails.
"""

import pytest

from contractguard.checklist import run_checklist
from contractguard.models import StatuteStatus
from contractguard.references import RULE_REFERENCES, STATUTE_AUDIT


def test_audit_table_covers_every_reference():
    assert set(STATUTE_AUDIT) == set(RULE_REFERENCES)
    for audit in STATUTE_AUDIT.values():
        assert audit.rule_id and audit.excerpt and audit.checked_points


def _check(text: str, rule_id: str, *, contract_type: str, lang: str, jurisdiction: str):
    for check in run_checklist(text, contract_type=contract_type, lang=lang, jurisdiction=jurisdiction):
        if check.rule_id == rule_id:
            return check
    raise AssertionError(f"{rule_id} not emitted for: {text[:60]}")


# Each pair is (text, expected status at/below the statutory line, then above it).
CA_CAP_BELOW = (
    "Governing law: California. The premises are in Los Angeles, CA. "
    "Monthly rent is $2,000. Tenant shall pay a security deposit of $2,000."
)
CA_CAP_ABOVE = (
    "Governing law: California. The premises are in Los Angeles, CA. "
    "Monthly rent is $2,000. Tenant shall pay a security deposit of $2,001."
)
CA_DEADLINE_OK = (
    "Governing law: California. Monthly rent is $2,000. "
    "Tenant shall pay a security deposit of $1,000. "
    "The deposit is refundable within 21 days of move-out."
)
CA_DEADLINE_OVER = (
    "Governing law: California. Monthly rent is $2,000. "
    "Tenant shall pay a security deposit of $1,000. "
    "The deposit is refundable within 22 days of move-out."
)

CN_PROBATION_OK = "本合同受中华人民共和国法律管辖。劳动合同期限三年，试用期六个月。"
CN_PROBATION_OVER = "本合同受中华人民共和国法律管辖。劳动合同期限三年，试用期七个月。"
CN_WAGE_OK = "本合同受中华人民共和国法律管辖。劳动合同期限三年，试用期六个月。试用期工资为约定工资的 80%。"
CN_WAGE_UNDER = "本合同受中华人民共和国法律管辖。劳动合同期限三年，试用期六个月。试用期工资为约定工资的 79%。"
CN_NONCOMPETE_OK = "本合同受中华人民共和国法律管辖。劳动合同期限三年。竞业限制期限 24 个月，按月给予经济补偿。"
CN_NONCOMPETE_OVER = "本合同受中华人民共和国法律管辖。劳动合同期限三年。竞业限制期限 25 个月，按月给予经济补偿。"
CN_LEASE_OK = "本合同受中华人民共和国法律管辖。租赁期限二十年，租金每月五千元。"
CN_LEASE_OVER = "本合同受中华人民共和国法律管辖。租赁期限二十一年，租金每月五千元。"
CN_EARNEST_OK = "本合同受中华人民共和国法律管辖。租赁合同总金额 100000 元，定金 20000 元。"
CN_EARNEST_OVER = "本合同受中华人民共和国法律管辖。租赁合同总金额 100000 元，定金 21000 元。"


@pytest.mark.parametrize(
    "rule_id,ok_text,over_text,ctype,lang,jur",
    [
        ("us_ca_security_deposit_cap", CA_CAP_BELOW, CA_CAP_ABOVE, "lease", "en", "us-ca"),
        ("us_ca_deposit_return_deadline", CA_DEADLINE_OK, CA_DEADLINE_OVER, "lease", "en", "us-ca"),
        ("cn_probation_duration_cap", CN_PROBATION_OK, CN_PROBATION_OVER, "unknown", "zh", "cn"),
        ("cn_probation_wage_floor", CN_WAGE_OK, CN_WAGE_UNDER, "unknown", "zh", "cn"),
        ("cn_noncompete_term_and_compensation", CN_NONCOMPETE_OK, CN_NONCOMPETE_OVER, "unknown", "zh", "cn"),
        ("cn_lease_term_cap", CN_LEASE_OK, CN_LEASE_OVER, "unknown", "zh", "cn"),
        ("cn_earnest_money_cap", CN_EARNEST_OK, CN_EARNEST_OVER, "unknown", "zh", "cn"),
    ],
)
def test_verdict_flips_exactly_at_the_statutory_line(rule_id, ok_text, over_text, ctype, lang, jur):
    assert rule_id in STATUTE_AUDIT
    ok = _check(ok_text, rule_id, contract_type=ctype, lang=lang, jurisdiction=jur)
    over = _check(over_text, rule_id, contract_type=ctype, lang=lang, jurisdiction=jur)
    assert ok.status in (StatuteStatus.OK, StatuteStatus.UNKNOWN), (rule_id, ok.status, ok.detail)
    assert over.status == StatuteStatus.VIOLATION, (rule_id, over.status, over.detail)

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

# 试用期上限全档表（《劳动合同法》第十九条）：<3mo → 0、3mo-1yr → ≤1、1-3yr → ≤2
CN_PROB_T1_OK = "本合同受中华人民共和国法律管辖。劳动合同期限二个月。"
CN_PROB_T1_OVER = "本合同受中华人民共和国法律管辖。劳动合同期限二个月，试用期一个月。"
CN_PROB_T2_OK = "本合同受中华人民共和国法律管辖。劳动合同期限六个月，试用期一个月。"
CN_PROB_T2_OVER = "本合同受中华人民共和国法律管辖。劳动合同期限六个月，试用期二个月。"
CN_PROB_T3_OK = "本合同受中华人民共和国法律管辖。劳动合同期限二年，试用期二个月。"
CN_PROB_T3_OVER = "本合同受中华人民共和国法律管辖。劳动合同期限二年，试用期三个月。"

CA_REFUND_OK = (
    "Governing law: California. Monthly rent is $2,000. "
    "Tenant shall pay a security deposit of $1,000, refundable at move-out."
)
CA_REFUND_BAD = (
    "Governing law: California. Monthly rent is $2,000. "
    "Tenant shall pay a non-refundable security deposit of $1,000."
)
CA_ENTRY_OK = (
    "Governing law: California. Monthly rent is $1,800. "
    "Landlord may enter the premises with 24 hours advance written notice."
)
CA_ENTRY_BAD = (
    "Governing law: California. Monthly rent is $1,800. "
    "Landlord may enter the premises without prior notice."
)
CN_SCOPE_OK = (
    "本合同受中华人民共和国法律管辖。劳动合同期限三年。"
    "公司提供专业培训，服务期两年。服务期内提前离职的，应支付违约金 20000 元。"
)
CN_SCOPE_BAD = (
    "本合同受中华人民共和国法律管辖。劳动合同期限三年。"
    "劳动者辞职的，应向用人单位支付违约金 50000 元。"
)
CN_TRAIN_OK = (
    "本合同受中华人民共和国法律管辖。劳动合同期限三年。"
    "公司为劳动者提供专项培训，培训费用 20000 元，服务期两年。"
    "服务期内提前离职的，应支付违约金 20000 元。"
)
CN_TRAIN_OVER = (
    "本合同受中华人民共和国法律管辖。劳动合同期限三年。"
    "公司为劳动者提供专项培训，培训费用 20000 元，服务期两年。"
    "服务期内提前离职的，应支付违约金 25000 元。"
)
CN_OT_WD_OK = "本合同受中华人民共和国法律管辖。劳动合同期限三年。工作日加班工资为正常工资的 150%。"
CN_OT_WD_UNDER = "本合同受中华人民共和国法律管辖。劳动合同期限三年。工作日加班工资为正常工资的 120%。"
CN_OT_RD_OK = "本合同受中华人民共和国法律管辖。劳动合同期限三年。休息日加班工资为正常工资的 200%。"
CN_OT_RD_UNDER = "本合同受中华人民共和国法律管辖。劳动合同期限三年。休息日加班工资为正常工资的 150%。"
CN_OT_HD_OK = "本合同受中华人民共和国法律管辖。劳动合同期限三年。法定节假日加班工资为正常工资的 300%。"
CN_OT_HD_UNDER = "本合同受中华人民共和国法律管辖。劳动合同期限三年。法定节假日加班工资为正常工资的 200%。"
CN_SI_OK = "本合同受中华人民共和国法律管辖。劳动合同期限三年，试用期六个月。"
CN_SI_BAD = (
    "本合同受中华人民共和国法律管辖。劳动合同期限三年。"
    "乙方自愿放弃社保，甲方以社保补贴形式代替缴纳。"
)
CN_LPR_OK = "本合同受中华人民共和国法律管辖。甲方向乙方借款 50000 元，年利率 10%。"
CN_LPR_OVER = "本合同受中华人民共和国法律管辖。甲方向乙方借款 50000 元，年利率 15%。"
CN_PRED_OK = (
    "本合同受中华人民共和国法律管辖。甲方向乙方借款 50000 元，年利率 10%，"
    "利息不预先在本金中扣除。"
)
CN_PRED_BAD = (
    "本合同受中华人民共和国法律管辖。甲方向乙方借款 50000 元，年利率 10%，"
    "利息预先在本金中扣除。"
)


FLIP_CASES = [
    ("us_ca_security_deposit_cap", CA_CAP_BELOW, CA_CAP_ABOVE, "lease", "en", "us-ca"),
    ("us_ca_deposit_return_deadline", CA_DEADLINE_OK, CA_DEADLINE_OVER, "lease", "en", "us-ca"),
    ("us_ca_deposit_refundability", CA_REFUND_OK, CA_REFUND_BAD, "lease", "en", "us-ca"),
    ("us_ca_entry_notice", CA_ENTRY_OK, CA_ENTRY_BAD, "lease", "en", "us-ca"),
    ("cn_probation_duration_cap", CN_PROBATION_OK, CN_PROBATION_OVER, "unknown", "zh", "cn"),
    ("cn_probation_duration_cap", CN_PROB_T1_OK, CN_PROB_T1_OVER, "unknown", "zh", "cn"),
    ("cn_probation_duration_cap", CN_PROB_T2_OK, CN_PROB_T2_OVER, "unknown", "zh", "cn"),
    ("cn_probation_duration_cap", CN_PROB_T3_OK, CN_PROB_T3_OVER, "unknown", "zh", "cn"),
    ("cn_probation_wage_floor", CN_WAGE_OK, CN_WAGE_UNDER, "unknown", "zh", "cn"),
    ("cn_noncompete_term_and_compensation", CN_NONCOMPETE_OK, CN_NONCOMPETE_OVER, "unknown", "zh", "cn"),
    ("cn_penalty_scope_limit", CN_SCOPE_OK, CN_SCOPE_BAD, "unknown", "zh", "cn"),
    ("cn_training_penalty_cap", CN_TRAIN_OK, CN_TRAIN_OVER, "unknown", "zh", "cn"),
    ("cn_overtime_pay_floor", CN_OT_WD_OK, CN_OT_WD_UNDER, "unknown", "zh", "cn"),
    ("cn_overtime_pay_floor", CN_OT_RD_OK, CN_OT_RD_UNDER, "unknown", "zh", "cn"),
    ("cn_overtime_pay_floor", CN_OT_HD_OK, CN_OT_HD_UNDER, "unknown", "zh", "cn"),
    ("cn_social_insurance_waiver", CN_SI_OK, CN_SI_BAD, "unknown", "zh", "cn"),
    ("cn_lease_term_cap", CN_LEASE_OK, CN_LEASE_OVER, "unknown", "zh", "cn"),
    ("cn_earnest_money_cap", CN_EARNEST_OK, CN_EARNEST_OVER, "unknown", "zh", "cn"),
    ("cn_loan_interest_cap", CN_LPR_OK, CN_LPR_OVER, "unknown", "zh", "cn"),
    ("cn_loan_no_prededucted_interest", CN_PRED_OK, CN_PRED_BAD, "unknown", "zh", "cn"),
]


@pytest.mark.parametrize("rule_id,ok_text,over_text,ctype,lang,jur", FLIP_CASES)
def test_verdict_flips_exactly_at_the_statutory_line(rule_id, ok_text, over_text, ctype, lang, jur):
    assert rule_id in STATUTE_AUDIT
    ok = _check(ok_text, rule_id, contract_type=ctype, lang=lang, jurisdiction=jur)
    over = _check(over_text, rule_id, contract_type=ctype, lang=lang, jurisdiction=jur)
    assert ok.status in (StatuteStatus.OK, StatuteStatus.UNKNOWN), (rule_id, ok.status, ok.detail)
    assert over.status == StatuteStatus.VIOLATION, (rule_id, over.status, over.detail)


def test_every_audited_rule_is_pinned_across_its_line():
    """审计表承诺的"逐条驱动过法定线"必须为真：每条 rule_id 至少一组翻转用例。"""
    pinned = {case[0] for case in FLIP_CASES}
    assert pinned == set(STATUTE_AUDIT), f"未钉住翻转的规则: {set(STATUTE_AUDIT) - pinned}"
